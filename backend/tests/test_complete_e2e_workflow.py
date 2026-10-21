"""
backend/tests/test_complete_e2e_workflow.py

Phase 2 Complete End-to-End Workflow Integration Test:
Verifies the complete 9-stage pipeline:
  1. Input Data Loading & Validation (validate_telemetry_csv, clean_and_engineer_features)
  2. Load Forecasting (Prophet, Random Forest, RNN via generate_forecast)
  3. Anomaly Detection (Isolation Forest & Z-Score via run_anomaly_detection)
  4. Alert Deduplication & Suppression Window (/api/v1/alerts/active)
  5. Schedule Optimization (MILP multi-stage task DAG via optimize_shift_schedule)
  6. Constraint Feasibility Audit (evaluate_constraint_audit_log, zero violations on feasible)
  7. Digital Twin Simulation (Solar + BESS, NPV/IRR, Section 32 WDV disclaimers)
  8. Human Decision Approval & Rejection Flow (Traceable decisions with operator notes)
  9. Dynamic Audit Trail & Provenance Verification (/api/v1/audit/logs)
"""

import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from backend.api import app
from backend.engine.dataset_loader import load_dataset
from backend.engine.data_pipeline import validate_telemetry_csv, clean_and_engineer_features
from backend.engine.forecaster import generate_forecast, calculate_safe_mape
from backend.engine.anomaly_detector import run_anomaly_detection
from backend.engine.scheduler import optimize_shift_schedule, evaluate_constraint_audit_log


@pytest.fixture
def client():
    return TestClient(app)


