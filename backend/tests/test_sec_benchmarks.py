import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.workspace_manager import (
    calculate_sec_compliance,
    calculate_iso_50001_enpi,
    list_workspaces,
    get_current_workspace,
    switch_workspace,
    BEE_PAT_SECTOR_NORMS
)
from engine.document_parser import (
    calculate_apfc_sizing,
    parse_electricity_bill,
    DISCOM_TARIFF_SCHEDULES
)
from engine.digital_twin import (
    DigitalTwinEngine,
    CEA_GRID_EMISSION_FACTORS,
    STATE_GRID_FACTORS
)
from engine.rag_engine import RAGEngine

class TestSectoralEnergyAndAnalytics(unittest.TestCase):

    def test_bee_pat_steel_compliance(self):
        """Test BEE PAT Cycle-VII SEC calculation for Steel Sector."""
        eval_res = calculate_sec_compliance(
            workspace_id="indian_steel",
            annual_production_tons=65000.0,
            annual_electrical_kwh=38500000.0,
            annual_thermal_toe=0.0
        )
        self.assertEqual(eval_res["sector"], "Steel")
        self.assertEqual(eval_res["sec_unit"], "TOE/ton crude steel")
        self.assertAlmostEqual(eval_res["baseline_sec"], 0.635, places=3)
        self.assertAlmostEqual(eval_res["target_sec"], 0.585, places=3)
        self.assertIn("sec_reduction_achieved_pct", eval_res)
        self.assertTrue(eval_res["is_compliant"])
        self.assertGreaterEqual(eval_res["escerts_generated"], 0.0)

    def test_bee_pat_cement_compliance(self):
        """Test BEE PAT Cycle-VII SEC calculation for Cement Sector."""
        eval_res = calculate_sec_compliance(
            workspace_id="indian_cement",
            annual_production_tons=850000.0,
            annual_electrical_kwh=65000000.0
        )
        self.assertEqual(eval_res["sector"], "Cement")
        self.assertEqual(eval_res["sec_unit"], "kWh/ton cement")
        self.assertAlmostEqual(eval_res["baseline_sec"], 76.2, places=1)
        self.assertAlmostEqual(eval_res["target_sec"], 68.5, places=1)

    def test_bee_pat_textile_compliance(self):
        """Test BEE PAT Cycle-VII SEC calculation for Textile Sector."""
        eval_res = calculate_sec_compliance(
            workspace_id="indian_textile",
            annual_production_tons=12000.0,
            annual_electrical_kwh=9800000.0
        )
        self.assertEqual(eval_res["sector"], "Textile")
        self.assertEqual(eval_res["sec_unit"], "MJ/kg fabric")
        self.assertAlmostEqual(eval_res["baseline_sec"], 16.8, places=1)

    def test_iso_50001_enpi(self):
        """Test ISO 50001:2018 Energy Performance Indicator baselining."""
        enpi = calculate_iso_50001_enpi(
            baseline_kwh=1000000.0,
            actual_kwh=920000.0,
            heating_degree_days=50.0,
            cooling_degree_days=120.0
        )
        self.assertIn("enpi_improvement_pct", enpi)
        self.assertGreater(enpi["net_energy_savings_kwh"], 0.0)
        self.assertEqual(enpi["iso_conformance"], "Conforming")

    def test_apfc_capacitor_sizing(self):
        """Test APFC reactive power sizing and payback calculations."""
        sizing = calculate_apfc_sizing(
            active_power_kw=1000.0,
            current_pf=0.82,
            target_pf=0.99,
            tariff_inr_kwh=8.50
        )
        self.assertGreater(sizing["exact_kvar_required"], 0.0)
        self.assertGreaterEqual(sizing["recommended_apfc_kvar"], sizing["exact_kvar_required"])
        self.assertIn("financial_analysis", sizing)
        self.assertGreater(sizing["financial_analysis"]["annual_savings_inr"], 0.0)

    def test_discom_bill_parser(self):
        """Test multi-DISCOM utility bill parser with tariff schedules."""
        res = parse_electricity_bill(
            file_bytes=b"sample_mock_bill_bytes",
            filename="steel_plant_may_2026.pdf",
            discom="MSEDCL"
        )
        self.assertEqual(res["status"], "success")
        self.assertIn("extracted_data", res)
        self.assertIn("total_bill_inr", res["extracted_data"])
        self.assertIn("apfc_recommendation", res)

    def test_digital_twin_battery_degradation(self):
        """Test Arrhenius LFP and NMC battery capacity degradation physics."""
        twin = DigitalTwinEngine(region="Western")
        lfp_aging = twin.simulate_battery_degradation(
            battery_capacity_kwh=500.0,
            chemistry="LFP",
            daily_cycles=1.0,
            depth_of_discharge=0.80,
            simulation_years=10
        )
        self.assertEqual(len(lfp_aging["trajectory"]), 10)
        self.assertEqual(lfp_aging["chemistry"], "LFP")
        # Ensure SOH decreases monotonically over time
        for i in range(1, len(lfp_aging["trajectory"])):
            self.assertLessEqual(
                lfp_aging["trajectory"][i]["soh_pct"],
                lfp_aging["trajectory"][i - 1]["soh_pct"]
            )

    def test_digital_twin_scenario_physics(self):
        """Test Digital Twin scenario simulation with temperature derating."""
        twin = DigitalTwinEngine(region="Western")
        scenario = twin.simulate_scenario(
            base_monthly_kwh=500000.0,
            solar_capacity_kw=500.0,
            battery_storage_kwh=200.0,
            load_shift_pct=15.0,
            ambient_temp_c=38.0
        )
        self.assertIn("energy_metrics", scenario)
        self.assertIn("financial_metrics", scenario)
        self.assertIn("carbon_metrics", scenario)
        self.assertIn("battery_lifecycle", scenario)
        self.assertGreater(scenario["financial_metrics"]["annual_savings_inr"], 0.0)

    def test_rag_engine_search(self):
        """Test semantic and keyword search across regulatory norms."""
        rag = RAGEngine()
        results = rag.search_rules(query="Specific Energy Consumption steel", category="Steel")
        self.assertGreater(len(results), 0)
        self.assertIn("BEE PAT", results[0]["title"])

if __name__ == "__main__":
    unittest.main()
