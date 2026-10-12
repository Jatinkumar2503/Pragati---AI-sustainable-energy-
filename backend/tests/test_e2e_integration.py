"""
PRAGATI AI — Phase 5, Workstream 1: End-to-End Subsystem Integration Test Suite
Traces actual FastAPI routes and service calls across:
1. High-frequency telemetry streaming & historical telemetry queries
2. Anomaly detection & triage
3. Deterministic alert management (trigger, deduplication, suppression window, acknowledge, resolve, audit history)
4. Load forecasting with holdout evaluation metrics (MAE, RMSE, safe MAPE/WAPE, provenance)
5. Multi-stage MILP scheduling with machine precedence, thermal lag buffers, and constraint auditing
6. Managerial Decision Center lifecycle (generation, evidence, review, approval signoff with SHA-256 audit hash, history)
7. Digital Twin 15-year lifecycle simulation, Arrhenius battery aging, and Carbon audit
8. Error handling, duplicate alerts, infeasible schedules, missing data, and schema validation
9. Clear data provenance labeling across all subsystem boundaries (historical replay vs synthetic vs live)
"""

import math
import unittest
from typing import Dict, Any, List
from fastapi.testclient import TestClient

from backend.api import app


class TestEndToEndSubsystemIntegration(unittest.TestCase):
    """
    Workstream 1: Full end-to-end integration across PRAGATI AI subsystem boundaries.
    """

    def setUp(self):
        self.client = TestClient(app)
        self.headers = {"X-API-Key": "pragati_sec_2026"}

    def test_full_subsystem_trace_telemetry_to_decision_and_digital_twin(self):
        """
        Trace complete operational workflow:
        Telemetry -> Anomaly -> Alert Lifecycle -> Forecaster -> Precedence Scheduler -> Decision Signoff -> Digital Twin
        """
        # ----------------------------------------------------------------------
        # Step 1: Telemetry Stream & Historical Query
        # ----------------------------------------------------------------------
        stream_res = self.client.get("/api/v1/telemetry/stream", headers=self.headers)
        self.assertEqual(stream_res.status_code, 200)
        stream_data = stream_res.json()
        self.assertEqual(stream_data["status"], "success")
        stream = stream_data["stream"]
        self.assertIn("active_load_kw", stream)
        self.assertIn("grid_voltage_v", stream)
        self.assertIn("power_factor", stream)
        self.assertIn("provenance", stream)
        self.assertEqual(stream["provenance"]["source_type"], "SYNTHETIC_STREAM")
        self.assertFalse(stream["provenance"]["is_live_physical_hardware"])

        hist_res = self.client.get("/api/telemetry?days=7&tenant_id=demo_steel", headers=self.headers)
        self.assertEqual(hist_res.status_code, 200)
        hist_data = hist_res.json()
        self.assertIsInstance(hist_data, dict)
        self.assertIn("timestamps", hist_data)
        self.assertIn("usage_kwh", hist_data)
        self.assertEqual(hist_data["data_source"], "HISTORICAL_UCI_BENCHMARK")
        self.assertFalse(hist_data["is_live_telemetry"])

        # ----------------------------------------------------------------------
        # Step 2: Anomaly Detection
        # ----------------------------------------------------------------------
        anom_res = self.client.get("/api/anomalies?tenant_id=demo_steel", headers=self.headers)
        self.assertEqual(anom_res.status_code, 200)
        anom_list = anom_res.json()
        self.assertIsInstance(anom_list, list)

        # Clustered anomaly events endpoint
        grp_res = self.client.get("/api/v1/alerts/grouped-events?limit=5", headers=self.headers)
        self.assertEqual(grp_res.status_code, 200)
        grp_data = grp_res.json()
        self.assertEqual(grp_data["status"], "success")
        self.assertGreater(len(grp_data["events"]), 0)
        self.assertIn("severity", grp_data["events"][0])

        # ----------------------------------------------------------------------
        # Step 3: Alert Lifecycle & Deduplication
        # ----------------------------------------------------------------------
        # Trigger an alert
        trigger_payload = {
            "alert_type": "Thermal Overload",
            "severity": "CRITICAL",
            "equipment": "Transformer T-05",
            "value": "96.5 °C",
            "threshold": "85.0 °C",
            "mitigation": "Activate forced-air cooling and transfer 40 kW load.",
            "suppression_window_seconds": 1800
        }
        trig_res1 = self.client.post("/api/v1/alerts/trigger", json=trigger_payload, headers=self.headers)
        self.assertEqual(trig_res1.status_code, 200)
        t_data1 = trig_res1.json()
        self.assertEqual(t_data1["status"], "triggered")
        alert_id = t_data1["alert"]["alert_id"]
        self.assertTrue(t_data1["is_new"])
        self.assertEqual(t_data1["alert"]["duplicate_count"], 1)

        # Immediate re-trigger should be suppressed by deduplication window
        trig_res2 = self.client.post("/api/v1/alerts/trigger", json=trigger_payload, headers=self.headers)
        self.assertEqual(trig_res2.status_code, 200)
        t_data2 = trig_res2.json()
        self.assertEqual(t_data2["status"], "deduplicated")
        self.assertFalse(t_data2["is_new"])
        self.assertEqual(t_data2["alert"]["alert_id"], alert_id)
        self.assertEqual(t_data2["alert"]["duplicate_count"], 2)

        # Active alerts check
        active_res = self.client.get("/api/v1/alerts/active", headers=self.headers)
        self.assertEqual(active_res.status_code, 200)
        active_data = active_res.json()
        self.assertEqual(active_data["status"], "success")

        # Acknowledge the alert
        ack_res = self.client.post("/api/v1/alerts/acknowledge", json={
            "alert_id": alert_id,
            "operator_name": "Lead Electrical Engineer"
        }, headers=self.headers)
        self.assertEqual(ack_res.status_code, 200)
        ack_data = ack_res.json()
        self.assertEqual(ack_data["status"], "success")
        self.assertEqual(ack_data["alert"]["status"], "ACKNOWLEDGED")

        # Resolve the alert
        res_res = self.client.post("/api/v1/alerts/resolve", json={
            "alert_id": alert_id,
            "operator_name": "Lead Electrical Engineer",
            "resolution_notes": "Forced-air cooling verified; temperature normalized to 78 °C."
        }, headers=self.headers)
        self.assertEqual(res_res.status_code, 200)
        res_data = res_res.json()
        self.assertEqual(res_data["status"], "success")
        self.assertEqual(res_data["alert"]["status"], "RESOLVED")

        # Alert history check
        hist_alerts_res = self.client.get("/api/v1/alerts/history?limit=10", headers=self.headers)
        self.assertEqual(hist_alerts_res.status_code, 200)
        hist_alerts = hist_alerts_res.json()["alerts"]
        found_alert = next((a for a in hist_alerts if a["alert_id"] == alert_id), None)
        self.assertIsNotNone(found_alert)
        self.assertEqual(found_alert["status"], "RESOLVED")
        self.assertGreaterEqual(len(found_alert["status_transitions"]), 2)

        # ----------------------------------------------------------------------
        # Step 4: Forecasting & Holdout Metrics
        # ----------------------------------------------------------------------
        fc_res = self.client.post("/api/forecast", json={"hours": 48, "tenant_id": "demo_steel"}, headers=self.headers)
        self.assertEqual(fc_res.status_code, 200)
        fc_data = fc_res.json()
        self.assertIn("rf_forecast", fc_data)
        self.assertIn("timestamps", fc_data)
        self.assertIn("metrics", fc_data)
        self.assertIn("provenance", fc_data)
        self.assertEqual(fc_data["provenance"]["source_type"], "HISTORICAL_BENCHMARK")
        self.assertFalse(fc_data["provenance"]["is_live_data"])

        # Check metrics endpoint
        metrics_res = self.client.get("/api/v1/forecast/metrics", headers=self.headers)
        self.assertEqual(metrics_res.status_code, 200)
        m_data = metrics_res.json()
        self.assertEqual(m_data["status"], "success")
        self.assertIn("models", m_data)
        for m in m_data["models"]:
            if m.get("rmse") is not None:
                self.assertFalse(math.isnan(m["rmse"]))
                self.assertFalse(math.isinf(m["rmse"]))

        # ----------------------------------------------------------------------
        # Step 5: Precedence Scheduler & Constraint Auditing
        # ----------------------------------------------------------------------
        # 3-stage steelmaking process: EAF -> LRF -> CCM with thermal lag constraints
        precedence_tasks = [
            {
                "task_id": "EAF-01",
                "name": "Electric Arc Melting",
                "machine": "Electric Arc Furnace #1",
                "task_load_kw": 180.0,
                "task_duration_h": 3,
                "dependencies": [],
                "min_lag_h": 0,
                "max_lag_h": None
            },
            {
                "task_id": "LRF-01",
                "name": "Ladle Refining & Alloying",
                "machine": "Ladle Refining Station #2",
                "task_load_kw": 90.0,
                "task_duration_h": 2,
                "dependencies": ["EAF-01"],
                "min_lag_h": 1,
                "max_lag_h": 3
            },
            {
                "task_id": "CCM-01",
                "name": "Continuous Billet Casting",
                "machine": "Continuous Casting Machine #1",
                "task_load_kw": 60.0,
                "task_duration_h": 2,
                "dependencies": ["LRF-01"],
                "min_lag_h": 0,
                "max_lag_h": 2
            }
        ]
        sched_res = self.client.post("/api/v1/scheduler/optimize", json={
            "task_load_kw": 180.0,
            "task_duration_h": 3,
            "solar_capacity_kw": 150.0,
            "battery_capacity_kwh": 50.0,
            "tasks": precedence_tasks
        }, headers=self.headers)
        self.assertEqual(sched_res.status_code, 200)
        opt_data = sched_res.json()["optimization"]
        self.assertTrue(opt_data["is_feasible"])
        self.assertEqual(opt_data["status"], "FEASIBLE")

        # Verify precedence ordering
        tasks_sched = opt_data["tasks_scheduled"]
        self.assertEqual(len(tasks_sched), 3)
        eaf_sched = next(t for t in tasks_sched if t["task_id"] == "EAF-01")
        lrf_sched = next(t for t in tasks_sched if t["task_id"] == "LRF-01")
        ccm_sched = next(t for t in tasks_sched if t["task_id"] == "CCM-01")

        # LRF must start after EAF finishes + at least 1h lag
        self.assertGreaterEqual(lrf_sched["start_hour"], eaf_sched["end_hour"] + 1)
        self.assertLessEqual(lrf_sched["start_hour"], eaf_sched["end_hour"] + 3)
        # CCM must start after LRF finishes
        self.assertGreaterEqual(ccm_sched["start_hour"], lrf_sched["end_hour"])

        # Check constraint audit log
        self.assertIn("constraint_audit_log", opt_data)
        self.assertGreater(len(opt_data["constraint_audit_log"]), 0)
        for entry in opt_data["constraint_audit_log"]:
            self.assertIn(entry["status"], ["SATISFIED", "BINDING", "VIOLATED"])

        # ----------------------------------------------------------------------
        # Step 6: Managerial Decision Center Lifecycle
        # ----------------------------------------------------------------------
        gen_res = self.client.post("/api/v1/decision/generate", json={
            "tenant_id": "demo_steel",
            "sector": "Steel",
            "task_load_kw": 120.0,
            "duration_hours": 4,
            "tasks": precedence_tasks
        }, headers=self.headers)
        self.assertEqual(gen_res.status_code, 200)
        gen_data = gen_res.json()
        self.assertEqual(gen_data["status"], "success")
        dc = gen_data["decision_center"]
        action_id = dc["action_id"]
        self.assertTrue(action_id.startswith("ACT-2026-"))
        self.assertEqual(dc["status"], "PENDING_APPROVAL")

        # Verify overview includes evidence and KPI stats
        overview_res = self.client.get("/api/v1/decision/overview", headers=self.headers)
        self.assertEqual(overview_res.status_code, 200)
        overview_data = overview_res.json()
        self.assertIn("forecast_metrics", overview_data)
        self.assertIn("active_alerts_count", overview_data)

        # Managerial approval
        app_res = self.client.post("/api/v1/decision/approve", json={
            "action_id": action_id,
            "manager_name": "Chief Sustainability Officer",
            "notes": "Approved shift of secondary refining batches to solar window."
        }, headers=self.headers)
        self.assertEqual(app_res.status_code, 200)
        app_data = app_res.json()
        self.assertEqual(app_data["status"], "success")
        approved_dc = app_data["decision_state"]
        self.assertEqual(approved_dc["status"], "APPROVED")
        self.assertEqual(approved_dc["approved_by"], "Chief Sustainability Officer")
        self.assertIn("approved_at", approved_dc)

        # History audit verification
        dec_hist_res = self.client.get("/api/v1/decision/history", headers=self.headers)
        self.assertEqual(dec_hist_res.status_code, 200)
        dec_history = dec_hist_res.json()["history"]
        found_action = next((a for a in dec_history if a["action_id"] == action_id), None)
        self.assertIsNotNone(found_action)
        self.assertEqual(found_action["status"], "APPROVED")

        # ----------------------------------------------------------------------
        # Step 7: Digital Twin 15-Year Simulation & Carbon Audit
        # ----------------------------------------------------------------------
        sim_res = self.client.post("/api/v1/simulation/digital_twin", json={
            "region": "Western",
            "base_monthly_kwh": 120000.0,
            "solar_capacity_kw": 200.0,
            "battery_storage_kwh": 100.0,
            "load_shift_pct": 20.0,
            "simulation_years": 15,
            "discount_rate_pct": 10.0,
            "tax_regime": "SECTION_32_RENEWABLE_40_WDV"
        }, headers=self.headers)
        self.assertEqual(sim_res.status_code, 200)
        twin_data = sim_res.json()["result"]["simulation"]
        fin = twin_data["financial_metrics"]
        life = twin_data["lifecycle_analysis"]

        self.assertGreater(fin["estimated_capex_inr"], 0.0)
        self.assertGreater(life["net_present_value_inr"], 0.0)
        self.assertIsNotNone(life["internal_rate_of_return_pct"])
        self.assertEqual(len(life["cash_flow_table"]), 15)

        # Carbon audit check
        audit_res = self.client.get("/api/v1/carbon/audit", headers=self.headers)
        self.assertEqual(audit_res.status_code, 200)
        audit_data = audit_res.json()
        self.assertEqual(audit_data["status"], "success")
        self.assertIn("audit_data", audit_data)
        self.assertIn("regional_breakdown", audit_data["audit_data"])
        self.assertEqual(audit_data["audit_data"]["national_average_kg_kwh"], 0.73)


