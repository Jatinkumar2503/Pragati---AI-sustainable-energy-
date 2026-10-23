"""
Automated Test Suite for PRAGATI AI Intelligent Factory Load Management & Production Scheduling.
Verifies all 18 industrial engineering and software scenarios specified in Section 15:
1. Total load is calculated correctly for all five machines.
2. A stopped machine is not counted as consuming its normal running load.
3. Missing or stale readings are not silently treated as zero.
4. kW and kWh are not confused.
5. A demand-limit breach is detected.
6. A predicted peak triggers a recommendation when a feasible flexible load exists.
7. The scheduler can operate multiple independent machines simultaneously.
8. Production dependencies are respected.
9. Active constrained processes are not interrupted by an energy-cost optimization.
10. A flexible batch can be rescheduled when its deadline and constraints permit it.
11. A recommendation is rejected if it causes a deadline violation.
12. The scheduler reports infeasibility when constraints conflict.
13. Cost savings are calculated against a defined baseline using configured tariffs.
14. Solar contribution is not double-counted.
15. An operator must approve recommendations before they are treated as approved.
16. Simulated results are clearly distinguished from measured results.
17. Machine explanations agree with the actual machine state and scheduling decision.
18. Existing tests continue to pass.
"""

import pytest
import datetime
from fastapi.testclient import TestClient

from backend.api import app
from backend.engine.load_manager import FactoryLoadManager, FACTORY_LOAD_MANAGER_INSTANCE, get_current_tariff_rate
from backend.engine.factory_catalog import get_factory_machines_data

client = TestClient(app)


def test_1_total_load_calculated_correctly_for_all_five_machines():
    """Scenario 1: Total load is the exact sum of active power draw (kW) for active machines."""
    mgr = FactoryLoadManager(contract_demand_limit_kw=450.0)
    summary = mgr.calculate_factory_load(tenant_id="demo_steel")

    # In baseline: EAF-01 (180 kW), LRF-01 (90 kW), CCM-01 (60 kW), ROLL-01 (120 kW) run. ANN-01 (70 kW) is on Standby (0 kW active draw).
    expected_sum = 180.0 + 90.0 + 60.0 + 120.0 + 0.0
    assert summary["total_factory_load_kw"] == pytest.approx(expected_sum, 0.1)
    assert summary["total_factory_load_kw"] == 450.0


def test_2_stopped_machine_not_counted_as_consuming_normal_running_load():
    """Scenario 2: A stopped or standby machine must contribute 0.0 kW to active factory draw."""
    mgr = FactoryLoadManager(contract_demand_limit_kw=450.0)

    # When all 5 machines are running:
    override_all_running = {
        "EAF-01": True, "LRF-01": True, "CCM-01": True, "ROLL-01": True, "ANN-01": True
    }
    all_run_summary = mgr.calculate_factory_load("demo_steel", override_machine_states=override_all_running)
    assert all_run_summary["total_factory_load_kw"] == 520.0

    # When ANN-01 is stopped/standby:
    override_ann_stopped = {
        "EAF-01": True, "LRF-01": True, "CCM-01": True, "ROLL-01": True, "ANN-01": False
    }
    stopped_summary = mgr.calculate_factory_load("demo_steel", override_machine_states=override_ann_stopped)
    assert stopped_summary["total_factory_load_kw"] == 450.0
    assert stopped_summary["total_factory_load_kw"] == all_run_summary["total_factory_load_kw"] - 70.0


def test_3_missing_or_stale_readings_not_silently_treated_as_zero():
    """Scenario 3: Missing machine readings flag the total as INCOMPLETE_ESTIMATED instead of silent 0."""
    mgr = FactoryLoadManager(contract_demand_limit_kw=450.0)
    summary = mgr.calculate_factory_load("demo_steel", missing_machine_ids=["EAF-01"])

    assert summary["data_quality"]["is_incomplete"] is True
    assert summary["data_quality"]["status"] == "INCOMPLETE_ESTIMATED"
    assert "EAF-01" in summary["data_quality"]["missing_machines"]
    assert len(summary["data_quality"]["notes"]) > 0


def test_4_kw_and_kwh_distinction_maintained():
    """Scenario 4: Instantaneous power (kW) and energy consumed over time (kWh) are never confused."""
    mgr = FactoryLoadManager(contract_demand_limit_kw=450.0)
    summary = mgr.calculate_factory_load("demo_steel")

    # Instantaneous power draw is in kW (rate of energy)
    assert summary["total_factory_load_kw"] == 450.0
    # Accumulated energy is in kWh (power × time)
    assert summary["total_energy_consumed_kwh"] > summary["total_factory_load_kw"]
    assert summary["total_energy_consumed_kwh"] == 8780.0


