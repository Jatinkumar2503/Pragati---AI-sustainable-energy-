"""
PRAGATI AI — Phase 4: Digital Twin Financial Validation Test Suite
Tests for:
1. Financial model correctness (CapEx, O&M, degradation, replacements, residual value)
2. 10-15 year lifecycle cash flows, NPV, IRR, simple payback, after-tax breakeven
3. Battery degradation physics and feedback into dispatch / energy savings
4. Indian Income Tax Act regimes (NO_TAX_BENEFIT, SECTION_32_RENEWABLE_40_WDV, STANDARD_CORPORATE_15_WDV)
5. Multi-variable sensitivity analysis and Tornado drivers ranking
6. Edge cases: zero savings, zero capacity, negative NPV, undefined IRR
7. FastAPI endpoints and backward compatibility
"""

import unittest
import pytest
from fastapi.testclient import TestClient

from backend.engine.digital_twin import (
    DigitalTwinEngine,
    calculate_irr_safe,
    TAX_REGIMES,
    CEA_GRID_EMISSION_FACTORS
)
from backend.agents.digital_twin_agent import DigitalTwinAgent
from backend.api import app


class TestFinancialModelCorrectness(unittest.TestCase):
    """Priority 1: Validate CapEx, annual savings, O&M, replacement costs, and payback distinctions."""

    def setUp(self):
        self.engine = DigitalTwinEngine(region="Western")

    def test_capex_and_annual_savings_formulas(self):
        sim = self.engine.simulate_scenario(
            base_monthly_kwh=100000.0,
            solar_capacity_kw=200.0,
            battery_storage_kwh=100.0,
            load_shift_pct=20.0,
            simulation_years=15
        )
        fin = sim["financial_metrics"]

        # Solar: 200 kW * 45,000 = ₹90,00,000; BESS: 100 kWh * 18,000 = ₹18,00,000 -> Total ₹1,08,00,000
        expected_capex = (200.0 * 45000.0) + (100.0 * 18000.0)
        self.assertEqual(fin["estimated_capex_inr"], expected_capex)
        self.assertGreater(fin["annual_savings_inr"], 0.0)
        self.assertAlmostEqual(fin["annual_savings_inr"], fin["monthly_savings_inr"] * 12.0, places=2)

    def test_distinction_between_simple_payback_and_after_tax_breakeven(self):
        sim = self.engine.simulate_scenario(
            base_monthly_kwh=150000.0,
            solar_capacity_kw=250.0,
            battery_storage_kwh=100.0,
            load_shift_pct=20.0,
            tax_regime="SECTION_32_RENEWABLE_40_WDV"
        )
        fin = sim["financial_metrics"]
        simple_pb = fin["undiscounted_simple_payback_years"]
        after_tax_be = fin["after_tax_cashflow_breakeven_years"]

        self.assertIsNotNone(simple_pb)
        self.assertIsNotNone(after_tax_be)
        # Accelerated depreciation tax shield accelerates after-tax cash-flow breakeven
        self.assertLessEqual(after_tax_be, simple_pb)

    def test_inverter_and_battery_replacement_events(self):
        sim = self.engine.simulate_scenario(
            base_monthly_kwh=150000.0,
            solar_capacity_kw=250.0,
            battery_storage_kwh=100.0,
            load_shift_pct=20.0,
            inverter_replacement_year=8,
            bess_replacement_threshold_soh=80.0,
            simulation_years=15
        )
        table = sim["lifecycle_analysis"]["cash_flow_table"]
        
        # Check inverter replacement in Year 8
        yr8 = next(row for row in table if row["year"] == 8)
        self.assertGreater(yr8["inverter_replacement_cost_inr"], 0.0)
        expected_inv_cost = (250.0 * 45000.0) * 0.10
        self.assertEqual(yr8["inverter_replacement_cost_inr"], expected_inv_cost)

        # Check other non-replacement years have 0 inverter replacement
        yr1 = next(row for row in table if row["year"] == 1)
        self.assertEqual(yr1["inverter_replacement_cost_inr"], 0.0)


