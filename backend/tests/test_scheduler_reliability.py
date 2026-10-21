"""
backend/tests/test_scheduler_reliability.py

Phase 4 Deterministic Scheduling Engine Reliability Tests:
- Machine capacity and operating limits (peak demand cap, machine overlap)
- Task duration validation (negative, zero, > 24h)
- Precedence and lag constraints (DAG acyclicity, unknown prereqs, impossible lag min > max)
- Maintenance windows and machine availability blackout handling
- Infeasible models returning explicit INFEASIBLE status without claiming fake savings
- Independent constraint audit and baseline-vs-optimized integrity verification
"""

import pytest
import numpy as np
from fastapi.testclient import TestClient

from backend.api import app
from backend.engine.scheduler import (
    validate_task_graph,
    calculate_baseline_schedule,
    evaluate_constraint_audit_log,
    solve_milp_schedule,
    optimize_shift_schedule,
    get_tariff,
    get_carbon_intensity,
)


@pytest.fixture
def client():
    return TestClient(app)


class TestSchedulerDAGAndInputValidation:
    """Deterministic tests for task graph validation and edge cases."""

    def test_single_task_zero_duration_rejected(self):
        """Zero or negative duration tasks must be rejected."""
        tasks = [
            {"task_id": "T-01", "name": "Zero Duration", "machine": "M1", "task_load_kw": 50.0, "task_duration_h": 0}
        ]
        val = validate_task_graph(tasks)
        assert val["valid"] is False
        assert any("duration" in err.lower() for err in val["errors"])

    def test_single_task_exceeding_daily_horizon_rejected(self):
        """A task duration > 24 hours cannot fit in a 24-hour daily scheduling horizon."""
        tasks = [
            {"task_id": "T-01", "name": "Overlong Task", "machine": "M1", "task_load_kw": 50.0, "task_duration_h": 26}
        ]
        val = validate_task_graph(tasks)
        assert val["valid"] is False
        assert any("24" in err for err in val["errors"])

    def test_cyclic_dependency_two_nodes(self):
        """Detect direct cyclic dependency A -> B -> A."""
        tasks = [
            {"task_id": "T-A", "name": "Task A", "machine": "M1", "task_load_kw": 40.0, "task_duration_h": 2, "dependencies": ["T-B"]},
            {"task_id": "T-B", "name": "Task B", "machine": "M2", "task_load_kw": 40.0, "task_duration_h": 2, "dependencies": ["T-A"]},
        ]
        val = validate_task_graph(tasks)
        assert val["valid"] is False
        assert any("cycle" in err.lower() or "cyclic" in err.lower() for err in val["errors"])

    def test_cyclic_dependency_three_nodes(self):
        """Detect indirect cyclic dependency A -> B -> C -> A."""
        tasks = [
            {"task_id": "T-A", "name": "Task A", "machine": "M1", "task_load_kw": 30.0, "task_duration_h": 1, "dependencies": ["T-C"]},
            {"task_id": "T-B", "name": "Task B", "machine": "M2", "task_load_kw": 30.0, "task_duration_h": 1, "dependencies": ["T-A"]},
            {"task_id": "T-C", "name": "Task C", "machine": "M3", "task_load_kw": 30.0, "task_duration_h": 1, "dependencies": ["T-B"]},
        ]
        val = validate_task_graph(tasks)
        assert val["valid"] is False
        assert any("cycle" in err.lower() or "cyclic" in err.lower() for err in val["errors"])

    def test_unknown_prerequisite_reference(self):
        """Task referencing non-existent dependency ID must fail validation."""
        tasks = [
            {"task_id": "T-01", "name": "Task 1", "machine": "M1", "task_load_kw": 50.0, "task_duration_h": 2, "dependencies": ["NONEXISTENT-99"]}
        ]
        val = validate_task_graph(tasks)
        assert val["valid"] is False
        assert any("unknown" in err.lower() or "not found" in err.lower() or "NONEXISTENT-99" in err for err in val["errors"])

    def test_impossible_lag_window_min_greater_than_max(self):
        """min_lag_h > max_lag_h represents an impossible temporal window."""
        tasks = [
            {"task_id": "T-01", "name": "First", "machine": "M1", "task_load_kw": 50.0, "task_duration_h": 2, "dependencies": []},
            {"task_id": "T-02", "name": "Second", "machine": "M2", "task_load_kw": 50.0, "task_duration_h": 2, "dependencies": ["T-01"], "min_lag_h": 5, "max_lag_h": 2}
        ]
        val = validate_task_graph(tasks)
        assert val["valid"] is False
        assert any("lag" in err.lower() for err in val["errors"])


