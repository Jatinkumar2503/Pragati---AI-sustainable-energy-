"""
PRAGATI AI — Phase 5 Workstream 4: Repeatable Industrial Demo Test Suite
Automated regression tests covering the 7-step five-minute repeatable demo workflow,
deterministic fixtures, provenance tracking, constraint audits, and failure paths.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api import app, DB_INSTANCE
from engine.demo_runner import DEMO_BENCHMARK_FIXTURE_V1, IndustrialDemoRunner

client = TestClient(app)


class TestDemoReadinessAndReset:
    """Step 1: Clean environment readiness check and non-destructive reset."""

    def test_health_readiness(self):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "healthy"
        assert "dataset_rows" in data

    def test_non_destructive_demo_reset(self):
        # Record row count before reset
        with DB_INSTANCE.get_connection() as conn:
            before_count = conn.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]

        res = client.post("/api/v1/demo/reset")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "success"
        assert data.get("fixture_id") == "STEEL_BENCHMARK_FIXTURE_V1"

        # Verify persistent database is unmodified
        with DB_INSTANCE.get_connection() as conn:
            after_count = conn.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]
        assert after_count == before_count, "Demo reset must not delete or modify persistent telemetry data."


class TestBenchmarkScenarioFixture:
    """Step 2: Versioned benchmark scenario loading and provenance inspection."""

    def test_get_demo_scenario(self):
        res = client.get("/api/v1/demo/scenario")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "success"
        scenario = data.get("scenario", {})

        # Verify fixture provenance
        assert scenario["fixture_id"] == "STEEL_BENCHMARK_FIXTURE_V1"
        assert scenario["provenance"] == "SYNTHETIC_BENCHMARK_FIXTURE_V1"
        assert scenario["is_synthetic"] is True
        assert "Synthetic engineering benchmark fixture" in scenario["disclaimer"]

        # Verify multi-stage task structure (EAF -> LRF -> CCM)
        tasks = scenario["multi_stage_tasks"]
        assert len(tasks) == 3
        eaf = next(t for t in tasks if t["machine"] == "EAF")
        lrf = next(t for t in tasks if t["machine"] == "LRF")
        ccm = next(t for t in tasks if t["machine"] == "CCM")

        assert eaf["prerequisites"] == []
        assert "TASK-EAF-01" in lrf["prerequisites"]
        assert "TASK-LRF-01" in ccm["prerequisites"]
        assert lrf["min_lag_h"] == 1
        assert lrf["max_lag_h"] == 3


class TestAnomalyAndDeduplicationLifecycle:
    """Step 3: Anomaly ingestion, alert deduplication, and lifecycle transitions."""

    def test_anomaly_and_deduplication_lifecycle(self):
        res = client.post("/api/v1/demo/step/anomaly")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "success"

        # Verify deduplication
        assert data.get("deduplication_verified") is True
        assert data.get("duplicate_suppressed_window_sec") == 3600
        assert data["duplicate_event"]["deduplicated"] is True

        # Verify acknowledgment and resolution
        assert data["acknowledgment"]["status"] == "success"
        assert data["acknowledgment"]["alert"]["status"] == "ACKNOWLEDGED"

        assert data["resolution"]["status"] == "success"
        assert data["resolution"]["alert"]["status"] == "RESOLVED"
        assert "Capacitor bank" in data["resolution"]["alert"]["resolution_notes"]


class TestForecastProvenanceAndLimitations:
    """Step 4: Load forecasting model benchmarks, holdout evaluation, and limitations."""

    def test_forecast_provenance(self):
        res = client.get("/api/v1/demo/step/forecast")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "success"

        prov = data.get("evaluation_provenance", {})
        assert prov.get("is_synthetic_fixture") is True
        assert "Chronological Holdout" in prov.get("strategy")
        assert prov.get("sample_count") == 2880

        # Check models
        models = data.get("models", [])
        assert len(models) >= 4
        ensemble = next(m for m in models if "Ensemble" in m["name"])
        assert ensemble["wape"] < 0.12
        assert ensemble["safe_mape_pct"] < 12.0
        assert ensemble["status"] == "RECOMMENDED"

        # Check explicit limitations
        limits = data.get("limitations", [])
        assert len(limits) >= 2
        assert any("breakdown" in l.lower() for l in limits)
        assert any("mape" in l.lower() for l in limits)


class TestMultiStageSchedulingAndConstraintAudit:
    """Step 5: Multi-stage MILP scheduling with EAF -> LRF -> CCM precedence & lag audit."""

    def test_schedule_optimization_and_audit(self):
        res = client.post("/api/v1/demo/step/schedule")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "success"
        assert data.get("feasible") is True

        # Precedence & buffer lag audit checks
        assert data.get("precedence_verified") == "SATISFIED"
        assert data.get("buffer_lag_verified") in ("SATISFIED", "BINDING")

        # Verify schedule chronological ordering
        sched = data.get("multi_task_schedule", [])
        assert len(sched) == 3
        eaf = next(s for s in sched if s["task_id"] == "TASK-EAF-01")
        lrf = next(s for s in sched if s["task_id"] == "TASK-LRF-01")
        ccm = next(s for s in sched if s["task_id"] == "TASK-CCM-01")

        # LRF start must be >= EAF finish + min_lag (1h)
        assert lrf["start_hour"] >= eaf["end_hour"] + 1
        # CCM start must be >= LRF finish + min_lag (1h)
        assert ccm["start_hour"] >= lrf["end_hour"] + 1

        # Savings verification
        savings = data.get("savings", {})
        assert savings.get("cost_dollars", 0) > 0


class TestDigitalTwin15YearLifecycle:
    """Step 6: 15-year lifecycle Digital Twin simulation with tax depreciation & sensitivity."""

    def test_digital_twin_simulation(self):
        res = client.post("/api/v1/demo/step/simulation")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "success"

        assert data.get("horizon_years") == 15
        assert data.get("initial_capex_usd") > 0
        assert data.get("net_present_value_usd") > 0
        assert data.get("internal_rate_of_return_pct") is not None
        assert data.get("internal_rate_of_return_pct") > 0
        assert data.get("tax_regime_used") == "SECTION_32_RENEWABLE_40_WDV"
        assert data.get("tax_depreciation_shield_usd") > 0

        # Degradation feedback
        assert data.get("battery_replacement_year") is not None
        assert data.get("battery_end_of_life_soh_pct") > 65.0

        # Sensitivity analysis factors
        tornado = data.get("tornado_sensitivity", [])
        assert len(tornado) >= 3
        # First factor has greatest impact swing
        assert tornado[0]["npv_swing_usd"] >= tornado[1]["npv_swing_usd"]


class TestManagerialApprovalAndAudit:
    """Step 7: Managerial decision approval and audit history recording."""

    def test_managerial_approval_and_audit(self):
        res = client.post("/api/v1/demo/step/approve")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "success"

        action_id = data.get("action_id")
        assert action_id.startswith("ACT-2026-")

        approval = data.get("approval_event", {})
        assert approval.get("status") == "success"
        decision = approval.get("decision", {})
        assert decision.get("status") == "APPROVED"
        assert "Priya Nair" in decision.get("approved_by")

        # Verify audit history
        audit = data.get("audit_history", [])
        assert len(audit) >= 1
        approved_entry = next((e for e in audit if e.get("action_id") == action_id), None)
        assert approved_entry is not None
        assert approved_entry.get("status") == "APPROVED"


class TestFullDemoSequenceRunner:
    """Validates complete automated 7-step sequence runner and performance manifest."""

    def test_run_full_demo_sequence(self):
        res = client.post("/api/v1/demo/run_sequence")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "COMPLETE_AND_VERIFIED"
        assert data.get("demo_manifest") == "PRAGATI_AI_5_MINUTE_INDUSTRIAL_DEMO_V1"
        assert data.get("execution_duration_seconds") < 30.0

        steps = data.get("steps_executed", [])
        assert len(steps) == 7
        for s in steps:
            assert s["status"] == "VERIFIED"


class TestDemoFailurePathsAndInfeasibility:
    """Validates robust handling of invalid inputs, infeasible schedules, and missing entities."""

    def test_acknowledge_nonexistent_alert_returns_404(self):
        res = client.post("/api/v1/alerts/acknowledge", json={
            "alert_id": "ALT-NONEXISTENT-9999",
            "operator_name": "Test Operator"
        })
        assert res.status_code == 404

    def test_resolve_nonexistent_alert_returns_404(self):
        res = client.post("/api/v1/alerts/resolve", json={
            "alert_id": "ALT-NONEXISTENT-9999",
            "operator_name": "Test Operator",
            "resolution_notes": "Attempting to resolve non-existent"
        })
        assert res.status_code == 404

    def test_infeasible_schedule_cyclic_dependency_caught(self):
        """Cyclic task dependency A -> B -> A must be reported cleanly as infeasible."""
        cyclic_tasks = [
            {"task_id": "T1", "machine": "EAF", "task_duration_h": 2, "task_load_kw": 100.0, "dependencies": ["T2"]},
            {"task_id": "T2", "machine": "LRF", "task_duration_h": 2, "task_load_kw": 100.0, "dependencies": ["T1"]}
        ]
        res = client.post("/api/schedule", json={
            "tenant_id": "demo_steel",
            "task_load_kw": 100.0,
            "task_duration_h": 4,
            "solar_capacity_kw": 150.0,
            "tasks": cyclic_tasks
        })
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "INFEASIBLE"
        assert "Cycle" in str(data.get("dependency_graph_status", {}))