class TestLifecycleCashFlowAndNPV(unittest.TestCase):
    """Priority 2: 10-15 year lifecycle cash flows, discounting, and IRR."""

    def setUp(self):
        self.engine = DigitalTwinEngine(region="Western")

    def test_lifecycle_10_and_15_year_horizons(self):
        sim_10 = self.engine.simulate_scenario(
            base_monthly_kwh=150000.0,
            solar_capacity_kw=200.0,
            battery_storage_kwh=80.0,
            load_shift_pct=15.0,
            simulation_years=10
        )
        self.assertEqual(sim_10["lifecycle_analysis"]["simulation_horizon_years"], 10)
        self.assertEqual(len(sim_10["lifecycle_analysis"]["cash_flow_table"]), 10)

        sim_15 = self.engine.simulate_scenario(
            base_monthly_kwh=150000.0,
            solar_capacity_kw=200.0,
            battery_storage_kwh=80.0,
            load_shift_pct=15.0,
            simulation_years=15
        )
        self.assertEqual(sim_15["lifecycle_analysis"]["simulation_horizon_years"], 15)
        self.assertEqual(len(sim_15["lifecycle_analysis"]["cash_flow_table"]), 15)

    def test_cumulative_cashflow_trajectory_consistency(self):
        sim = self.engine.simulate_scenario(
            base_monthly_kwh=150000.0,
            solar_capacity_kw=200.0,
            battery_storage_kwh=100.0,
            load_shift_pct=20.0,
            simulation_years=12,
            discount_rate_pct=10.0
        )
        table = sim["lifecycle_analysis"]["cash_flow_table"]
        capex = sim["financial_metrics"]["estimated_capex_inr"]

        # Verify running cumulative cash flow matches sum of net cash flows
        running_cf = -capex
        for row in table:
            running_cf += row["net_cashflow_inr"]
            self.assertAlmostEqual(row["cumulative_cashflow_inr"], running_cf, delta=1.0)

        # Verify NPV equals final cumulative discounted cash flow
        final_dcf = table[-1]["cumulative_discounted_cashflow_inr"]
        self.assertAlmostEqual(sim["lifecycle_analysis"]["net_present_value_inr"], final_dcf, delta=1.0)

    def test_irr_safe_calculation_and_edge_cases(self):
        # 1. Normal project with positive returns
        cf_positive = [-100000.0, 30000.0, 30000.0, 30000.0, 30000.0, 30000.0]
        irr = calculate_irr_safe(cf_positive)
        self.assertIsNotNone(irr)
        self.assertGreater(irr, 10.0)

        # 2. Project with total inflows less than initial outlay -> None
        cf_insufficient = [-100000.0, 10000.0, 10000.0]
        self.assertIsNone(calculate_irr_safe(cf_insufficient))

        # 3. All negative outflows -> None
        cf_all_neg = [-50000.0, -5000.0, -5000.0]
        self.assertIsNone(calculate_irr_safe(cf_all_neg))

        # 4. Zero length or invalid starting outflow -> None
        self.assertIsNone(calculate_irr_safe([]))
        self.assertIsNone(calculate_irr_safe([1000.0, 2000.0]))


class TestBatteryDegradationPhysicsAndFeedback(unittest.TestCase):
    """Priority 3: Battery degradation physics and feedback directly into energy savings."""

    def setUp(self):
        self.engine = DigitalTwinEngine(region="Western")

    def test_degradation_directly_reduces_annual_battery_savings(self):
        sim = self.engine.simulate_scenario(
            base_monthly_kwh=200000.0,
            solar_capacity_kw=0.0,  # Isolate battery-only effects
            battery_storage_kwh=200.0,
            load_shift_pct=0.0,
            simulation_years=10,
            bess_replacement_threshold_soh=40.0  # Prevent replacement
        )
        table = sim["lifecycle_analysis"]["cash_flow_table"]

        # Battery capacity and shaved kWh should decrease from Year 1 to Year 10
        yr1 = table[0]
        yr10 = table[-1]
        self.assertGreater(yr1["battery_soh_pct"], yr10["battery_soh_pct"])
        self.assertGreater(yr1["battery_shaved_kwh"], yr10["battery_shaved_kwh"])

    def test_lfp_vs_nmc_chemistry_aging(self):
        lfp = self.engine.simulate_battery_degradation(
            battery_capacity_kwh=100.0,
            chemistry="LFP",
            operating_temp_c=35.0,
            simulation_years=10
        )
        nmc = self.engine.simulate_battery_degradation(
            battery_capacity_kwh=100.0,
            chemistry="NMC",
            operating_temp_c=35.0,
            simulation_years=10
        )
        # LFP should have higher retained SOH than NMC over 10 years
        final_lfp_soh = lfp["trajectory"][-1]["soh_pct"]
        final_nmc_soh = nmc["trajectory"][-1]["soh_pct"]
        self.assertGreater(final_lfp_soh, final_nmc_soh)

    def test_temperature_derating_acceleration(self):
        cool = self.engine.simulate_battery_degradation(
            battery_capacity_kwh=100.0,
            chemistry="LFP",
            operating_temp_c=25.0,
            simulation_years=8
        )
        hot = self.engine.simulate_battery_degradation(
            battery_capacity_kwh=100.0,
            chemistry="LFP",
            operating_temp_c=45.0,
            simulation_years=8
        )
        # High temperatures accelerate Arrhenius calendar degradation
        self.assertGreater(cool["trajectory"][-1]["soh_pct"], hot["trajectory"][-1]["soh_pct"])

    def test_calibration_status_and_disclosures_present(self):
        aging = self.engine.simulate_battery_degradation(battery_capacity_kwh=100.0)
        self.assertEqual(aging["calibration_status"], "SEMI_EMPIRICAL_MODEL")
        self.assertIn("BMS", aging["calibration_disclaimer"])


