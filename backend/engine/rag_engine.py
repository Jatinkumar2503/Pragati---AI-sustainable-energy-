import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Standard Indian Industrial Compliance Guidelines & Tariff Knowledge Store
BEE_PAT_KNOWLEDGE = [
    {
        "id": "pat_steel_sec",
        "title": "BEE PAT Cycle-VII Specific Energy Consumption (SEC) Norms for Iron & Steel",
        "rule": "Specific Energy Consumption (SEC) threshold for integrated steel plants is 0.585 TOE/ton of crude steel. Penalties apply at ₹10,000 per TOE excess.",
        "category": "Steel"
    },
    {
        "id": "pat_cement_sec",
        "title": "BEE PAT Cycle-VII Thermal & Electrical Norms for Cement Plants",
        "rule": "Electrical energy consumption norm for Portland Pozzolana Cement (PPC) is 68.5 kWh/ton of cement produced.",
        "category": "Cement"
    },
    {
        "id": "pat_textile_sec",
        "title": "BEE Energy Conservation Building Code & Textile Cluster Norms",
        "rule": "Thermal energy norm for composite textile wet processing mills is 14.2 MJ/kg of fabric processed.",
        "category": "Textile"
    },
    {
        "id": "tod_tariff_maharashtra",
        "title": "MSEDCL Industrial Time-of-Day (ToD) Tariff Schedule",
        "rule": "Peak hours (09:00-12:00 & 18:00-22:00) incur +₹1.50/kWh surcharge. Off-peak hours (22:00-06:00) receive -₹1.00/kWh rebate.",
        "category": "Tariff"
    },
    {
        "id": "tod_tariff_gujarat",
        "title": "UGVCL High Tension Industrial Tariff Schedule",
        "rule": "Night shift rebate of ₹0.85/kWh applies between 22:00 and 06:00. Power factor penalty applies below 0.90 lagging.",
        "category": "Tariff"
    }
]

class RAGEngine:
    """
    RAG (Retrieval-Augmented Generation) Knowledge Engine for Bureau of Energy Efficiency (BEE)
    rules, PAT target guidelines, and state electricity board ToD tariff schedules.
    """
    def __init__(self):
        self.knowledge_base = BEE_PAT_KNOWLEDGE

    def search_rules(self, query: str, category: str = None, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Performs semantic/keyword match against standard regulatory knowledge documents.
        """
        query_lower = query.lower()
        results = []
        
        for item in self.knowledge_base:
            score = 0
            if category and item["category"].lower() == category.lower():
                score += 5
            if any(term in item["title"].lower() or term in item["rule"].lower() for term in query_lower.split()):
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
