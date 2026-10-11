import pytest
import numpy as np
from fastapi.testclient import TestClient
from api import app
from engine.scheduler import (
    validate_task_graph,
    calculate_baseline_schedule,
    evaluate_constraint_audit_log,
    solve_milp_schedule,
    optimize_shift_schedule,
    get_tariff,
    get_carbon_intensity
)
from engine.decision_engine import DecisionEngine, DECISION_ENGINE_INSTANCE

client = TestClient(app)

class TestDependencyGraphValidation:
    """Test graph structure, DAG acyclicity, unknown prerequisites, and lag constraints."""

    def test_valid_three_stage_dag(self):
        tasks = [
            {"task_id": "EAF-01", "name": "Electric Arc Melting", "machine": "Furnace #1", "task_load_kw": 180.0, "task_duration_h": 3, "dependencies": [], "min_lag_h": 0, "max_lag_h": None},
            {"task_id": "LRF-01", "name": "Ladle Refining", "machine": "Refiner #2", "task_load_kw": 90.0, "task_duration_h": 2, "dependencies": ["EAF-01"], "min_lag_h": 1, "max_lag_h": 3},
            {"task_id": "CCM-01", "name": "Continuous Casting", "machine": "Caster #1", "task_load_kw": 60.0, "task_duration_h": 2, "dependencies": ["LRF-01"], "min_lag_h": 0, "max_lag_h": 2}
        ]
        is_valid, errors = validate_task_graph(tasks)
        assert is_valid is True
        assert len(errors) == 0

    def test_cycle_detection_direct(self):
        tasks = [
            {"task_id": "T1", "task_load_kw": 100.0, "task_duration_h": 2, "dependencies": ["T2"]},
            {"task_id": "T2", "task_load_kw": 80.0, "task_duration_h": 2, "dependencies": ["T1"]}
        ]
        is_valid, errors = validate_task_graph(tasks)
        assert is_valid is False
        assert any("Cycle detected" in err for err in errors)

    def test_cycle_detection_indirect(self):
        tasks = [
            {"task_id": "A", "task_load_kw": 100.0, "task_duration_h": 2, "dependencies": ["C"]},
            {"task_id": "B", "task_load_kw": 80.0, "task_duration_h": 2, "dependencies": ["A"]},
            {"task_id": "C", "task_load_kw": 50.0, "task_duration_h": 2, "dependencies": ["B"]}
        ]
        is_valid, errors = validate_task_graph(tasks)
        assert is_valid is False
        assert any("Cycle detected" in err for err in errors)

    def test_unknown_prerequisite_detection(self):
        tasks = [
            {"task_id": "LRF-01", "task_load_kw": 90.0, "task_duration_h": 2, "dependencies": ["GHOST_TASK"]}
        ]
        is_valid, errors = validate_task_graph(tasks)
        assert is_valid is False
        assert any("Unknown prerequisite" in err for err in errors)

    def test_duplicate_task_id_detection(self):
        tasks = [
            {"task_id": "EAF-01", "task_load_kw": 180.0, "task_duration_h": 3, "dependencies": []},
            {"task_id": "EAF-01", "task_load_kw": 120.0, "task_duration_h": 2, "dependencies": []}
        ]
        is_valid, errors = validate_task_graph(tasks)
        assert is_valid is False
        assert any("Duplicate task_id" in err for err in errors)

    def test_impossible_lag_window_min_greater_than_max(self):
        tasks = [
            {"task_id": "EAF-01", "task_load_kw": 180.0, "task_duration_h": 3, "dependencies": []},
            {"task_id": "LRF-01", "task_load_kw": 90.0, "task_duration_h": 2, "dependencies": ["EAF-01"], "min_lag_h": 4, "max_lag_h": 2}
        ]
        is_valid, errors = validate_task_graph(tasks)
        assert is_valid is False
        assert any("min_lag_h" in err and "max_lag_h" in err for err in errors)

    def test_invalid_task_parameters(self):
        tasks = [
            {"task_id": "BAD_DUR", "task_load_kw": 100.0, "task_duration_h": 0, "dependencies": []},
            {"task_id": "BAD_LOAD", "task_load_kw": -10.0, "task_duration_h": 2, "dependencies": []}
        ]
        is_valid, errors = validate_task_graph(tasks)
        assert is_valid is False
        assert len(errors) >= 2