class TestIndianTaxRegimeValidation(unittest.TestCase):
    """Priority 4: Explicit, configurable Indian Income Tax Act regimes without false Section 32AD assumptions."""

    def setUp(self):
        self.engine = DigitalTwinEngine(region="Western")

    def test_tax_regimes_catalogue_contains_statutory_references(self):
        self.assertIn("NO_TAX_BENEFIT", TAX_REGIMES)
        self.assertIn("SECTION_32_RENEWABLE_40_WDV", TAX_REGIMES)
        self.assertIn("STANDARD_CORPORATE_15_WDV", TAX_REGIMES)

        sec32 = TAX_REGIMES["SECTION_32_RENEWABLE_40_WDV"]
        self.assertEqual(sec32["depreciation_rate_pct"], 40.0)
        self.assertIn("Section 32", sec32["statutory_reference"])
        self.assertIn("Section 115BAA", sec32["eligibility_disclosure"])

    def test_no_tax_benefit_regime_produces_zero_tax_shield(self):
        sim = self.engine.simulate_scenario(
            base_monthly_kwh=150000.0,
            solar_capacity_kw=250.0,
            battery_storage_kwh=100.0,
            load_shift_pct=20.0,
            tax_regime="NO_TAX_BENEFIT"
        )
        tax = sim["tax_regime_audit"]
        self.assertEqual(tax["selected_regime"], "NO_TAX_BENEFIT")
        self.assertEqual(tax["year1_tax_shield_inr"], 0.0)
        self.assertEqual(tax["total_lifecycle_tax_shield_inr"], 0.0)

    def test_section_32_renewable_produces_valid_shield(self):
        sim = self.engine.simulate_scenario(
            base_monthly_kwh=150000.0,
            solar_capacity_kw=250.0,
            battery_storage_kwh=100.0,
            load_shift_pct=20.0,
            tax_regime="SECTION_32_RENEWABLE_40_WDV"
        )
        tax = sim["tax_regime_audit"]
        capex = sim["financial_metrics"]["estimated_capex_inr"]
        expected_yr1_dep = capex * 0.40
        expected_yr1_shield = expected_yr1_dep * 0.2517
        self.assertAlmostEqual(tax["year1_depreciation_inr"], expected_yr1_dep, delta=1.0)
        self.assertAlmostEqual(tax["year1_tax_shield_inr"], expected_yr1_shield, delta=1.0)
        self.assertGreater(tax["total_lifecycle_tax_shield_inr"], tax["year1_tax_shield_inr"])

    def test_tax_shield_increases_npv_compared_to_no_tax_benefit(self):
        sim_no_tax = self.engine.simulate_scenario(
            base_monthly_kwh=150000.0,
            solar_capacity_kw=250.0,
            battery_storage_kwh=100.0,
            load_shift_pct=20.0,
            tax_regime="NO_TAX_BENEFIT"
        )
        sim_sec32 = self.engine.simulate_scenario(
            base_monthly_kwh=150000.0,
            solar_capacity_kw=250.0,
            battery_storage_kwh=100.0,
            load_shift_pct=20.0,
            tax_regime="SECTION_32_RENEWABLE_40_WDV"
        )
        npv_no_tax = sim_no_tax["lifecycle_analysis"]["net_present_value_inr"]
        npv_sec32 = sim_sec32["lifecycle_analysis"]["net_present_value_inr"]
        self.assertGreater(npv_sec32, npv_no_tax)


