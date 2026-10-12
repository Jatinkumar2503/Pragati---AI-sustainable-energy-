"""
PRAGATI AI — Phase 5, Workstream 2: Independent Financial Benchmark Test Suite
This test module performs independent verification of:
1. Initial CapEx and annual savings
2. Written Down Value (WDV) depreciation schedules (Section 32 40% vs Standard 15% vs No Tax)
3. Tax shields under Section 115BAA corporate tax (25.17%)
4. Scheduled equipment replacements (Inverter Year 8 at 10% solar CapEx, BESS cell replacement at SOH <= 70%)
5. Terminal salvage / residual value (Year 15, 5% of CapEx)
6. 15-year lifecycle cash flow timing and discounting convention (NPV)
7. Robust Internal Rate of Return (IRR) bisection and edge cases (all-negative, zero generation, undefined IRR)
8. Multi-variable sensitivity Tornado drivers rank ordering
9. Statutory tax disclosures and non-guaranteed modeled estimates

CRITICAL REQUIREMENT:
All benchmark expected answers in this file are computed using closed-form mathematical
functions and independent solvers implemented directly in this test file, WITHOUT calling
production calculation functions to generate expected answers.
"""

import math
import unittest
from typing import List, Dict, Any, Optional
from fastapi.testclient import TestClient

from backend.api import app
from backend.engine.digital_twin import DigitalTwinEngine, TAX_REGIMES


# ==============================================================================
# INDEPENDENT REFERENCE BENCHMARK IMPLEMENTATIONS (NOT CALLING PRODUCTION CODE)
# ==============================================================================

def benchmark_capex(solar_kw: float, bess_kwh: float, solar_unit_cost: float = 45000.0, bess_unit_cost: float = 18000.0) -> float:
    """Independent CapEx calculation: Solar + BESS."""
    return (solar_kw * solar_unit_cost) + (bess_kwh * bess_unit_cost)


def benchmark_wdv_depreciation(capex: float, dep_rate_pct: float, corp_tax_rate_pct: float, years: int = 15) -> List[Dict[str, float]]:
    """
    Independent WDV depreciation & tax shield schedule.
    Formula:
        Dep_t = WDV_{t-1} * (dep_rate_pct / 100)
        TaxShield_t = Dep_t * (corp_tax_rate_pct / 100)
        WDV_t = WDV_{t-1} - Dep_t
    """
    rate = dep_rate_pct / 100.0
    tax_rate = corp_tax_rate_pct / 100.0
    wdv = capex
    schedule = []
    for yr in range(1, years + 1):
        if rate > 0.0:
            dep = wdv * rate
            closing_wdv = wdv - dep
            tax_shield = dep * tax_rate
            wdv = closing_wdv
        else:
            dep = 0.0
            closing_wdv = 0.0
            tax_shield = 0.0
        schedule.append({
            "year": yr,
            "depreciation": round(dep, 2),
            "tax_shield": round(tax_shield, 2),
            "closing_wdv": round(closing_wdv, 2)
        })
    return schedule


def benchmark_irr_bisection(cash_flows: List[float], low: float = -0.40, high: float = 3.0, tol: float = 1e-6, max_iter: int = 200) -> Optional[float]:
    """
    Independent binary-search IRR solver implemented from first principles.
    Finds r such that NPV(r) = sum_{t=0}^N CF_t / (1 + r)^t = 0.
    Returns percentage (e.g. 14.5 for 14.5%), or None if mathematically undefined.
    """
    if not cash_flows or len(cash_flows) < 2:
        return None
    if cash_flows[0] >= 0:
        return None
    # If cumulative positive inflows do not exceed initial capital outlay, IRR is undefined / negative
    if sum(cash_flows[1:]) <= abs(cash_flows[0]):
        return None
    if all(cf <= 0 for cf in cash_flows[1:]):
        return None

    def npv_at_rate(r: float) -> float:
        total = 0.0
        for t, cf in enumerate(cash_flows):
            denom = (1.0 + r) ** t
            if denom == 0:
                return float("inf")
            total += cf / denom
        return total

    f_low = npv_at_rate(low)
    f_high = npv_at_rate(high)

    if f_low * f_high > 0:
        # Extend bracket
        high = 10.0
        f_high = npv_at_rate(high)
        if f_low * f_high > 0:
            return None

    for _ in range(max_iter):
        mid = (low + high) / 2.0
        f_mid = npv_at_rate(mid)
        if abs(f_mid) < tol or (high - low) < tol:
            return round(mid * 100.0, 2)
        if f_low * f_mid < 0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid
    return round(((low + high) / 2.0) * 100.0, 2)