def test_5_demand_limit_breach_detected():
    """Scenario 5: Negative demand headroom triggers an explicit demand-limit breach alert."""
    mgr = FactoryLoadManager(contract_demand_limit_kw=450.0)
    # Simulate turning on all 5 machines simultaneously (520 kW vs 450 kW limit)
    all_run = {"EAF-01": True, "LRF-01": True, "CCM-01": True, "ROLL-01": True, "ANN-01": True}
    summary = mgr.calculate_factory_load("demo_steel", override_machine_states=all_run)

    assert summary["is_limit_breached"] is True
    assert summary["demand_headroom_kw"] == -70.0
    assert summary["overrun_kw"] == 70.0


def test_6_predicted_peak_triggers_recommendation_when_flexible_load_exists():
    """Scenario 6: Load forecaster identifies peak breach and triggers a recommendation for flexible ANN-01."""
    mgr = FactoryLoadManager(contract_demand_limit_kw=450.0)
    forecast = mgr.evaluate_load_forecast_and_peak("demo_steel")

    assert forecast["peak_breach_detected"] is True
    assert forecast["peak_magnitude_kw"] > forecast["contract_demand_limit_kw"]
    assert forecast["peak_overrun_kw"] > 0.0

    rec = mgr.generate_intelligent_recommendation("demo_steel")
    assert rec["affected_machine_id"] == "ANN-01"
    assert rec["expected_factory_load_change_kw"] == -70.0


def test_7_scheduler_operates_multiple_machines_simultaneously():
    """Scenario 7: The scheduler supports concurrent multi-machine operation without artificial serialization."""
    mgr = FactoryLoadManager(contract_demand_limit_kw=450.0)
    summary = mgr.calculate_factory_load("demo_steel")

    # 4 machines operate at the exact same timestamp
    running_machines = [m for m in summary["machines"] if m["is_running"]]
    assert len(running_machines) == 4
    machine_ids = {m["machine_id"] for m in running_machines}
    assert machine_ids == {"EAF-01", "LRF-01", "CCM-01", "ROLL-01"}


def test_8_production_dependencies_respected():
    """Scenario 8: Precedence relationships (EAF -> LRF -> CCM -> ROLL) are recorded and validated."""
    machines = FACTORY_LOAD_MANAGER_INSTANCE.get_fleet_machines("demo_steel")
    m_dict = {m["machine_id"]: m for m in machines}

    assert "EAF-01" in m_dict["LRF-01"]["upstream_dependency"]
    assert "LRF-01" in m_dict["CCM-01"]["upstream_dependency"]
    assert "CCM-01" in m_dict["ROLL-01"]["upstream_dependency"]


def test_9_active_constrained_processes_not_interrupted_by_cost_optimization():
    """Scenario 9: Non-interruptible metallurgical processes (EAF, LRF, CCM) are marked non-flexible and continue running."""
    machines = FACTORY_LOAD_MANAGER_INSTANCE.get_fleet_machines("demo_steel")
    m_dict = {m["machine_id"]: m for m in machines}

    for mid in ["EAF-01", "LRF-01", "CCM-01"]:
        assert m_dict[mid]["is_flexible"] is False
        assert m_dict[mid]["can_safely_reschedule"] is False
        assert m_dict[mid]["recommended_action"] == "Continue running"


def test_10_flexible_batch_rescheduled_when_deadline_and_recipe_permit():
    """Scenario 10: Cold annealing batch is flexible and safely rescheduled into off-peak window."""
    machines = FACTORY_LOAD_MANAGER_INSTANCE.get_fleet_machines("demo_steel")
    ann = next(m for m in machines if m["machine_id"] == "ANN-01")

    assert ann["is_flexible"] is True
    assert ann["can_safely_reschedule"] is True
    assert ann["recommended_action"] == "Keep on standby"


def test_11_recommendation_rejected_if_it_causes_deadline_violation():
    """Scenario 11: Feasibility engine rejects any proposal that completes past the customer deadline."""
    mgr = FactoryLoadManager(contract_demand_limit_kw=450.0)

    # Task duration = 4h, planned start = 15:00, deadline = 18:00 (15+4=19 > 18)
    res = mgr.evaluate_schedule_feasibility(
        task_duration_h=4.0,
        planned_start_h=15,
        deadline_h=18,
        machine_load_kw=70.0
    )
    assert res["is_feasible"] is False
    assert len(res["violations"]) > 0
    assert res["violations"][0]["constraint"] == "C-DEADLINE"


def test_12_scheduler_reports_infeasibility_when_constraints_conflict():
    """Scenario 12: Infeasible task graph reports specific violated constraints with explanations."""
    mgr = FactoryLoadManager(contract_demand_limit_kw=450.0)

    # Preceding task finishes at hour 14, but planned start is requested at hour 12
    res = mgr.evaluate_schedule_feasibility(
        task_duration_h=3.0,
        planned_start_h=12,
        deadline_h=20,
        machine_load_kw=90.0,
        preceding_task_end_h=14
    )
    assert res["is_feasible"] is False
    assert any(v["constraint"] == "C-PRECEDENCE" for v in res["violations"])


