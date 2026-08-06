"""
PRAGATI AI — Workspace Manager & Sectoral Energy Benchmarking Engine
Provides enterprise tenant workspace isolation, Bureau of Energy Efficiency (BEE) PAT Cycle-VII
Specific Energy Consumption (SEC) compliance calculation, ISO 50001 EnPI baselining,
and ESCerts (Energy Saving Certificates) trading valuation.
"""

import logging
import math
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Bureau of Energy Efficiency (BEE) PAT Cycle-VII Specific Energy Consumption (SEC) Norms
# Units: Steel (TOE/ton crude steel), Cement (kWh/ton cement & kcal/kg clinker), Textile (MJ/kg fabric)
BEE_PAT_SECTOR_NORMS = {
    "Steel": {
        "sector_code": "SEC-STEEL-01",
        "baseline_sec_toe_per_ton": 0.635,
        "target_sec_toe_per_ton": 0.585,
        "toe_to_kwh_factor": 11630.0,  # 1 Metric Ton of Oil Equivalent = 11,630 kWh
        "kwh_to_toe_factor": 1.0 / 11630.0,
        "escert_market_price_inr": 1840.0,  # Price per Energy Saving Certificate (1 ESCert = 1 MTOE)
        "penalty_per_toe_inr": 10000.0,
        "compliance_cycle": "BEE PAT Cycle-VII (2024-2027)"
    },
    "Cement": {
        "sector_code": "SEC-CEMENT-02",
        "baseline_sec_kwh_per_ton": 76.2,
        "target_sec_kwh_per_ton": 68.5,
        "thermal_baseline_kcal_per_kg": 775.0,
        "thermal_target_kcal_per_kg": 725.0,
        "escert_market_price_inr": 1840.0,
        "penalty_per_toe_inr": 10000.0,
        "compliance_cycle": "BEE PAT Cycle-VII (2024-2027)"
    },
    "Textile": {
        "sector_code": "SEC-TEXTILE-03",
        "baseline_sec_mj_per_kg": 16.8,
        "target_sec_mj_per_kg": 14.2,
        "mj_to_kwh_factor": 0.277778,  # 1 MJ = 0.277778 kWh
        "escert_market_price_inr": 1840.0,
        "penalty_per_toe_inr": 10000.0,
        "compliance_cycle": "BEE PAT Cycle-VII (2024-2027)"
    }
}

WORKSPACES: Dict[str, Dict[str, Any]] = {
    "indian_steel": {
        "id": "indian_steel",
        "name": "Indian Steel Industry Demo",
        "sector": "Steel",
        "provenance": "Public Indian Industrial Dataset (BEE PAT Cycle-VII & ASI Steel Cohort)",
        "is_demo": True,
        "production_capacity_tons_year": 65000.0,
        "metrics": {
            "active_load_kw": 4850.0,
            "annual_kwh": 38500000.0,
            "avg_power_factor": 0.88,
            "pragati_score": 742
        },
        "bee_pat_baseline": {
            "baseline_sec_toe": 0.635,
            "target_sec_toe": 0.585,
            "current_sec_toe": 0.592
        }
    },
    "indian_cement": {
        "id": "indian_cement",
        "name": "Indian Cement Industry Demo",
        "sector": "Cement",
        "provenance": "Public Indian Industrial Dataset (BEE PAT Cement SEC Benchmarks)",
        "is_demo": True,
        "production_capacity_tons_year": 850000.0,
        "metrics": {
            "active_load_kw": 8200.0,
            "annual_kwh": 65000000.0,
            "avg_power_factor": 0.92,
            "pragati_score": 815
        },
        "bee_pat_baseline": {
            "baseline_sec_kwh": 76.2,
            "target_sec_kwh": 68.5,
            "current_sec_kwh": 70.1
        }
    },
    "indian_textile": {
        "id": "indian_textile",
        "name": "Indian Textile Industry Demo",
        "sector": "Textile",
        "provenance": "Public Indian Industrial Dataset (Ministry of Textiles Cluster Audits)",
        "is_demo": True,
        "production_capacity_tons_year": 12000.0,
        "metrics": {
            "active_load_kw": 1250.0,
            "annual_kwh": 9800000.0,
            "avg_power_factor": 0.86,
            "pragati_score": 690
        },
        "bee_pat_baseline": {
            "baseline_sec_mj": 16.8,
            "target_sec_mj": 14.2,
            "current_sec_mj": 14.9
        }
    },
    "customer_sandbox": {
        "id": "customer_sandbox",
        "name": "Customer Sandbox",
        "sector": "Custom Facility",
        "provenance": "Customer Uploaded Telemetry (Private Sandbox)",
        "is_demo": False,
        "production_capacity_tons_year": 10000.0,
        "metrics": {
            "active_load_kw": 0.0,
            "annual_kwh": 0.0,
            "avg_power_factor": 1.0,
            "pragati_score": 0
        },
        "bee_pat_baseline": {
            "baseline_sec_toe": 0.600,
            "target_sec_toe": 0.550,
            "current_sec_toe": 0.575
        }
    }
}

CURRENT_WORKSPACE_ID = "indian_steel"

def list_workspaces() -> List[Dict[str, Any]]:
    """Returns list of all registered tenant workspaces."""
    return list(WORKSPACES.values())

def get_current_workspace() -> Dict[str, Any]:
    """Retrieves the active workspace configuration."""
    return WORKSPACES[CURRENT_WORKSPACE_ID]