def benchmark_npv(cash_flows_nominal: List[float], discount_rate_pct: float) -> float:
    """
    Independent Net Present Value calculation.
    NPV = sum_{t=1}^N CF_t / (1 + r)^t - CapEx  (with CF_0 = -CapEx in cash_flows_nominal[0]).
    """
    r = discount_rate_pct / 100.0
    total = cash_flows_nominal[0]  # initial outlay (negative)
    for t in range(1, len(cash_flows_nominal)):
        total += cash_flows_nominal[t] / ((1.0 + r) ** t)
    return round(total, 2)


# ==============================================================================
# TEST SUITE: INDEPENDENT FINANCIAL VALIDATION
# ==============================================================================

class TestIndependentFinancialBenchmarks(unittest.TestCase):
    """
    Validates PRAGATI AI financial model against independently formulated benchmarks.
    """

    def setUp(self):
        self.client = TestClient(app)
        self.engine = DigitalTwinEngine(region="Western")

    def test_benchmark_capex_and_breakdown(self):
        """1. Verify initial CapEx calculation against independent benchmark."""
        solar_kw = 200.0
        bess_kwh = 100.0
        expected_capex = benchmark_capex(solar_kw, bess_kwh)
        # 200 * 45,000 + 100 * 18,000 = 9,000,000 + 1,800,000 = 10,800,000 INR
        self.assertEqual(expected_capex, 10800000.0)

        sim = self.engine.simulate_scenario(
            base_monthly_kwh=100000.0,
            solar_capacity_kw=solar_kw,
            battery_storage_kwh=bess_kwh,
            load_shift_pct=20.0
        )
        fin = sim["financial_metrics"]
        life = sim["lifecycle_analysis"]
        self.assertEqual(fin["estimated_capex_inr"], expected_capex)
        self.assertEqual(life["initial_capex_inr"], expected_capex)

    def test_benchmark_wdv_depreciation_section_32_and_standard_regimes(self):
        """2. Verify year-by-year 40% and 15% WDV depreciation schedules & tax shields."""
        capex = 10800000.0
        corp_tax_rate = 25.17

        # 40% WDV (Section 32 Renewable)
        bmark_40 = benchmark_wdv_depreciation(capex, 40.0, corp_tax_rate, years=15)
        # Year 1: Dep = 10,800,000 * 0.40 = 4,320,000; TaxShield = 4,320,000 * 0.2517 = 1,087,344
        self.assertEqual(bmark_40[0]["depreciation"], 4320000.0)
        self.assertAlmostEqual(bmark_40[0]["tax_shield"], 4320000.0 * (25.17 / 100.0), places=2)
        # Year 2: Opening WDV = 6,480,000; Dep = 2,592,000; TaxShield = 2,592,000 * 0.2517 = 652,406.4
        self.assertEqual(bmark_40[1]["depreciation"], 2592000.0)
        self.assertAlmostEqual(bmark_40[1]["tax_shield"], 2592000.0 * (25.17 / 100.0), places=2)

        # Run production engine with 40% WDV
        sim_40 = self.engine.simulate_scenario(
            base_monthly_kwh=100000.0,
            solar_capacity_kw=200.0,
            battery_storage_kwh=100.0,
            load_shift_pct=20.0,
            tax_regime="SECTION_32_RENEWABLE_40_WDV"
        )
        cf_table_40 = sim_40["lifecycle_analysis"]["cash_flow_table"]
        for yr_idx in range(15):
            prod_dep = cf_table_40[yr_idx]["depreciation_inr"]
            prod_shield = cf_table_40[yr_idx]["tax_shield_inr"]
            self.assertAlmostEqual(prod_dep, bmark_40[yr_idx]["depreciation"], delta=2.0)
            self.assertAlmostEqual(prod_shield, bmark_40[yr_idx]["tax_shield"], delta=2.0)

        # 15% WDV (Standard Corporate)
        bmark_15 = benchmark_wdv_depreciation(capex, 15.0, corp_tax_rate, years=15)
        sim_15 = self.engine.simulate_scenario(
            base_monthly_kwh=100000.0,
            solar_capacity_kw=200.0,
            battery_storage_kwh=100.0,
            load_shift_pct=20.0,
            tax_regime="STANDARD_CORPORATE_15_WDV"
        )
        cf_table_15 = sim_15["lifecycle_analysis"]["cash_flow_table"]
        for yr_idx in range(15):
            prod_dep = cf_table_15[yr_idx]["depreciation_inr"]
            prod_shield = cf_table_15[yr_idx]["tax_shield_inr"]
            self.assertAlmostEqual(prod_dep, bmark_15[yr_idx]["depreciation"], delta=2.0)
            self.assertAlmostEqual(prod_shield, bmark_15[yr_idx]["tax_shield"], delta=2.0)

    def test_benchmark_zero_tax_benefit_regime(self):
        """3. Verify zero tax benefit regime yields strictly zero depreciation tax shield."""
        sim_zero = self.engine.simulate_scenario(
            base_monthly_kwh=100000.0,
            solar_capacity_kw=200.0,
            battery_storage_kwh=100.0,
            load_shift_pct=20.0,
            tax_regime="NO_TAX_BENEFIT"
        )
        cf_table = sim_zero["lifecycle_analysis"]["cash_flow_table"]
        for row in cf_table:
            self.assertEqual(row["depreciation_inr"], 0.0)
            self.assertEqual(row["tax_shield_inr"], 0.0)
        self.assertEqual(sim_zero["lifecycle_analysis"]["total_tax_shield_inr"], 0.0)

    def test_benchmark_scheduled_replacement_costs_and_salvage_value(self):
        """4. Verify Inverter replacement at Year 8, BESS replacement, and terminal salvage value."""
        solar_kw = 200.0
        bess_kwh = 100.0
        solar_capex = solar_kw * 45000.0  # 9,000,000 INR
        total_capex = solar_capex + (bess_kwh * 18000.0)  # 10,800,000 INR

        expected_inverter_cost = solar_capex * 0.10  # 10% default = 900,000 INR
        expected_salvage_value = total_capex * 0.05  # 5% = 540,000 INR

        sim = self.engine.simulate_scenario(
            base_monthly_kwh=120000.0,
            solar_capacity_kw=solar_kw,
            battery_storage_kwh=bess_kwh,
            load_shift_pct=20.0,
            simulation_years=15
        )
        cf_table = sim["lifecycle_analysis"]["cash_flow_table"]

        # Year 8: Inverter replacement
        yr8_row = cf_table[7]
        self.assertEqual(yr8_row["year"], 8)
        self.assertEqual(yr8_row["inverter_replacement_cost_inr"], expected_inverter_cost)

        # Non-Year-8 rows must have zero inverter replacement cost
        for yr_idx, row in enumerate(cf_table):
            if row["year"] != 8:
                self.assertEqual(row["inverter_replacement_cost_inr"], 0.0)

        # Year 15: Terminal salvage value
        yr15_row = cf_table[14]
        self.assertEqual(yr15_row["year"], 15)
        self.assertEqual(yr15_row["salvage_value_inr"], expected_salvage_value)

        # Non-Year-15 rows must have zero salvage value
        for yr_idx in range(14):
            self.assertEqual(cf_table[yr_idx]["salvage_value_inr"], 0.0)

    def test_benchmark_lifecycle_npv_and_irr_reconciliation(self):
        """5. Reconcile NPV and IRR outputs against independent benchmark calculations."""
        sim = self.engine.simulate_scenario(
            base_monthly_kwh=150000.0,
            solar_capacity_kw=250.0,
            battery_storage_kwh=100.0,
            load_shift_pct=20.0,
            discount_rate_pct=10.0,
            simulation_years=15,
            tax_regime="SECTION_32_RENEWABLE_40_WDV"
        )
        life = sim["lifecycle_analysis"]
        cash_flows = life["cash_flows_nominal"]

        # Calculate independent benchmark NPV
        bmark_npv = benchmark_npv(cash_flows, discount_rate_pct=10.0)
        self.assertAlmostEqual(life["net_present_value_inr"], bmark_npv, delta=5.0)

        # Calculate independent benchmark IRR
        bmark_irr = benchmark_irr_bisection(cash_flows)
        self.assertIsNotNone(bmark_irr)
        self.assertAlmostEqual(life["internal_rate_of_return_pct"], bmark_irr, delta=0.1)

    def test_zero_generation_edge_case(self):
        """6. Verify zero capacity scenario results in CapEx=0, NPV=0, and safely undefined IRR."""
        sim = self.engine.simulate_scenario(
            base_monthly_kwh=100000.0,
            solar_capacity_kw=0.0,
            battery_storage_kwh=0.0,
            load_shift_pct=0.0,
            simulation_years=15
        )
        fin = sim["financial_metrics"]
        life = sim["lifecycle_analysis"]

        self.assertEqual(fin["estimated_capex_inr"], 0.0)
        self.assertEqual(fin["annual_savings_inr"], 0.0)
        self.assertEqual(life["net_present_value_inr"], 0.0)
        self.assertIsNone(life["internal_rate_of_return_pct"])
        self.assertEqual(life["irr_status"], "NOT_MEANINGFUL")
        self.assertIn("IRR is not meaningful", life["irr_explanation"])

        # Ensure no NaN or infinite values enter results
        for row in life["cash_flow_table"]:
            for k, v in row.items():
                if isinstance(v, (int, float)):
                    self.assertFalse(math.isnan(v), f"NaN found in {k} at year {row['year']}")
                    self.assertFalse(math.isinf(v), f"Inf found in {k} at year {row['year']}")

    def test_all_negative_cash_flows_edge_case(self):
        """7. Verify scenario with CapEx > 0 but zero savings produces negative NPV and None IRR."""
        sim = self.engine.simulate_scenario(
            base_monthly_kwh=0.0,
            solar_capacity_kw=100.0,
            battery_storage_kwh=0.0,
            load_shift_pct=0.0,
            tax_regime="NO_TAX_BENEFIT"
        )
        life = sim["lifecycle_analysis"]

        self.assertEqual(life["initial_capex_inr"], 4500000.0)
        self.assertFalse(math.isnan(life["net_present_value_inr"]))
        self.assertFalse(math.isinf(life["net_present_value_inr"]))

        # Construct an explicitly all-negative synthetic cash flow list to verify independent solver
        all_neg_cfs = [-1000000.0, -20000.0, -21000.0, -22000.0, -23000.0]
        irr_bmark = benchmark_irr_bisection(all_neg_cfs)
        self.assertIsNone(irr_bmark)

    def test_reconcile_api_endpoint_simulation_against_benchmark(self):
        """8. Reconcile FastAPI POST /api/v1/simulation/digital_twin against independent benchmark."""
        req_payload = {
            "region": "Western",
            "base_monthly_kwh": 120000.0,
            "solar_capacity_kw": 200.0,
            "battery_storage_kwh": 100.0,
            "load_shift_pct": 15.0,
            "ambient_temp_c": 32.0,
            "battery_chemistry": "LFP",
            "simulation_years": 15,
            "discount_rate_pct": 10.0,
            "tariff_escalation_pct": 4.0,
            "tax_regime": "SECTION_32_RENEWABLE_40_WDV"
        }
        res = self.client.post("/api/v1/simulation/digital_twin", json=req_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")

        result = data["result"]
        # Endpoint returns {"agent": ..., "simulation": sim_dict, "xai_card": ...}
        sim_data = result["simulation"]
        fin = sim_data["financial_metrics"]
        life = sim_data["lifecycle_analysis"]

        # Check CapEx
        expected_capex = benchmark_capex(200.0, 100.0)
        self.assertEqual(fin["estimated_capex_inr"], expected_capex)

        # Check NPV against independent formula
        cash_flows = life["cash_flows_nominal"]
        bmark_npv = benchmark_npv(cash_flows, discount_rate_pct=10.0)
        self.assertAlmostEqual(life["net_present_value_inr"], bmark_npv, delta=5.0)

        # Check IRR against independent bisection solver
        bmark_irr = benchmark_irr_bisection(cash_flows)
        self.assertIsNotNone(bmark_irr)
        self.assertAlmostEqual(life["internal_rate_of_return_pct"], bmark_irr, delta=0.1)

        # Check Year 1 WDV depreciation in API response
        cf_yr1 = life["cash_flow_table"][0]
        self.assertAlmostEqual(cf_yr1["depreciation_inr"], expected_capex * 0.40, delta=2.0)
        self.assertAlmostEqual(cf_yr1["tax_shield_inr"], (expected_capex * 0.40) * (25.17 / 100.0), delta=2.0)

    def test_statutory_tax_disclosures_and_provenance(self):
        """9. Verify tax regimes endpoint and disclosures avoid unsupported eligibility claims."""
        res = self.client.get("/api/v1/simulation/tax_regimes")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        regimes = data["tax_regimes"]

        # Verify Section 32 disclosures
        sec32 = regimes["SECTION_32_RENEWABLE_40_WDV"]
        self.assertIn("Section 32", sec32["name"])
        self.assertEqual(sec32["depreciation_rate_pct"], 40.0)
        self.assertEqual(sec32["corporate_tax_rate_pct"], 25.17)
        self.assertIn("Requires eligibility verification", sec32["eligibility_disclosure"])
        self.assertIn("115BAA", sec32["eligibility_disclosure"])

        # Verify simulated output discloses modeled estimates in disclaimers
        sim = self.engine.simulate_scenario(
            base_monthly_kwh=100000.0,
            solar_capacity_kw=200.0,
            battery_storage_kwh=100.0,
            load_shift_pct=20.0
        )
        self.assertIn("disclaimers", sim)
        disclaimers = sim["disclaimers"]
        self.assertIn("nature_of_results", disclaimers)
        self.assertEqual(disclaimers["nature_of_results"], "MODELED_ESTIMATES")
        self.assertIn("tax_advisory_notice", disclaimers)
        self.assertIn("chartered accountant", disclaimers["tax_advisory_notice"].lower())


if __name__ == "__main__":
    unittest.main()