class TestSensitivityAndTornadoAnalysis(unittest.TestCase):
    """Priority 5: Multi-variable sensitivity and Tornado Drivers ranking."""

    def setUp(self):
        self.engine = DigitalTwinEngine(region="Western")

    def test_tornado_drivers_ranked_by_swing(self):
        sim = self.engine.simulate_scenario(
            base_monthly_kwh=150000.0,
            solar_capacity_kw=250.0,
            battery_storage_kwh=100.0,
            load_shift_pct=20.0
        )
        tornado = sim["sensitivity_tornado"]
        drivers = tornado["tornado_drivers"]

        self.assertGreater(len(drivers), 3)
        # Check sorted descending by NPV swing
        for i in range(1, len(drivers)):
            self.assertGreaterEqual(drivers[i - 1]["npv_swing_inr"], drivers[i]["npv_swing_inr"])
            self.assertEqual(drivers[i]["rank"], i + 1)

    def test_scenario_comparison_best_base_worst(self):
        sim = self.engine.simulate_scenario(
            base_monthly_kwh=150000.0,
            solar_capacity_kw=250.0,
            battery_storage_kwh=100.0,
            load_shift_pct=20.0
        )
        scenarios = sim["sensitivity_tornado"]["scenario_comparison"]
        base_npv = scenarios["base_case"]["npv_inr"]
        best_npv = scenarios["best_case"]["npv_inr"]
        worst_npv = scenarios["worst_case"]["npv_inr"]

        self.assertGreater(best_npv, base_npv)
        self.assertLess(worst_npv, base_npv)

    def test_zero_capacity_edge_case(self):
        sim = self.engine.simulate_scenario(
            base_monthly_kwh=150000.0,
            solar_capacity_kw=0.0,
            battery_storage_kwh=0.0,
            load_shift_pct=0.0
        )
        fin = sim["financial_metrics"]
        self.assertEqual(fin["estimated_capex_inr"], 0.0)
        self.assertEqual(fin["net_present_value_inr"], 0.0)
        self.assertIsNone(fin["internal_rate_of_return_pct"])


class TestFastAPIDigitalTwinEndpoints(unittest.TestCase):
    """Priority 6 & 7: API endpoints exposure, schema validation, and backward compatibility."""

    def setUp(self):
        self.client = TestClient(app)

    def test_api_tax_regimes_endpoint(self):
        res = self.client.get("/api/v1/simulation/tax_regimes")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("tax_regimes", data)
        self.assertIn("SECTION_32_RENEWABLE_40_WDV", data["tax_regimes"])

    def test_api_post_digital_twin_with_custom_tax_regime(self):
        payload = {
            "region": "Western",
            "base_monthly_kwh": 150000.0,
            "solar_capacity_kw": 250.0,
            "battery_storage_kwh": 100.0,
            "load_shift_pct": 20.0,
            "simulation_years": 15,
            "discount_rate_pct": 10.0,
            "tax_regime": "NO_TAX_BENEFIT"
        }
        res = self.client.post("/api/v1/simulation/digital_twin", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        sim = data["result"]["simulation"]

        # Check Phase 4 structures
        self.assertIn("lifecycle_analysis", sim)
        self.assertIn("sensitivity_tornado", sim)
        self.assertIn("tax_regime_audit", sim)
        self.assertEqual(sim["tax_regime_audit"]["selected_regime"], "NO_TAX_BENEFIT")
        self.assertIn("disclaimers", sim)
        self.assertEqual(sim["disclaimers"]["nature_of_results"], "MODELED_ESTIMATES")

    def test_legacy_simulate_alias_endpoint(self):
        payload = {
            "solar_capacity_kw": 200.0,
            "battery_capacity_kwh": 80.0,
            "load_shift_pct": 15.0
        }
        res = self.client.post("/simulate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("annual_solar_generation_kwh", data)
        self.assertIn("net_present_value_dollars", data)
        self.assertIn("yearly_cash_flows", data)
        self.assertIn("undiscounted_simple_payback_years", data)

    def test_digital_twin_agent_xai_card_generation(self):
        agent = DigitalTwinAgent()
        out = agent.run({
            "solar_capacity_kw": 200.0,
            "battery_storage_kwh": 80.0,
            "simulation_years": 15,
            "tax_regime": "SECTION_32_RENEWABLE_40_WDV"
        })
        self.assertEqual(out["agent"], "DigitalTwinAgent")
        self.assertIn("NPV", out["xai_card"]["reasoning_why"])
        self.assertIn("breakeven", out["xai_card"]["reasoning_why"])


if __name__ == "__main__":
    unittest.main()