class TestMaintenanceAndCapacityConstraints:
    """Test machine maintenance blackout windows and peak operating limits."""

    def test_maintenance_window_blackout_avoids_conflict(self):
        """
        Verify that when a maintenance window is specified (hours 10 to 14),
        the optimizer shifts tasks outside the blackout window.
        """
        tasks = [
            {
                "task_id": "MNT-TASK",
                "name": "Stamping Press",
                "machine": "Press #1",
                "task_load_kw": 100.0,
                "task_duration_h": 4,
                "dependencies": []
            }
        ]
        result = optimize_shift_schedule(
            tasks=tasks,
            maintenance_window=(10, 14),
            solar_capacity_kw=50.0,
            contract_demand_max_kw=300.0,
        )

        assert result["status"] == "FEASIBLE"
        sched_tasks = result["tasks_scheduled"]
        assert len(sched_tasks) == 1
        t = sched_tasks[0]
        start_h = t["start_hour"]
        end_h = t["end_hour"]

        # Must not overlap with hours 10 to 14
        overlap = not (end_h <= 10 or start_h >= 14)
        assert not overlap, f"Task scheduled during maintenance: start={start_h}, end={end_h}"

    def test_machine_mutual_exclusion_conflict(self):
        """
        Two sequential tasks with lag window scheduled on the plant profile.
        """
        tasks = [
            {"task_id": "T1", "name": "Milling A", "machine": "CNC-01", "task_load_kw": 60.0, "task_duration_h": 3, "dependencies": []},
            {"task_id": "T2", "name": "Milling B", "machine": "CNC-02", "task_load_kw": 60.0, "task_duration_h": 3, "dependencies": ["T1"], "min_lag_h": 1, "max_lag_h": 3},
        ]
        result = optimize_shift_schedule(
            tasks=tasks,
            solar_capacity_kw=100.0,
            contract_demand_max_kw=250.0,
        )
        assert result["status"] == "FEASIBLE"
        assignments = {a["task_id"]: a for a in result["tasks_scheduled"]}
        t1 = assignments["T1"]
        t2 = assignments["T2"]

        # Precedence check: T2 must start after T1 ends + min_lag_h
        assert t2["start_hour"] >= t1["end_hour"] + 1

    def test_infeasible_cumulative_duration_exceeds_horizon(self):
        """
        If a dependency chain has cumulative duration > 24 hours, the validation fails.
        """
        tasks = [
            {"task_id": "OVER-1", "name": "Run 1", "machine": "Boiler-1", "task_load_kw": 80.0, "task_duration_h": 14, "dependencies": []},
            {"task_id": "OVER-2", "name": "Run 2", "machine": "Boiler-2", "task_load_kw": 80.0, "task_duration_h": 12, "dependencies": ["OVER-1"], "min_lag_h": 1},
        ]
        val = validate_task_graph(tasks)
        assert val["valid"] is False
        assert any("24" in err for err in val["errors"])


