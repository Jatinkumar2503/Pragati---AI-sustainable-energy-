import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

WORKSPACES = {
    "indian_steel": {
        "id": "indian_steel",
        "name": "Indian Steel Industry Demo",
        "sector": "Steel",
        "provenance": "Public Indian Industrial Dataset (BEE PAT Cycle-VII & ASI Steel Cohort)",
        "is_demo": True,
        "metrics": {
            "active_load_kw": 4850.0,
            "annual_kwh": 38500000.0,
            "avg_power_factor": 0.88,
            "pragati_score": 742
        }
    },
    "indian_cement": {
        "id": "indian_cement",
        "name": "Indian Cement Industry Demo",
        "sector": "Cement",
        "provenance": "Public Indian Industrial Dataset (BEE PAT Cement SEC Benchmarks)",
        "is_demo": True,
        "metrics": {
            "active_load_kw": 8200.0,
            "annual_kwh": 65000000.0,
            "avg_power_factor": 0.92,
            "pragati_score": 815
        }
    },
    "indian_textile": {
        "id": "indian_textile",
        "name": "Indian Textile Industry Demo",
        "sector": "Textile",
        "provenance": "Public Indian Industrial Dataset (Ministry of Textiles Cluster Audits)",
        "is_demo": True,
        "metrics": {
            "active_load_kw": 1250.0,
            "annual_kwh": 9800000.0,
            "avg_power_factor": 0.86,
            "pragati_score": 690
        }
    },
    "customer_sandbox": {
        "id": "customer_sandbox",
        "name": "Customer Sandbox",
        "sector": "Custom Facility",
        "provenance": "Customer Uploaded Telemetry (Private Sandbox)",
        "is_demo": False,
        "metrics": {
            "active_load_kw": 0.0,
            "annual_kwh": 0.0,
            "avg_power_factor": 1.0,
            "pragati_score": 0
        }
    }
}

CURRENT_WORKSPACE_ID = "indian_steel"

def list_workspaces() -> List[Dict[str, Any]]:
    return list(WORKSPACES.values())

def get_current_workspace() -> Dict[str, Any]:
    return WORKSPACES[CURRENT_WORKSPACE_ID]

def switch_workspace(workspace_id: str) -> Dict[str, Any]:
    global CURRENT_WORKSPACE_ID
    if workspace_id not in WORKSPACES:
        raise ValueError(f"Invalid workspace ID: {workspace_id}")
    CURRENT_WORKSPACE_ID = workspace_id
    logger.info(f"[WorkspaceManager] Switched active workspace to: {workspace_id}")
    return WORKSPACES[CURRENT_WORKSPACE_ID]