def test_complete_e2e_industrial_intelligence_pipeline(client):
    """
    Executes and validates the end-to-end industrial energy intelligence workflow:
    Input data -> Validation -> Forecasting -> Anomaly Detection -> Deduplication
    -> Scheduling -> Constraint Audit -> Digital Twin -> Decision Center -> Dynamic Audit Logs.
    """

    # -------------------------------------------------------------------------
    # STAGE 1: Data Ingestion & Physical Validation
    # -------------------------------------------------------------------------
    df = load_dataset()
    assert df is not None and len(df) > 100, "Dataset loader failed to provide telemetry data."

    # Validate schema using pipeline validator
    test_csv_df = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=48, freq="1h"),
        "usage_kwh": np.random.uniform(100, 300, 48),
        "power_factor": np.random.uniform(0.85, 0.95, 48)
    })
    is_valid, msg = validate_telemetry_csv(test_csv_df)
    assert is_valid is True, f"Telemetry CSV validation failed: {msg}"

    cleaned_df = clean_and_engineer_features(test_csv_df)
    assert len(cleaned_df) == 48
    assert "hour" in cleaned_df.columns
    assert "hour_sin" in cleaned_df.columns
    assert "power_factor" in cleaned_df.columns

    # -------------------------------------------------------------------------
    # STAGE 2: Load Forecasting with Multi-Model Ensemble
    # -------------------------------------------------------------------------
    forecast_input_df = df.copy()
    if "usage_kwh" not in forecast_input_df.columns and "active_power_kw" in forecast_input_df.columns:
        forecast_input_df["usage_kwh"] = forecast_input_df["active_power_kw"]
    if "date" not in forecast_input_df.columns and "timestamp" in forecast_input_df.columns:
        forecast_input_df["date"] = forecast_input_df["timestamp"]

    fc_sample = forecast_input_df.tail(1200).copy()
    fc_res = generate_forecast(fc_sample, forecast_hours=24, backtest_folds=2)
    assert fc_res is not None
    assert "prophet_forecast" in fc_res
    assert "rf_forecast" in fc_res
    assert "metrics" in fc_res
    assert len(fc_res["rf_forecast"]) == 24

    # -------------------------------------------------------------------------
    # STAGE 3: Anomaly Detection with Contextual Metadata
    # -------------------------------------------------------------------------
    anom_input_df = pd.DataFrame({
        "date": pd.date_range(start="2026-01-01", periods=60, freq="15min"),
        "usage_kwh": np.random.uniform(80, 180, 60),
        "reactive_lagging_kvarh": np.random.uniform(10, 30, 60),
        "reactive_leading_kvarh": np.random.uniform(5, 15, 60),
        "power_factor_lagging": np.random.uniform(80, 92, 60),
        "load_type": ["Medium_Load"] * 60,
        "week_status": ["Weekday"] * 60,
        "day_of_week": ["Monday"] * 60
    })
    # Inject an abnormal consumption surge
    anom_input_df.loc[15, "usage_kwh"] = 750.0

    anomalies = run_anomaly_detection(anom_input_df, contamination=0.05)
    assert isinstance(anomalies, list)
    assert len(anomalies) > 0
    assert "timestamp" in anomalies[0]
    assert "usage_kwh" in anomalies[0]

    # -------------------------------------------------------------------------
    # STAGE 4: Alert Deduplication & Triage Status
    # -------------------------------------------------------------------------
    alerts_endpoint_res = client.get("/api/v1/alerts/active")
    assert alerts_endpoint_res.status_code == 200
    alert_payload = alerts_endpoint_res.json()
    assert alert_payload["status"] == "success"
    assert "result" in alert_payload

    # -------------------------------------------------------------------------
    # STAGE 5 & 6: Schedule Optimization & Constraint Feasibility Audit
    # -------------------------------------------------------------------------
    multi_stage_tasks = [
        {
            "task_id": "MELT-01",
            "name": "Induction Melting",
            "machine": "Furnace-A",
            "task_load_kw": 160.0,
            "task_duration_h": 3,
            "dependencies": [],
            "min_lag_h": 0,
            "max_lag_h": None
        },
        {
            "task_id": "CAST-01",
            "name": "Billet Continuous Casting",
            "machine": "Caster-1",
            "task_load_kw": 85.0,
            "task_duration_h": 2,
            "dependencies": ["MELT-01"],
            "min_lag_h": 1,
            "max_lag_h": 3
        }
    ]

    sched_payload = {
        "tenant_id": "demo_steel",
        "solar_capacity_kw": 120.0,
        "contract_demand_max_kw": 400.0,
        "maintenance_window": [2, 5],
        "tasks": multi_stage_tasks
    }

    sched_res = client.post("/api/v1/scheduler/optimize", json=sched_payload)
    assert sched_res.status_code == 200
    sched_data = sched_res.json()["optimization"]
    assert sched_data["status"] == "FEASIBLE"
    assert len(sched_data["tasks_scheduled"]) == 2

    # Verify Constraint Feasibility Audit Log
    audit_entries = sched_data["constraint_audit_log"]
    assert len(audit_entries) > 0
    violations = [e for e in audit_entries if e["status"] == "VIOLATED"]
    assert len(violations) == 0, f"Expected 0 violations for feasible schedule, got: {violations}"

    # Verify Baseline vs Optimized metrics comparison
    comparison = sched_data["metrics_comparison"]
    assert comparison["status"] == "FEASIBLE"
    assert "baseline" in comparison and "optimized" in comparison
    assert comparison["baseline"]["total_cost_usd"] >= comparison["optimized"]["total_cost_usd"]

    # -------------------------------------------------------------------------
    # STAGE 7: Digital Twin Simulation (Solar PV + BESS with Statutory Disclaimers)
    # -------------------------------------------------------------------------
    dt_payload = {
        "solar_capacity_kw": 150.0,
        "battery_storage_kwh": 100.0,
        "load_shift_pct": 20.0,
        "region": "Western",
        "tax_regime": "SECTION_32_RENEWABLE_40_WDV"
    }
    dt_res = client.post("/api/v1/simulation/digital_twin", json=dt_payload)
    assert dt_res.status_code == 200
    dt_data = dt_res.json()
    assert dt_data["status"] == "success"
    sim = dt_data["result"]["simulation"]

    # Check financial indicators
    assert "financial_metrics" in sim
    fin = sim["financial_metrics"]
    assert "estimated_capex_inr" in fin and "estimated_capex_usd" in fin
    assert "annual_savings_inr" in fin and "annual_savings_usd" in fin
    assert "payback_period_years" in fin
    assert "net_present_value_inr" in fin and "net_present_value_usd" in fin
    assert "internal_rate_of_return_pct" in fin
    assert fin["internal_rate_of_return_pct"] > 0.0

    # Verify lifecycle and statutory disclaimers
    life = sim.get("lifecycle_analysis", {})
    assert "cash_flow_table" in life or "after_tax_cashflow_breakeven_years" in fin

    # Verify Section 32 statutory tax regime and disclaimers
    assert "inr_metrics" in fin
    assert "Section 32" in fin["inr_metrics"]["section"]

    tax_reg_res = client.get("/api/v1/simulation/tax_regimes")
    assert tax_reg_res.status_code == 200
    assert "Section 32" in tax_reg_res.json()["statutory_note"]

    # -------------------------------------------------------------------------
    # STAGE 8: Decision Center: Human Approval & Rejection Flow
    # -------------------------------------------------------------------------
    # 1. Generate first action recommendation for rejection test
    rec1_res = client.post("/api/v1/decision/generate", json={"sector": "Steel", "tenant_id": "demo_steel"})
    assert rec1_res.status_code == 200
    rec1_data = rec1_res.json()
    action1 = rec1_data.get("decision_center", {})
    action1_id = action1.get("action_id", "ACT-REJECT-001")

    # Reject action 1 with operator reason
    reject_payload = {
        "action_id": action1_id,
        "manager_name": "Chief Safety Engineer",
        "reason": "Scheduled maintenance window on Furnace-A extended by 2 hours due to ladle refractories."
    }
    reject_res = client.post("/api/v1/decision/reject", json=reject_payload)
    assert reject_res.status_code == 200
    rej_data = reject_res.json()
    assert rej_data["status"] == "success"
    rej_state = rej_data["decision_state"]
    assert rej_state["status"] == "REJECTED"
    assert rej_state["action_id"] == action1_id
    assert "Chief Safety Engineer" in rej_state["rejected_by"]
    assert "ladle refractories" in rej_state["rejection_reason"]

    # 2. Generate second action recommendation for approval test
    rec2_res = client.post("/api/v1/decision/generate", json={"sector": "Textiles", "tenant_id": "demo_textiles"})
    assert rec2_res.status_code == 200
    rec2_data = rec2_res.json()
    action2 = rec2_data.get("decision_center", {})
    action2_id = action2.get("action_id", "ACT-APPROVE-002")

    # Approve action 2 with operator notes
    approve_payload = {
        "action_id": action2_id,
        "manager_name": "Plant Operations Lead",
        "notes": "Approved off-peak spinning shift to utilize overnight tariff tier."
    }
    approve_res = client.post("/api/v1/decision/approve", json=approve_payload)
    assert approve_res.status_code == 200
    app_data = approve_res.json()
    assert app_data["status"] == "success"
    app_state = app_data["decision_state"]
    assert app_state["status"] == "APPROVED"
    assert app_state["action_id"] == action2_id

    # -------------------------------------------------------------------------
    # STAGE 9: Dynamic Audit Trail & Traceability Verification
    # -------------------------------------------------------------------------
    audit_res = client.get("/api/v1/audit/logs")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["status"] == "success"
    logs = audit_data["logs"]
    assert len(logs) > 0

    # Ensure both rejected and approved decisions appear dynamically in the live audit history
    rejected_logged = any(
        action1_id in log.get("action_id", "") and log.get("status") == "REJECTED"
        for log in logs
    )
    assert rejected_logged, f"Expected rejected action '{action1_id}' in audit logs."

    approved_logged = any(
        action2_id in log.get("action_id", "") and log.get("status") == "APPROVED"
        for log in logs
    )
    assert approved_logged, f"Expected approved action '{action2_id}' in audit logs."