class TestOperationalRealismScheduler:
    """Test MILP multi-stage scheduling, precedence constraints, and buffer lag enforcement."""

    def test_multi_stage_steel_process_scheduling(self):
        """EAF -> LRF -> CCM precedence order and buffer lags."""
        tasks = [
            {"task_id": "EAF-01", "name": "Electric Arc Melting", "machine": "Furnace #1", "task_load_kw": 180.0, "task_duration_h": 3, "dependencies": [], "min_lag_h": 0, "max_lag_h": None},
            {"task_id": "LRF-01", "name": "Ladle Refining", "machine": "Refiner #2", "task_load_kw": 90.0, "task_duration_h": 2, "dependencies": ["EAF-01"], "min_lag_h": 1, "max_lag_h": 3},
            {"task_id": "CCM-01", "name": "Continuous Casting", "machine": "Caster #1", "task_load_kw": 60.0, "task_duration_h": 2, "dependencies": ["LRF-01"], "min_lag_h": 0, "max_lag_h": 2}
        ]
        res = optimize_shift_schedule(tasks=tasks, solar_capacity_kw=150.0, maintenance_window=(2, 5))
        assert res["status"] == "FEASIBLE"
        assert res["is_feasible"] is True
        
        sched = {t["task_id"]: t for t in res["tasks_scheduled"]}
        assert "EAF-01" in sched and "LRF-01" in sched and "CCM-01" in sched
        
        eaf = sched["EAF-01"]
        lrf = sched["LRF-01"]
        ccm = sched["CCM-01"]
        
        # Verify precedence: LRF start >= EAF end + min_lag (1)
        lag_eaf_lrf = lrf["start_hour"] - eaf["end_hour"]
        assert lag_eaf_lrf >= 1, f"Expected LRF start >= EAF end + 1, got EAF end {eaf['end_hour']}, LRF start {lrf['start_hour']}"
        assert lag_eaf_lrf <= 3, f"Expected lag <= max_lag 3, got {lag_eaf_lrf}"
        
        # Verify precedence: CCM start >= LRF end + min_lag (0)
        lag_lrf_ccm = ccm["start_hour"] - lrf["end_hour"]
        assert lag_lrf_ccm >= 0, f"Expected CCM start >= LRF end, got LRF end {lrf['end_hour']}, CCM start {ccm['start_hour']}"
        assert lag_lrf_ccm <= 2, f"Expected lag <= max_lag 2, got {lag_lrf_ccm}"
        
        # Verify maintenance window avoidance (02:00-05:00)
        for t in [eaf, lrf, ccm]:
            task_hrs = set(range(t["start_hour"], t["end_hour"]))
            assert not task_hrs.intersection({2, 3, 4, 5}), f"Task {t['task_id']} overlapped maintenance window [2, 5]"

    def test_infeasible_schedule_handles_gracefully_without_false_savings(self):
        """When total work + lags exceed 24h, solver reports infeasible without claiming savings."""
        tasks = [
            {"task_id": "T1", "task_load_kw": 100.0, "task_duration_h": 14, "dependencies": []},
            {"task_id": "T2", "task_load_kw": 100.0, "task_duration_h": 12, "dependencies": ["T1"], "min_lag_h": 2}
        ]
        res = optimize_shift_schedule(tasks=tasks, solar_capacity_kw=150.0)
        assert res["status"] == "INFEASIBLE"
        assert res["is_feasible"] is False
        assert res["savings"]["cost_dollars"] == 0.0
        assert res["savings"]["cost_inr"] == 0.0
        assert res["savings"]["carbon_kg"] == 0.0
        assert res["metrics_comparison"]["status"] == "INFEASIBLE"

    def test_cyclic_task_graph_aborts_without_crash(self):
        """Cyclic task graph returns INFEASIBLE and records graph violation in audit log."""
        tasks = [
            {"task_id": "EAF", "task_load_kw": 100.0, "task_duration_h": 2, "dependencies": ["CCM"]},
            {"task_id": "CCM", "task_load_kw": 100.0, "task_duration_h": 2, "dependencies": ["EAF"]}
        ]
        res = optimize_shift_schedule(tasks=tasks)
        assert res["status"] == "INFEASIBLE"
        assert res["dependency_graph_status"]["valid"] is False
        assert any(e["status"] == "VIOLATED" for e in res["constraint_audit_log"])


