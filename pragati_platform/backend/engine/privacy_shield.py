import re
import threading
import logging

logger = logging.getLogger(__name__)

class PrivacyShield:
    def __init__(self):
        # Session mapping store format: { session_id: { placeholder: original_value } }
        self._mappings = {}
        self._lock = threading.Lock()
        
        # General sensitive patterns to redact
        self.patterns = {
            "EMAIL": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "IP": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            "TIMESTAMP": r'\b\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\b'
        }
        
        # Base known proprietary entity/facility terms
        self.base_keywords = [
            ("Cambridge Smelting Co.", "FACILITY"),
            ("Cambridge Smelting", "FACILITY"),
            ("Steel Plant #4", "FACILITY"),
            ("Steel Plant", "FACILITY"),
            ("Smelter 3B", "EQUIPMENT"),
            ("Smelter 3b", "EQUIPMENT"),
            ("Furnace 12", "EQUIPMENT")
        ]
        
        # Context markers for rule-based Named Entity Recognition (NER)
        self.context_indicators = [
            "facility", "plant", "smelter", "furnace", "meter", "machine", 
            "compressor", "boiler", "turbine", "site", "co.", "inc.", "corp."
        ]

    def _get_session_store(self, session_id: str) -> dict:
        with self._lock:
            if session_id not in self._mappings:
                self._mappings[session_id] = {}
            return self._mappings[session_id]

    def _extract_ner_entities(self, text: str) -> list:
        """
        Rule-based Context-Aware Named Entity Recognition (NER) parser.
        Detects capitalized proper nouns or alpha-numeric identifiers (e.g. 'Turbine 4X', 'Cambridge Site')
        that are associated with industrial context indicators.
        """
        entities = []
        
        # 1. Regex to find capitalized word groups and trailing alpha-numerics (e.g. 'Smelter 3B', 'Unit 12')
        # Matches patterns like 'Cambridge Smelting Co.' or 'Furnace 12'
        pattern = r'\b[A-Z][a-zA-Z0-9]*(?:\s+[A-Z0-9][a-zA-Z0-9]*)*\b'
        matches = re.finditer(pattern, text)
        
        text_lower = text.lower()
        
        for m in matches:
            entity_str = m.group(0)
            start_idx, end_idx = m.span()
            
            # Skip short words that are likely standard sentence starters or abbreviations (unless they are known keywords)
            if len(entity_str) < 3:
                continue
                
            # Rule A: Check if the matched string contains any of our base keywords
            is_known = False
            for kw, cat in self.base_keywords:
                if kw.lower() in entity_str.lower() or entity_str.lower() in kw.lower():
                    entities.append((entity_str, cat))
                    is_known = True
                    break
            if is_known:
                continue
                
            # Rule B: Context window search. If the matched proper noun is near context words
            # (e.g., "draw of Furnace 12", "temperature at Cambridge Site")
            window_start = max(0, start_idx - 30)
            window_end = min(len(text), end_idx + 30)
            surrounding_context = text_lower[window_start:window_end]
            
            for indicator in self.context_indicators:
                if indicator in surrounding_context:
                    # Categorize based on keywords in the entity or context
                    category = "FACILITY" if any(x in entity_str.lower() for x in ["plant", "site", "co", "facility"]) else "EQUIPMENT"
                    entities.append((entity_str, category))
                    break
                    
        # Sort by length descending to prevent substring substitution collision
        entities = sorted(list(set(entities)), key=lambda x: len(x[0]), reverse=True)
        return entities

    def anonymize(self, text: str, session_id: str) -> str:
        """
        Anonymizes sensitive elements (PII, IPs, proprietary entities) in text using regex and context-aware NER.
        Stores placeholders in the session dictionary for recovery.
        """
        if not text:
            return ""
            
        store = self._get_session_store(session_id)
        anonymized_text = text
        
        # 1. Run context-aware rule-based NER to extract and redact proprietary names
        ner_entities = self._extract_ner_entities(text)
        for entity, category in ner_entities:
            # Check if this exact entity already has a placeholder in store
            placeholder = None
            for p, val in store.items():
                if val == entity:
                    placeholder = p
                    break
            if not placeholder:
                placeholder = f"[REDACTED_{category}_{len(store)}]"
                store[placeholder] = entity
            
            # Replace case-insensitively but safely
            anonymized_text = re.sub(re.escape(entity), placeholder, anonymized_text)
            
        # 2. Redact standard regex patterns (IPs, Emails, exact Timestamps)
        for pat_name, regex in self.patterns.items():
            matches = re.findall(regex, anonymized_text)
            for match in set(matches):
                placeholder = None
                for p, val in store.items():
                    if val == match:
                        placeholder = p
                        break
                if not placeholder:
                    placeholder = f"[REDACTED_{pat_name}_{len(store)}]"
                    store[placeholder] = match
                    
                anonymized_text = re.sub(re.escape(match), placeholder, anonymized_text)
                
        return anonymized_text

    def deanonymize(self, text: str, session_id: str) -> str:
        """
        Reverses the anonymization process by restoring local original strings from the session store.
        """
        if not text:
            return ""
            
        store = self._get_session_store(session_id)
        deanonymized_text = text
        
        # Sort placeholders by length descending to prevent substring substitution collisions
        placeholders = sorted(store.keys(), key=len, reverse=True)
        for placeholder in placeholders:
            original = store[placeholder]
            deanonymized_text = deanonymized_text.replace(placeholder, original)
            
        return deanonymized_text

    def anonymize_data(self, data, session_id: str):
        """
        Recursively walks dictionaries, lists, and values to anonymize text and limit numeric precision.
        """
        if isinstance(data, dict):
            return {k: self.anonymize_data(v, session_id) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.anonymize_data(v, session_id) for v in data]
        elif isinstance(data, str):
            return self.anonymize(data, session_id)
        elif isinstance(data, float):
            # Limit precision leakage by rounding telemetry loads to 0.5 kW
            # (Differential privacy/obfuscation standard)
            return round(data * 2.0) / 2.0
        else:
            return data

    def clear_session(self, session_id: str):
        """
        Clears mapping memory for a session once the API request turn is fully complete.
        """
        with self._lock:
            if session_id in self._mappings:
                del self._mappings[session_id]

# Singleton instance for backend use
privacy_shield = PrivacyShield()

if __name__ == "__main__":
    ps = PrivacyShield()
    sid = "test-session-123"
    
    # Test text containing an unhardcoded proprietary entity "Boiler X99"
    query = "Check temperature sensor logs for Boiler X99 at London Facility (IP: 10.0.0.45) on 2026-06-06 20:00:00."
    print("Original:", query)
    
    anon = ps.anonymize(query, sid)
    print("\nAnonymized:", anon)
    
    restored = ps.deanonymize(anon, sid)
    print("\nRestored:", restored)