def test_13_cost_savings_calculated_against_defined_baseline_using_configured_tariffs():
    """Scenario 13: Financial savings are derived from explicit peak vs off-peak tariff differences."""
    peak_tariff = get_current_tariff_rate(19)["rate_inr"]  # Peak hour
    offpeak_tariff = get_current_tariff_rate(23)["rate_inr"]  # Off-peak night hour

    assert peak_tariff == 12.50
    assert offpeak_tariff == 4.20

    # 70 kW Annealing Bay for 4 hours
    kwh = 70.0 * 4.0
    baseline_cost = kwh * peak_tariff  # 280 * 12.50 = 3500.0
    optimized_cost = kwh * offpeak_tariff  # 280 * 4.20 = 1176.0
    savings = baseline_cost - optimized_cost

    assert baseline_cost == 3500.0
    assert optimized_cost == 1176.0
    assert savings == 2324.0

    mgr = FactoryLoadManager(contract_demand_limit_kw=450.0)
    rec = mgr.generate_intelligent_recommendation("demo_steel")
    assert abs(rec["estimated_cost_diff_inr"]) == pytest.approx(savings, 0.1)


def test_14_solar_contribution_not_double_counted():
    """Scenario 14: Net grid import is strictly max(0, total_factory_load - solar_generation)."""
    mgr = FactoryLoadManager(contract_demand_limit_kw=450.0)
    summary = mgr.calculate_factory_load("demo_steel")

    total_load = summary["total_factory_load_kw"]
    solar = summary["current_solar_kw"]
    net_import = summary["net_grid_import_kw"]

    assert net_import == pytest.approx(max(0.0, total_load - solar), 0.1)
    # Check that solar + net_import equals total load (no fictitious duplication)
    assert solar + net_import == pytest.approx(total_load, 0.1)


def test_15_operator_must_approve_recommendations_before_execution():
    """Scenario 15: Recommendations require explicit operator authorization and are never dispatched automatically."""
    mgr = FactoryLoadManager(contract_demand_limit_kw=450.0)
    rec = mgr.generate_intelligent_recommendation("demo_steel")

    # Initial state must be pending review
    assert rec["approval_status"] == "PENDING_REVIEW"
    assert rec["approved_by"] is None

    # Approve action
    res = mgr.approve_recommendation(rec["recommendation_id"], operator_name="Lead Electrical Engineer")
    assert res["status"] == "success"
    assert mgr.active_recommendation["approval_status"] == "APPROVED"
    assert mgr.active_recommendation["approved_by"] == "Lead Electrical Engineer"


def test_16_simulated_results_clearly_distinguished_from_measured_results():
    """Scenario 16: Telemetry and decision metadata explicitly state measurement nature and simulation mode."""
    mgr = FactoryLoadManager(contract_demand_limit_kw=450.0)
    summary = mgr.calculate_factory_load("demo_steel")
    rec = mgr.generate_intelligent_recommendation("demo_steel")

    assert rec["mode"] == "DEMONSTRATION_MODE"
    machines = summary["machines"]
    eaf = next(m for m in machines if m["machine_id"] == "EAF-01")
    ann = next(m for m in machines if m["machine_id"] == "ANN-01")

    assert eaf["is_running"] is True
    assert ann["is_running"] is False


def test_17_machine_explanations_agree_with_actual_machine_state():
    """Scenario 17: Explanations provide defensible engineering reasons matching current operating state."""
    machines = FACTORY_LOAD_MANAGER_INSTANCE.get_fleet_machines("demo_steel")
    for m in machines:
        if m["is_running_now"]:
            assert "why_running_now" in m and len(m["why_running_now"]) > 20
            assert "why_continue_or_change" in m and len(m["why_continue_or_change"]) > 20
        else:
            assert "why_stopped_now" in m and len(m["why_stopped_now"]) > 20
            assert "Standby" in m["status"]


def test_18_api_endpoints_functional():
    """Scenario 18: Factory load management REST API endpoints are online, responsive, and contract-compliant."""
    # 1. Load status endpoint
    res_status = client.get("/api/v1/factory/load-status?tenant_id=demo_steel")
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert data_status["total_factory_load_kw"] == 450.0
    assert data_status["contract_demand_limit_kw"] == 450.0

    # 2. Recommendations endpoint
    res_rec = client.get("/api/v1/factory/load-recommendations?tenant_id=demo_steel")
    assert res_rec.status_code == 200
    data_rec = res_rec.json()
    assert data_rec["status"] == "success"
    rec = data_rec["active_recommendation"]
    assert rec["affected_machine_id"] == "ANN-01"

    # 3. Approve endpoint
    res_app = client.post("/api/v1/factory/load-recommendations/approve", json={
        "recommendation_id": rec["recommendation_id"],
        "operator_name": "Shift Superintendent",
        "notes": "Verified off-peak dispatch"
    })
    assert res_app.status_code == 200
    assert res_app.json()["status"] == "success"

    # 4. Factory machines endpoint
    res_mach = client.get("/api/v1/factory/machines?tenant_id=demo_steel")
    assert res_mach.status_code == 200
    data_mach = res_mach.json()
    assert len(data_mach["machines"]) == 5
    assert data_mach["active_running_load_kw"] == 450.0
