import unittest
import sys
import os
from fastapi.testclient import TestClient

# Ensure backend folder is in path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import app
from engine.decision_engine import DecisionEngine, DECISION_ENGINE_INSTANCE

class TestDecisionCenter(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.headers = {"X-API-Key": "pragati-prod-secret-2026"}

    def test_decision_overview_endpoint(self):
        res = self.client.get("/api/v1/decision/overview", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("decision_center", data)
        self.assertIn("action_id", data["decision_center"])
        self.assertIn("evidence", data["decision_center"])
        self.assertIn("schedule_alternative", data["decision_center"])
        self.assertIn("constraints_verified", data["decision_center"])
        self.assertIn("forecast_metrics", data)
        self.assertIn("active_alerts_count", data)

    def test_decision_generate_endpoint(self):
        req_payload = {
            "tenant_id": "demo_steel",
            "sector": "Steel",
            "task_load_kw": 120.0,
            "duration_hours": 4
        }
        res = self.client.post("/api/v1/decision/generate", json=req_payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        dc = data["decision_center"]
        self.assertTrue(dc["action_id"].startswith("ACT-2026-"))
        self.assertEqual(dc["status"], "PENDING_APPROVAL")
        self.assertIn("evidence", dc)
        self.assertIn("anomaly_trigger", dc["evidence"])
        self.assertIn("projected_peak_kw", dc["evidence"])
        self.assertIn("schedule_alternative", dc)
        self.assertGreater(dc["schedule_alternative"]["cost_savings_per_batch_usd"], 0)
        self.assertIn("constraints_verified", dc)
        self.assertEqual(len(dc["constraints_verified"]), 4)
        self.assertIn("provenance", dc)

    def test_decision_approve_endpoint(self):
        # Generate fresh action first
        gen_res = self.client.post("/api/v1/decision/generate", json={"task_load_kw": 100.0, "duration_hours": 4}, headers=self.headers)
        action_id = gen_res.json()["decision_center"]["action_id"]

        approve_payload = {
            "action_id": action_id,
            "manager_name": "Chief Sustainability Officer",
            "notes": "Verified off-peak solar window shift; approved for production dispatch."
        }
        res = self.client.post("/api/v1/decision/approve", json=approve_payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["decision_state"]["status"], "APPROVED")
        self.assertEqual(data["decision_state"]["approved_by"], "Chief Sustainability Officer")
        self.assertIsNotNone(data["decision_state"]["approved_at"])

    def test_decision_reject_endpoint(self):
        gen_res = self.client.post("/api/v1/decision/generate", json={"task_load_kw": 100.0, "duration_hours": 4}, headers=self.headers)
        action_id = gen_res.json()["decision_center"]["action_id"]

        reject_payload = {
            "action_id": action_id,
            "manager_name": "Plant Superintendent",
            "reason": "Emergency maintenance scheduled on annealing bay during proposed slot."
        }
        res = self.client.post("/api/v1/decision/reject", json=reject_payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["decision_state"]["status"], "REJECTED")
        self.assertEqual(data["decision_state"]["rejected_by"], "Plant Superintendent")

    def test_decision_history_endpoint(self):
        res = self.client.get("/api/v1/decision/history", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("history", data)
        self.assertGreater(data["total_count"], 0)

if __name__ == "__main__":
    unittest.main()
