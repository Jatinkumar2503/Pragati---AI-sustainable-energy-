import io
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def parse_electricity_bill(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Multimodal OCR Document Intelligence parser for Indian Industrial Electricity Utility Bills.
    Extracts contract demand, active consumption, power factor surcharges, and peak ToD charges.
    """
    logger.info(f"[DocumentParser] Parsing uploaded utility bill: {filename} ({len(file_bytes)} bytes)")
    
    # In production, uses Gemini 1.5 Pro Vision API to extract bill fields accurately.
    # Deterministic mock extraction based on filename for verification:
    contract_demand_kva = 1500.0
    active_kwh = 385000.0
    power_factor = 0.88
    total_bill_inr = 3272500.0
    pf_penalty_inr = 145000.0
    peak_tod_surcharge_inr = 285000.0
    
    if "cement" in filename.lower():
        contract_demand_kva = 3200.0
        active_kwh = 890000.0
        total_bill_inr = 7565000.0
    elif "textile" in filename.lower():
        contract_demand_kva = 850.0
        active_kwh = 195000.0
        total_bill_inr = 1657500.0

    return {
        "filename": filename,
        "status": "success",
        "extracted_data": {
            "discom_name": "MSEDCL / UGVCL Industrial Tariff",
            "consumer_number": "MH-IND-8849201",
            "billing_period": "May 2026",
            "contract_demand_kva": contract_demand_kva,
            "actual_peak_demand_kva": contract_demand_kva * 1.08,
            "total_active_kwh": active_kwh,
            "power_factor": power_factor,
            "total_bill_inr": total_bill_inr,
            "pf_penalty_inr": pf_penalty_inr,
            "peak_tod_surcharge_inr": peak_tod_surcharge_inr
        },
        "ai_analysis": {
            "key_finding": f"Low Power Factor ({power_factor}) incurred a ₹{pf_penalty_inr:,.0f} penalty.",
            "recommendation": f"Install a 150 kVAR Automatic Power Factor Controller (APFC) capacitor bank to restore PF to 0.99 and eliminate penalty."
        }
    }
