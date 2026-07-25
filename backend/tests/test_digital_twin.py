"""
Unit tests for DigitalTwinEngine, DigitalTwinAgent, and Carbon Audit APIs.
"""

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.digital_twin import DigitalTwinEngine, CEA_GRID_EMISSION_FACTORS
from agents.digital_twin_agent import DigitalTwinAgent

class TestDigitalTwin(unittest.TestCase):

    def test_digital_twin_engine_simulation(self):
        engine = DigitalTwinEngine(region="Western")
        results = engine.simulate_scenario(
            base_monthly_kwh=150000.0,
            solar_capacity_kw=250.0,
            battery_storage_kwh=100.0,
            load_shift_pct=20.0
        )
        self.assertEqual(results["region"], "Western")
        self.assertIn("financial_metrics", results)
        self.assertIn("carbon_metrics", results)
        self.assertGreater(results["financial_metrics"]["annual_savings_inr"], 0.0)
        self.assertGreater(results["carbon_metrics"]["annual_co2_reduction_tons"], 0.0)

    def test_cea_grid_emission_factors(self):
        engine = DigitalTwinEngine(region="Northern")
        audit_data = engine.get_grid_audit_data()
        self.assertEqual(audit_data["regional_breakdown"]["Northern"], 0.71)
        self.assertEqual(audit_data["regional_breakdown"]["Western"], 0.79)

    def test_digital_twin_agent_run(self):
        agent = DigitalTwinAgent()
        output = agent.run({
            "region": "Southern",
            "base_monthly_kwh": 200000.0,
            "solar_capacity_kw": 300.0,
            "battery_storage_kwh": 150.0,
            "load_shift_pct": 25.0
        })
        self.assertEqual(output["agent"], "DigitalTwinAgent")
        self.assertIn("xai_card", output)
        self.assertEqual(output["xai_card"]["agent_name"], "DigitalTwinAgent")
        self.assertTrue(output["xai_card"]["human_approval_required"])

if __name__ == "__main__":
    unittest.main()