class TestBaselineFairnessAndMetrics:
    """Test Priority 2: Baseline vs Optimized comparison consistency."""

    def test_baseline_fairness_identical_workload_and_assumptions(self):
        tasks = [
            {"task_id": "EAF-01", "task_load_kw": 150.0, "task_duration_h": 3, "dependencies": [], "min_lag_h": 0},
            {"task_id": "LRF-01", "task_load_kw": 80.0, "task_duration_h": 2, "dependencies": ["EAF-01"], "min_lag_h": 1}
        ]
        res = optimize_shift_schedule(tasks=tasks, solar_capacity_kw=150.0, contract_demand_max_kw=450.0)
        assert res["status"] == "FEASIBLE"
        
        mc = res["metrics_comparison"]
        assert mc["baseline_method"] == "CONVENTIONAL_ASAP_DISPATCH"
        assert mc["measurement_nature"] == "MODELED_ESTIMATES"
        assert mc["operating_assumptions"]["workload_identical"] is True
        assert mc["operating_assumptions"]["tariffs_identical"] is True
        assert mc["operating_assumptions"]["emissions_factors_identical"] is True
        
        b = mc["baseline"]
        o = mc["optimized"]
        d = mc["deltas"]
        
        # Values in INR and USD
        assert b["total_cost_inr"] > 0
        assert b["total_cost_usd"] > 0
        assert o["total_cost_inr"] > 0
        assert o["total_cost_usd"] > 0
        
        # Delta arithmetic consistency
        assert round(b["total_cost_usd"] - o["total_cost_usd"], 2) == d["cost_savings_usd"]
        assert round(b["total_cost_inr"] - o["total_cost_inr"], 2) == d["cost_savings_inr"]
        assert round(b["grid_emissions_kg_co2"] - o["grid_emissions_kg_co2"], 2) == d["emissions_reduction_kg_co2"]

    def test_baseline_dispatch_honors_precedence_and_maintenance(self):
        tasks = [
            {"task_id": "A", "task_load_kw": 100.0, "task_duration_h": 2, "dependencies": []},
            {"task_id": "B", "task_load_kw": 100.0, "task_duration_h": 2, "dependencies": ["A"], "min_lag_h": 2}
        ]
        base = calculate_baseline_schedule(tasks, solar_capacity_kw=100.0, maintenance_window=(2, 5))
        assert base["baseline_method"] == "CONVENTIONAL_ASAP_DISPATCH"
        assert base["is_feasible"] is True
        assert len(base["tasks_scheduled"]) == 2
        
        sched = {t["task_id"]: t for t in base["tasks_scheduled"]}
        # B start >= A end + 2
        assert sched["B"]["start_hour"] >= sched["A"]["end_hour"] + 2


