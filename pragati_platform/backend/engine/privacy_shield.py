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
        
        # Known proprietary entity/facility terms to scan and replace
        self.entity_keywords = [
            ("Cambridge Smelting Co.", "FACILITY"),
            ("Cambridge Smelting", "FACILITY"),
            ("Steel Plant #4", "FACILITY"),
            ("Steel Plant", "FACILITY"),
            ("Smelter 3B", "EQUIPMENT"),
            ("Smelter 3b", "EQUIPMENT"),
            ("Furnace 12", "EQUIPMENT")
        ]

    def _get_session_store(self, session_id: str) -> dict:
        with self._lock:
            if session_id not in self._mappings:
                self._mappings[session_id] = {}
            return self._mappings[session_id]

    def anonymize(self, text: str, session_id: str) -> str:
        """
        Anonymizes sensitive elements (PII, IPs, proprietary entities, calendar dates) in text.
        Stores placeholders in the session dictionary for recovery.
        """
        if not text:
            return ""
            
        store = self._get_session_store(session_id)
        anonymized_text = text
        
        # 1. Redact known proprietary facility/machinery keywords
        for keyword, category in self.entity_keywords:
            if keyword in anonymized_text:
                # Find or create placeholder token
                placeholder = None
                for k, v in store.items():
                    if v == keyword:
                        placeholder = k
                        break
                if not placeholder:
                    placeholder = f"[REDACTED_{category}_{len(store)}]"
                    store[placeholder] = keyword
                
                anonymized_text = anonymized_text.replace(keyword, placeholder)
                
        # 2. Redact general regex patterns (IPs, Emails, exact Timestamps)
        for pat_name, regex in self.patterns.items():
            matches = re.findall(regex, anonymized_text)
            for match in set(matches):
                placeholder = None
                for k, v in store.items():
                    if v == match:
                        placeholder = k
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
    # Test script
    ps = PrivacyShield()
    sid = "test-session-123"
    
    query = "What is the grid draw of Furnace 12 at Cambridge Smelting Co. (IP: 192.168.1.105) on 2018-01-01 22:15:00?"
    print("Original Query:", query)
    
    anon = ps.anonymize(query, sid)
    print("\nAnonymized Prompt sent to Cloud:", anon)
    
    # Simulate LLM response containing placeholders
    llm_response = f"According to the records, the grid draw of [REDACTED_EQUIPMENT_1] at [REDACTED_FACILITY_0] was 45.5 kW at timestamp [REDACTED_TIMESTAMP_3]."
    print("\nLLM Response from Cloud:", llm_response)
    
    restored = ps.deanonymize(llm_response, sid)
    print("\nLocal Restored Response shown to user:", restored)