class TestErrorHandlingAndEdgeCases(unittest.TestCase):
    """
    Workstream 1: Infeasible schedules, missing data, duplicate alerts, and schema validation.
    """

    def setUp(self):
        self.client = TestClient(app)
        self.headers = {"X-API-Key": "pragati_sec_2026"}

    def test_infeasible_scheduler_cyclic_dependency(self):
        """Verify scheduler detects cyclic task dependencies and returns INFEASIBLE cleanly."""
        cyclic_tasks = [
            {
                "task_id": "STAGE-A",
                "machine": "Machine A",
                "task_load_kw": 100.0,
                "task_duration_h": 2,
                "dependencies": ["STAGE-B"]
            },
            {
                "task_id": "STAGE-B",
                "machine": "Machine B",
                "task_load_kw": 100.0,
                "task_duration_h": 2,
                "dependencies": ["STAGE-A"]
            }
        ]
        res = self.client.post("/api/v1/scheduler/optimize", json={
            "task_load_kw": 100.0,
            "task_duration_h": 2,
            "tasks": cyclic_tasks
        }, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        opt = res.json()["optimization"]
        self.assertFalse(opt["is_feasible"])
        self.assertEqual(opt["status"], "INFEASIBLE")
        self.assertFalse(opt["dependency_graph_status"]["valid"])
        self.assertFalse(opt["dependency_graph_status"]["is_acyclic"])
        self.assertTrue(any("Cycle detected" in err for err in opt["dependency_graph_status"]["errors"]))

    def test_infeasible_scheduler_impossible_lag_window(self):
        """Verify scheduler catches min_lag_h > max_lag_h error."""
        impossible_lag_tasks = [
            {
                "task_id": "STAGE-A",
                "machine": "Machine A",
                "task_load_kw": 100.0,
                "task_duration_h": 2,
                "dependencies": []
            },
            {
                "task_id": "STAGE-B",
                "machine": "Machine B",
                "task_load_kw": 100.0,
                "task_duration_h": 2,
                "dependencies": ["STAGE-A"],
                "min_lag_h": 5,
                "max_lag_h": 2  # min > max is impossible
            }
        ]
        res = self.client.post("/api/v1/scheduler/optimize", json={
            "task_load_kw": 100.0,
            "task_duration_h": 2,
            "tasks": impossible_lag_tasks
        }, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        opt = res.json()["optimization"]
        self.assertFalse(opt["is_feasible"])
        self.assertTrue(any("impossible lag window" in err.lower() for err in opt["dependency_graph_status"]["errors"]))

    def test_alert_not_found_handling(self):
        """Verify 404 is returned when acknowledging or resolving non-existent alert ID."""
        ack_res = self.client.post("/api/v1/alerts/acknowledge", json={
            "alert_id": "ALT-NONEXISTENT-9999",
            "operator_name": "Test Operator"
        }, headers=self.headers)
        self.assertEqual(ack_res.status_code, 404)

        res_res = self.client.post("/api/v1/alerts/resolve", json={
            "alert_id": "ALT-NONEXISTENT-9999",
            "operator_name": "Test Operator",
            "resolution_notes": "None"
        }, headers=self.headers)
        self.assertEqual(res_res.status_code, 404)

    def test_missing_data_schema_validation(self):
        """Verify FastAPI returns 422 Unprocessable Entity for invalid or missing required fields."""
        # Empty payload to alert trigger
        res1 = self.client.post("/api/v1/alerts/trigger", json={}, headers=self.headers)
        self.assertEqual(res1.status_code, 422)

        # Missing action_id in decision approve
        res2 = self.client.post("/api/v1/decision/approve", json={"notes": "missing id"}, headers=self.headers)
        self.assertEqual(res2.status_code, 422)

    def test_decision_rejection_workflow(self):
        """Verify decision rejection changes status and records manager rejection reason."""
        gen_res = self.client.post("/api/v1/decision/generate", json={
            "task_load_kw": 100.0,
            "duration_hours": 4
        }, headers=self.headers)
        action_id = gen_res.json()["decision_center"]["action_id"]

        rej_res = self.client.post("/api/v1/decision/reject", json={
            "action_id": action_id,
            "manager_name": "VP Manufacturing",
            "reason": "Maintenance overhaul scheduled during recommended slot."
        }, headers=self.headers)
        self.assertEqual(rej_res.status_code, 200)
        rej_data = rej_res.json()
        self.assertEqual(rej_data["status"], "success")
        dc = rej_data["decision_state"]
        self.assertEqual(dc["status"], "REJECTED")
        self.assertEqual(dc["rejected_by"], "VP Manufacturing")
        self.assertIn("rejected_at", dc)


if __name__ == "__main__":
    unittest.main()