class TestStructuredConstraintAuditLog:
    """Test Priority 3: SATISFIED, BINDING, VIOLATED, NOT_EVALUATED statuses."""

    def test_audit_log_statuses_comprehensive(self):
        tasks = [
            {"task_id": "EAF-01", "task_load_kw": 180.0, "task_duration_h": 3, "dependencies": [], "min_lag_h": 0},
            {"task_id": "LRF-01", "task_load_kw": 90.0, "task_duration_h": 2, "dependencies": ["EAF-01"], "min_lag_h": 1, "max_lag_h": 2}
        ]
        res = optimize_shift_schedule(tasks=tasks, battery_capacity_kwh=50.0, battery_rate_kw=25.0)
        audit = {entry["constraint_id"]: entry for entry in res["constraint_audit_log"]}
        
        assert "C-DEMAND-01" in audit
        assert "C-MAINT-01" in audit
        assert "C-PF-01" in audit
        assert "C-BESS-SOC-01" in audit
        assert "C-BESS-CRATE-01" in audit
        assert "C-PRECEDENCE-01" in audit
        assert "C-BUFFER-LAG-01" in audit
        
        for cid, entry in audit.items():
            assert entry["status"] in ["SATISFIED", "BINDING", "VIOLATED", "NOT_EVALUATED"]
            assert len(entry["explanation"]) > 0
            assert "applicable_limit" in entry
            assert "observed_value" in entry

    def test_not_evaluated_status_when_bess_is_zero(self):
        """When battery is 0 kWh, SoC and C-rate must be NOT_EVALUATED."""
        tasks = [
            {"task_id": "T1", "task_load_kw": 100.0, "task_duration_h": 3, "dependencies": []}
        ]
        res = optimize_shift_schedule(tasks=tasks, battery_capacity_kwh=0.0, battery_rate_kw=0.0)
        audit = {entry["constraint_id"]: entry for entry in res["constraint_audit_log"]}
        
        assert audit["C-BESS-SOC-01"]["status"] == "NOT_EVALUATED"
        assert audit["C-BESS-CRATE-01"]["status"] == "NOT_EVALUATED"

    def test_not_evaluated_status_for_standalone_precedence(self):
        """Standalone single-task run must mark precedence and buffer lag as NOT_EVALUATED."""
        res = optimize_shift_schedule(task_load_kw=100.0, task_duration_h=4)
        audit = {entry["constraint_id"]: entry for entry in res["constraint_audit_log"]}
        
        assert audit["C-PRECEDENCE-01"]["status"] == "NOT_EVALUATED"
        assert audit["C-BUFFER-LAG-01"]["status"] == "NOT_EVALUATED"

    def test_binding_constraint_detected_at_buffer_boundary(self):
        """When buffer lag exactly equals min_lag or max_lag, it is marked BINDING."""
        tasks_sched = [
            {"task_id": "T1", "start_hour": 6, "end_hour": 9, "dependencies": []},
            {"task_id": "T2", "start_hour": 10, "end_hour": 12, "dependencies": ["T1"], "min_lag_h": 1, "max_lag_h": 3}
        ]
        # Lag is 10 - 9 = 1, which exactly equals min_lag_h = 1 -> BINDING
        audit = evaluate_constraint_audit_log(
            tasks_scheduled=tasks_sched,
            peak_grid_opt_kw=200.0,
            contract_demand_max_kw=450.0,
            maintenance_window=(2, 5),
            min_pf=0.92,
            battery_capacity_kwh=0.0,
            battery_rate_kw=0.0,
            min_soc_kwh=0.0,
            max_soc_kwh=0.0,
            max_charge_kw=0.0,
            max_discharge_kw=0.0,
            has_tasks_dependencies=True
        )
        lag_entry = next(e for e in audit if e["constraint_id"] == "C-BUFFER-LAG-01")
        assert lag_entry["status"] == "BINDING"

    def test_violated_constraint_detected_when_exceeding_contract_demand(self):
        """When peak grid demand exceeds contract ceiling, C-DEMAND-01 is marked VIOLATED."""
        audit = evaluate_constraint_audit_log(
            tasks_scheduled=[],
            peak_grid_opt_kw=520.0,
            contract_demand_max_kw=450.0,
            maintenance_window=None,
            min_pf=0.92,
            battery_capacity_kwh=0.0,
            battery_rate_kw=0.0,
            min_soc_kwh=0.0,
            max_soc_kwh=0.0,
            max_charge_kw=0.0,
            max_discharge_kw=0.0,
            has_tasks_dependencies=False
        )
        demand_entry = next(e for e in audit if e["constraint_id"] == "C-DEMAND-01")
        assert demand_entry["status"] == "VIOLATED"
        assert "exceeded" in demand_entry["explanation"].lower()