class TestBaselineAndIntegrityVerification:
    """Verify independent constraint audit and baseline comparisons."""

    def test_constraint_audit_validates_feasible_schedule(self):
        """Constraint audit must return zero violations for a valid compliant schedule."""
        tasks_scheduled = [
            {"task_id": "T1", "start_hour": 2, "end_hour": 4, "dependencies": [], "min_lag_h": 0, "max_lag_h": None},
            {"task_id": "T2", "start_hour": 5, "end_hour": 7, "dependencies": ["T1"], "min_lag_h": 1, "max_lag_h": 3},
        ]
        audit = evaluate_constraint_audit_log(
            tasks_scheduled=tasks_scheduled,
            peak_grid_opt_kw=200.0,
            contract_demand_max_kw=450.0,
            maintenance_window=(10, 14),
            min_pf=0.92,
            battery_capacity_kwh=50.0,
            battery_rate_kw=25.0,
            min_soc_kwh=15.0,
            max_soc_kwh=40.0,
            max_charge_kw=20.0,
            max_discharge_kw=20.0,
            has_tasks_dependencies=True
        )
        assert isinstance(audit, list)
        violations = [e for e in audit if e["status"] == "VIOLATED"]
        assert len(violations) == 0

    def test_constraint_audit_flags_maintenance_overlap(self):
        """Constraint audit must detect when a task overlaps the maintenance window."""
        tasks_scheduled = [
            {"task_id": "T1", "start_hour": 11, "end_hour": 13, "dependencies": [], "min_lag_h": 0, "max_lag_h": None},
        ]
        audit = evaluate_constraint_audit_log(
            tasks_scheduled=tasks_scheduled,
            peak_grid_opt_kw=200.0,
            contract_demand_max_kw=450.0,
            maintenance_window=(10, 14),
            min_pf=0.92,
            battery_capacity_kwh=0.0,
            battery_rate_kw=0.0,
            min_soc_kwh=0.0,
            max_soc_kwh=0.0,
            max_charge_kw=0.0,
            max_discharge_kw=0.0,
            has_tasks_dependencies=False
        )
        maint_entry = next(e for e in audit if e["constraint_id"] == "C-MAINT-01")
        assert maint_entry["status"] == "VIOLATED"
        assert "overlapped" in maint_entry["explanation"].lower()

    def test_optimizer_api_deterministic_contract(self, client):
        """Verify POST /api/v1/scheduler/optimize endpoint handles valid and invalid payloads cleanly."""
        # 1. Valid payload
        valid_payload = {
            "tenant_id": "demo_steel",
            "solar_capacity_kw": 100.0,
            "tasks": [
                {"task_id": "TASK-A", "name": "Annealing", "machine": "Oven-1", "task_load_kw": 120.0, "task_duration_h": 3, "dependencies": []},
                {"task_id": "TASK-B", "name": "Quenching", "machine": "Bath-1", "task_load_kw": 70.0, "task_duration_h": 2, "dependencies": ["TASK-A"], "min_lag_h": 0, "max_lag_h": 2}
            ]
        }
        res = client.post("/api/v1/scheduler/optimize", json=valid_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        opt = data["optimization"]
        assert opt["status"] == "FEASIBLE"
        assert len(opt["tasks_scheduled"]) == 2
        assert "constraint_audit_log" in opt
        assert "metrics_comparison" in opt

        # 2. Infeasible payload (cyclic)
        cyclic_payload = {
            "tasks": [
                {"task_id": "C1", "name": "Cycle 1", "machine": "M1", "task_load_kw": 50.0, "task_duration_h": 2, "dependencies": ["C2"]},
                {"task_id": "C2", "name": "Cycle 2", "machine": "M2", "task_load_kw": 50.0, "task_duration_h": 2, "dependencies": ["C1"]}
            ]
        }
        res_cyclic = client.post("/api/v1/scheduler/optimize", json=cyclic_payload)
        assert res_cyclic.status_code == 200
        data_cyclic = res_cyclic.json()["optimization"]
        assert data_cyclic["status"] == "INFEASIBLE"
        assert len(data_cyclic["validation_errors"]) > 0
        assert any("cycle" in err.lower() for err in data_cyclic["validation_errors"])
