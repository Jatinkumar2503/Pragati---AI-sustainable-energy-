import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Standard Indian Industrial Compliance Guidelines, CERC Grid Codes, and Tariff Knowledge Store
BEE_PAT_KNOWLEDGE = [
    {
        "id": "pat_steel_sec",
        "title": "BEE PAT Cycle-VII Specific Energy Consumption (SEC) Norms for Iron & Steel",
        "rule": "Specific Energy Consumption (SEC) threshold for integrated steel plants is 0.585 TOE/ton of crude steel. Penalties apply at ₹10,000 per TOE excess.",
        "category": "Steel",
        "citation": "Bureau of Energy Efficiency (BEE) PAT Rules 2024, Gazette Notification S.O. 1294(E)"
    },
    {
        "id": "pat_cement_sec",
        "title": "BEE PAT Cycle-VII Thermal & Electrical Norms for Cement Plants",
        "rule": "Electrical energy consumption norm for Portland Pozzolana Cement (PPC) is 68.5 kWh/ton of cement produced. Thermal norm is 725 kcal/kg clinker.",
        "category": "Cement",
        "citation": "BEE PAT Cycle-VII Cement Sector Target Book 2024"
    },
    {
        "id": "pat_textile_sec",
        "title": "BEE Energy Conservation Building Code & Textile Cluster Norms",
        "rule": "Thermal energy norm for composite textile wet processing mills is 14.2 MJ/kg of fabric processed.",
        "category": "Textile",
        "citation": "Ministry of Power / BEE Textile Energy Audit Benchmark 2023"
    },
    {
        "id": "tod_tariff_maharashtra",
        "title": "MSEDCL Industrial Time-of-Day (ToD) Tariff Schedule",
        "rule": "Peak hours (09:00-12:00 & 18:00-22:00) incur +₹1.50/kWh surcharge. Off-peak hours (22:00-06:00) receive -₹1.00/kWh rebate. PF rebate up to 7% for PF > 0.95.",
        "category": "Tariff",
        "citation": "MERC Multi-Year Tariff Order for MSEDCL HT Industrial Consumers"
    },
    {
        "id": "tod_tariff_gujarat",
        "title": "UGVCL High Tension Industrial Tariff Schedule",
        "rule": "Night shift rebate of ₹0.85/kWh applies between 22:00 and 06:00. Power factor penalty applies below 0.90 lagging with 2% surcharge per 0.01 drop.",
        "category": "Tariff",
        "citation": "GERC Tariff Order for Torrent Power & UGVCL HT Consumers"
    },
    {
        "id": "cerc_grid_code_2023",
        "title": "CERC Indian Electricity Grid Code (IEGC) 2023 Frequency Operating Band",
        "rule": "National grid frequency shall be maintained strictly within 49.90 Hz to 50.05 Hz band. Industrial drawal deviations outside this band incur commercial Deviation Settlement Mechanism (DSM) charges.",
        "category": "Grid Code",
        "citation": "Central Electricity Regulatory Commission (IEGC) Regulations 2023"
    },
    {
        "id": "open_access_solar_rules",
        "title": "Green Energy Open Access Rules 2022 (Electricity Act 2003 Section 42)",
        "rule": "Designated consumers with connected load >= 100 kW are eligible for Open Access green power. Cross-subsidy surcharge (CSS) capped at 20% of average cost of supply.",
        "category": "Solar & Open Access",
        "citation": "Ministry of Power Green Energy Open Access Rules 2022, Notification G.S.R. 418(E)"
    },
    {
        "id": "sebi_brsr_principle_6",
        "title": "SEBI BRSR Core Principle 6 — Energy and GHG Intensity Disclosures",
        "rule": "Listed industrial entities must disclose Scope 1 (Direct), Scope 2 (Market & Location based electricity), and Energy Intensity per rupee of revenue under BRSR Principle 6.",
        "category": "ESG & BRSR",
        "citation": "Securities and Exchange Board of India (SEBI) Circular SEBI/HO/CFD/CFD-SEC-2/P/CIR/2023/122"
    },
    {
        "id": "iso_50001_enpi_standard",
        "title": "ISO 50001:2018 Energy Management Systems — Energy Performance Indicators",
        "rule": "Organizations must establish Energy Baselines (EnB) and Energy Performance Indicators (EnPI) normalized for production variables, heating/cooling degree days, and plant utilization.",
        "category": "ISO Standards",
        "citation": "International Organization for Standardization ISO 50001:2018 Clause 6.5 & 6.6"
    }
]

class RAGEngine:
    """
    RAG (Retrieval-Augmented Generation) Knowledge Engine for Bureau of Energy Efficiency (BEE)
    rules, PAT target guidelines, CERC grid codes, SEBI BRSR ESG disclosures, and state electricity board ToD tariff schedules.
    """
    def __init__(self):
        self.knowledge_base = BEE_PAT_KNOWLEDGE

    def search_rules(self, query: str, category: Optional[str] = None, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Performs semantic/keyword match against standard regulatory knowledge documents.
        """
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        results = []
        
        for item in self.knowledge_base:
            score = 0
            if category and item["category"].lower() == category.lower():
                score += 8
            
            title_terms = set(item["title"].lower().split())
            rule_terms = set(item["rule"].lower().split())
            
            # Term overlap score
            matched_title = query_terms.intersection(title_terms)
            matched_rule = query_terms.intersection(rule_terms)
            
            score += len(matched_title) * 4
            score += len(matched_rule) * 2
            
            if any(term in item["title"].lower() or term in item["rule"].lower() for term in query_terms):
                score += 3
                
            if score > 0:
                results.append((score, item))
                
        # Sort by relevance score descending
        results.sort(key=lambda x: x[0], reverse=True)
        matched = [r[1] for r in results[:top_k]]
        
        if not matched:
            matched = [self.knowledge_base[0]] # Fallback to default BEE rule
            
        logger.info(f"[RAGEngine] Searched query='{query}' (category={category}) -> Returned {len(matched)} matching rules.")
        return matched

rag_engine = RAGEngine()