class TestBackwardCompatibility:
    """Ensure zero regressions for existing single-task invocations."""

    def test_legacy_single_task_call_preserves_all_original_fields(self):
        res = optimize_shift_schedule(task_load_kw=100.0, task_duration_h=4, solar_capacity_kw=150.0)
        
        # Legacy fields
        assert "best_start_hour" in res
        assert "best_cost" in res
        assert "best_carbon_kg" in res
        assert "best_hourly_details" in res
        assert "baseline" in res
        assert "savings" in res
        assert "validation" in res
        assert "battery_final_soh_pct" in res
        assert "battery_degradation_pct" in res
        assert "constraints_respected" in res
        assert "plan_comparison" in res
        
        # New Phase 3 operational realism fields
        assert "constraint_audit_log" in res
        assert "metrics_comparison" in res
        assert "tasks_scheduled" in res
        assert "precedence_summary" in res
        assert "dependency_graph_status" in res


class TestFastAPIIntegrationAndDecisionCenter:
    """Test Priority 4: API endpoints and Decision Center integration."""

    def test_api_scheduler_optimize_endpoint_with_tasks(self):
        payload = {
            "tenant_id": "demo_steel",
            "solar_capacity_kw": 150.0,
            "tasks": [
                {"task_id": "EAF-01", "name": "Electric Arc Furnace", "task_load_kw": 180.0, "task_duration_h": 3, "dependencies": [], "min_lag_h": 0},
                {"task_id": "LRF-01", "name": "Ladle Refining", "task_load_kw": 90.0, "task_duration_h": 2, "dependencies": ["EAF-01"], "min_lag_h": 1, "max_lag_h": 3}
            ]
        }
        res = client.post("/api/v1/scheduler/optimize", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        opt = data["optimization"]
        assert opt["status"] == "FEASIBLE"
        assert len(opt["tasks_scheduled"]) == 2
        assert "constraint_audit_log" in opt
        assert "metrics_comparison" in opt

    def test_api_schedule_endpoint_backward_compatibility(self):
        payload = {
            "tenant_id": "demo_steel",
            "task_load_kw": 100.0,
            "task_duration_h": 4,
            "solar_capacity_kw": 150.0
        }
        res = client.post("/api/schedule", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "best_start_hour" in data
        assert "constraint_audit_log" in data
        assert "metrics_comparison" in data

    def test_api_decision_overview_includes_operational_realism(self):
        res = client.get("/api/v1/decision/overview")
        assert res.status_code == 200
        data = res.json()
        dc = data["decision_center"]
        assert "constraint_audit_log" in dc
        assert "metrics_comparison" in dc
        assert "tasks_scheduled" in dc

    def test_api_decision_generate_with_multi_stage_tasks(self):
        payload = {
            "tenant_id": "demo_steel",
            "sector": "Steel",
            "task_load_kw": 180.0,
            "duration_hours": 3,
            "tasks": [
                {"task_id": "EAF-01", "name": "Electric Arc Melting", "task_load_kw": 180.0, "task_duration_h": 3, "dependencies": [], "min_lag_h": 0},
                {"task_id": "LRF-01", "name": "Ladle Refining", "task_load_kw": 90.0, "task_duration_h": 2, "dependencies": ["EAF-01"], "min_lag_h": 1, "max_lag_h": 3},
                {"task_id": "CCM-01", "name": "Continuous Casting", "task_load_kw": 60.0, "task_duration_h": 2, "dependencies": ["LRF-01"], "min_lag_h": 0, "max_lag_h": 2}
            ]
        }
        res = client.post("/api/v1/decision/generate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        dc = data["decision_center"]
        assert len(dc["tasks_scheduled"]) == 3
        assert len(dc["precedence_summary"]) == 2
        assert "constraint_audit_log" in dc
        assert "metrics_comparison" in dc