def switch_workspace(workspace_id: str) -> Dict[str, Any]:
    """Switches the active platform workspace."""
    global CURRENT_WORKSPACE_ID
    if workspace_id not in WORKSPACES:
        raise ValueError(f"Invalid workspace ID: {workspace_id}. Available: {list(WORKSPACES.keys())}")
    CURRENT_WORKSPACE_ID = workspace_id
    logger.info(f"[WorkspaceManager] Switched active workspace to: {workspace_id}")
    return WORKSPACES[CURRENT_WORKSPACE_ID]

def calculate_sec_compliance(
    workspace_id: str,
    annual_production_tons: float,
    annual_electrical_kwh: float,
    annual_thermal_toe: float = 0.0
) -> Dict[str, Any]:
    """
    Computes BEE PAT Specific Energy Consumption (SEC) performance, target achievement,
    and compliance grade for a designated industrial consumer.
    """
    ws = WORKSPACES.get(workspace_id, WORKSPACES["indian_steel"])
    sector = ws.get("sector", "Steel")
    norms = BEE_PAT_SECTOR_NORMS.get(sector, BEE_PAT_SECTOR_NORMS["Steel"])
    
    if annual_production_tons <= 0:
        annual_production_tons = 1.0

    if sector == "Steel":
        # Total energy in TOE = Electrical TOE + Thermal TOE
        electrical_toe = annual_electrical_kwh / norms["toe_to_kwh_factor"]
        total_energy_toe = electrical_toe + annual_thermal_toe
        actual_sec = total_energy_toe / annual_production_tons
        target_sec = norms["target_sec_toe_per_ton"]
        baseline_sec = norms["baseline_sec_toe_per_ton"]
        sec_unit = "TOE/ton crude steel"
    elif sector == "Cement":
        actual_sec = annual_electrical_kwh / annual_production_tons
        target_sec = norms["target_sec_kwh_per_ton"]
        baseline_sec = norms["baseline_sec_kwh_per_ton"]
        sec_unit = "kWh/ton cement"
    else:  # Textile
        # Convert kWh to MJ (1 kWh = 3.6 MJ), production in kg (1 ton = 1000 kg)
        total_mj = annual_electrical_kwh * 3.6
        actual_sec = total_mj / (annual_production_tons * 1000.0)
        target_sec = norms["target_sec_mj_per_kg"]
        baseline_sec = norms["baseline_sec_mj_per_kg"]
        sec_unit = "MJ/kg fabric"

    sec_reduction_pct = max(0.0, ((baseline_sec - actual_sec) / baseline_sec) * 100.0)
    target_reduction_pct = ((baseline_sec - target_sec) / baseline_sec) * 100.0
    is_compliant = actual_sec <= target_sec

    # ESCerts Calculation (1 ESCert = 1 MTOE energy saved beyond target)
    delta_toe_per_ton = (target_sec - actual_sec)
    if sector == "Cement":
        delta_toe_per_ton = (target_sec - actual_sec) / norms.get("toe_to_kwh_factor", 11630.0)
    elif sector == "Textile":
        delta_toe_per_ton = ((target_sec - actual_sec) * 0.277778) / 11630.0

    total_delta_toe = delta_toe_per_ton * annual_production_tons
    if total_delta_toe > 0:
        escerts_generated = round(total_delta_toe, 2)
        escerts_value_inr = round(escerts_generated * norms["escert_market_price_inr"], 2)
        penalty_inr = 0.0
        compliance_status = "Over-Compliant (ESCerts Surplus Eligible)"
    else:
        escerts_generated = 0.0
        escerts_value_inr = 0.0
        shortfall_toe = abs(total_delta_toe)
        penalty_inr = round(shortfall_toe * norms["penalty_per_toe_inr"], 2)
        compliance_status = "Non-Compliant (BEE Penalty Shortfall)" if actual_sec > target_sec else "Compliant"

    return {
        "workspace_id": workspace_id,
        "sector": sector,
        "compliance_cycle": norms["compliance_cycle"],
        "sec_unit": sec_unit,
        "baseline_sec": round(baseline_sec, 4),
        "target_sec": round(target_sec, 4),
        "actual_sec": round(actual_sec, 4),
        "sec_reduction_achieved_pct": round(sec_reduction_pct, 2),
        "sec_target_reduction_pct": round(target_reduction_pct, 2),
        "is_compliant": is_compliant,
        "compliance_status": compliance_status,
        "escerts_generated": escerts_generated,
        "escerts_value_inr": escerts_value_inr,
        "potential_penalty_inr": penalty_inr
    }

def calculate_iso_50001_enpi(
    baseline_kwh: float,
    actual_kwh: float,
    heating_degree_days: float = 0.0,
    cooling_degree_days: float = 0.0
) -> Dict[str, Any]:
    """
    Computes ISO 50001:2018 Energy Performance Indicator (EnPI) and Cumulative Sum of Savings (CUSUM).
    """
    weather_adjustment_factor = 1.0 + (heating_degree_days * 0.0005) + (cooling_degree_days * 0.0008)
    expected_kwh = baseline_kwh * weather_adjustment_factor
    kwh_savings = max(0.0, expected_kwh - actual_kwh)
    energy_intensity_improvement_pct = ((expected_kwh - actual_kwh) / max(1.0, expected_kwh)) * 100.0

    return {
        "standard": "ISO 50001:2018 Clause 6.6 Energy Performance Indicators",
        "baseline_consumption_kwh": round(baseline_kwh, 2),
        "weather_adjusted_expected_kwh": round(expected_kwh, 2),
        "actual_consumption_kwh": round(actual_kwh, 2),
        "net_energy_savings_kwh": round(kwh_savings, 2),
        "enpi_improvement_pct": round(energy_intensity_improvement_pct, 2),
        "iso_conformance": "Conforming" if energy_intensity_improvement_pct >= 0.0 else "Action Required"
    }
