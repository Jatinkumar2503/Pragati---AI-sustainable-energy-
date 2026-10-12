"""
PRAGATI AI — Digital Twin Scenario Simulation, Battery Degradation Physics & Lifecycle Financial Validation Engine
Provides physical modeling for Solar PV with temperature derating, LFP/NMC BESS Arrhenius battery aging,
Load Shifting, CEA Grid Emission Factors, 10-15 Year Lifecycle Cash Flows, NPV, IRR, Simple Payback,
After-Tax Cash-Flow Breakeven, Multi-Variable Sensitivity Tornado Analysis, and Configurable Indian Tax Regimes.
"""

import math
from typing import Dict, Any, List, Optional, Tuple

# Central Electricity Authority (CEA) CO2 Baseline Database for Indian Power Sector (kg CO2/kWh)
CEA_GRID_EMISSION_FACTORS = {
    "Northern": 0.71,
    "Western": 0.79,
    "Southern": 0.68,
    "Eastern": 0.85,
    "North-Eastern": 0.62,
    "National Average": 0.73
}

# State-level Grid Emission Intensities (kg CO2/kWh)
STATE_GRID_FACTORS = {
    "Maharashtra": 0.82,
    "Gujarat": 0.81,
    "Karnataka": 0.64,
    "Tamil Nadu": 0.67,
    "Telangana": 0.76,
    "Odisha": 0.91,
    "West Bengal": 0.88,
    "Rajasthan": 0.78
}

# Indian Corporate Tax & Depreciation Regimes under Income Tax Act 1961
# Note: Section 32AD was a historical 15% investment allowance in backward areas;
# Renewable depreciation is governed by Section 32 (Rule 5, Appendix I).
TAX_REGIMES = {
    "NO_TAX_BENEFIT": {
        "regime_key": "NO_TAX_BENEFIT",
        "name": "No Tax Benefit (Conservative Baseline)",
        "description": "Zero depreciation tax shield claimed. Baseline scenario without corporate tax deduction assumptions.",
        "depreciation_rate_pct": 0.0,
        "corporate_tax_rate_pct": 0.0,
        "eligibility_disclosure": "No eligibility conditions required. Baseline transparent evaluation.",
        "statutory_reference": "N/A — Pre-tax operational cash flows only"
    },
    "SECTION_32_RENEWABLE_40_WDV": {
        "regime_key": "SECTION_32_RENEWABLE_40_WDV",
        "name": "Income Tax Act Section 32 (Renewable Energy 40% WDV)",
        "description": "Accelerated Written Down Value depreciation (40% p.a.) applicable to renewable energy devices / solar plant under Section 32, Rule 5, Appendix I.",
        "depreciation_rate_pct": 40.0,
        "corporate_tax_rate_pct": 25.17,  # Section 115BAA concessional rate (22% + 10% surcharge + 4% cess)
        "eligibility_disclosure": "Requires eligibility verification under applicable corporate tax regime (concessional Section 115BAA vs standard regime) and asset commissioning compliance under Indian Income Tax Act 1961.",
        "statutory_reference": "Income Tax Act 1961, Section 32(1) read with Rule 5 & Appendix I (Part A, III(8)(ix))"
    },
    "STANDARD_CORPORATE_15_WDV": {
        "regime_key": "STANDARD_CORPORATE_15_WDV",
        "name": "Income Tax Act Section 32 (General Plant & Machinery 15% WDV)",
        "description": "Standard Written Down Value depreciation (15% p.a.) for general industrial plant and machinery.",
        "depreciation_rate_pct": 15.0,
        "corporate_tax_rate_pct": 25.17,
        "eligibility_disclosure": "Standard plant and machinery depreciation available to corporate taxpayers under the Income Tax Act 1961.",
        "statutory_reference": "Income Tax Act 1961, Section 32(1) (General Plant & Machinery block)"
    }
}

INR_USD_EXCHANGE_RATE = 83.50  # Modeled exchange rate for dual currency reporting


def calculate_irr_safe(cash_flows: List[float], max_iter: int = 200, tol: float = 1e-6) -> Optional[float]:
    """
    Robust pure-Python IRR calculator using binary search / secant method.
    Returns IRR as a percentage (e.g. 14.5 for 14.5%), or None if not meaningful.
    Ensures safe handling of all-negative, non-converging, or no-positive-return scenarios.
    """
    if not cash_flows or len(cash_flows) < 2:
        return None

    # Condition 1: Must start with negative initial capital outlay
    if cash_flows[0] >= 0:
        return None

    # Condition 2: Sum of subsequent inflows must exceed initial outlay for a positive rate of return
    total_inflows = sum(cash_flows[1:])
    if total_inflows <= abs(cash_flows[0]):
        return None

    # Condition 3: At least one positive inflow must exist
    if all(cf <= 0 for cf in cash_flows[1:]):
        return None

    def npv_func(r: float) -> float:
        total = 0.0
        for i, cf in enumerate(cash_flows):
            denom = (1.0 + r) ** i
            if denom == 0:
                return float("inf")
            total += cf / denom
        return total

    # Define search bracket for realistic industrial project IRRs: -40% to +300%
    low, high = -0.40, 3.0
    f_low = npv_func(low)
    f_high = npv_func(high)

    if f_low * f_high > 0:
        # Check if root is further right
        high = 10.0
        f_high = npv_func(high)
        if f_low * f_high > 0:
            return None

    # Binary search bisection
    for _ in range(max_iter):
        mid = (low + high) / 2.0
        f_mid = npv_func(mid)
        if abs(f_mid) < tol or (high - low) < tol:
            return round(mid * 100.0, 2)
        if f_low * f_mid < 0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid

    return round(((low + high) / 2.0) * 100.0, 2)


class DigitalTwinEngine:
    """
    Digital Twin Engine for factory energy scenario simulation.
    Models Solar PV generation, BESS battery charging/discharging,
    Time-of-Day load shifting, Arrhenius battery degradation, 10-15 year lifecycle economics,
    and Scope 1/2/3 carbon reductions.
    """
    def __init__(self, region: str = "Western"):
        self.region = region
        self.grid_factor = CEA_GRID_EMISSION_FACTORS.get(region, 0.73)
        self.solar_cost_per_kw = 45000.0  # INR per kW installed solar
        self.bess_cost_per_kwh = 18000.0  # INR per kWh installed BESS
        self.peak_tariff_rate = 11.50     # INR per kWh peak ToD tariff
        self.offpeak_tariff_rate = 6.20   # INR per kWh offpeak ToD tariff
        self.pv_temp_coeff = -0.0038      # -0.38% / deg C above 25 deg C STC

    def simulate_battery_degradation(
        self,
        battery_capacity_kwh: float,
        chemistry: str = "LFP",
        daily_cycles: float = 1.0,
        depth_of_discharge: float = 0.80,
        operating_temp_c: float = 35.0,
        simulation_years: int = 10
    ) -> Dict[str, Any]:
        """
        Computes electro-chemical State of Health (SOH) capacity retention over time using
        Arrhenius chemical aging (calendar fade) and mechanical stress fatigue (cycling fade).
        SOH(t) = 1.0 - (B_cal * exp(-E_a / (R*T)) * t^0.5 + B_cyc * (DOD)^beta * N_cycles^gamma)
        """
        chemistry = chemistry.upper()
        # LFP has ~4500-6000 cycles to 80% SOH; NMC has ~2000-3000 cycles.
        if chemistry == "LFP":
            b_cal = 0.012
            b_cyc = 0.00018
            beta = 1.15
            gamma = 0.85
            e_a = 28000.0  # J/mol
        else:  # NMC
            b_cal = 0.022
            b_cyc = 0.00035
            beta = 1.30
            gamma = 0.90
            e_a = 35000.0  # J/mol

        r_gas = 8.314  # J/(mol*K)
        temp_k = operating_temp_c + 273.15
        arrhenius_factor = math.exp(-e_a / (r_gas * temp_k))

        yearly_soh_trajectory = []
        usable_capacity_trajectory = []

        for yr in range(1, simulation_years + 1):
            total_cycles = daily_cycles * 365.0 * yr
            cal_fade = b_cal * (arrhenius_factor * 1e4) * math.sqrt(yr)
            cyc_fade = b_cyc * (depth_of_discharge ** beta) * (total_cycles ** gamma)
            total_fade = cal_fade + cyc_fade
            soh = max(0.40, round(1.0 - total_fade, 4))
            retained_kwh = round(battery_capacity_kwh * soh, 2)
            usable_kwh = round(retained_kwh * depth_of_discharge, 2)
            
            yearly_soh_trajectory.append({
                "year": yr,
                "soh_pct": round(soh * 100.0, 2),
                "retained_capacity_kwh": retained_kwh,
                "usable_capacity_kwh": usable_kwh,
                "calendar_loss_pct": round(cal_fade * 100.0, 2),
                "cycle_loss_pct": round(cyc_fade * 100.0, 2)
            })
            usable_capacity_trajectory.append(usable_kwh)

        end_of_life_80_year = simulation_years
        end_of_life_70_year = simulation_years
        for pt in yearly_soh_trajectory:
            if pt["soh_pct"] <= 80.0 and end_of_life_80_year == simulation_years:
                end_of_life_80_year = pt["year"]
            if pt["soh_pct"] <= 70.0 and end_of_life_70_year == simulation_years:
                end_of_life_70_year = pt["year"]

        return {
            "battery_capacity_kwh": battery_capacity_kwh,
            "chemistry": chemistry,
            "operating_temp_c": operating_temp_c,
            "depth_of_discharge_pct": depth_of_discharge * 100.0,
            "projected_eol_80_pct_year": end_of_life_80_year,
            "projected_eol_70_pct_year": end_of_life_70_year,
            "trajectory": yearly_soh_trajectory,
            "usable_capacity_kwh_trajectory": usable_capacity_trajectory,
            "calibration_status": "SEMI_EMPIRICAL_MODEL",
            "calibration_disclaimer": "Degradation trajectories model Arrhenius calendar fade and cycle mechanical fatigue based on published literature parameters. Site-specific calibration against physical Battery Management System (BMS) telemetry is recommended before capital expenditure commitment."
        }

    def calculate_lifecycle_cashflows(
        self,
        solar_capacity_kw: float,
        battery_storage_kwh: float,
        solar_capex_inr: float,
        bess_capex_inr: float,
        base_annual_solar_kwh: float,
        base_annual_battery_kwh: float,
        base_annual_shifted_kwh: float,
        soh_trajectory: List[Dict[str, Any]],
        simulation_years: int = 15,
        discount_rate_pct: float = 10.0,
        tariff_escalation_pct: float = 4.0,
        om_cost_pct_of_capex: float = 1.5,
        om_escalation_pct: float = 4.0,
        tax_regime: str = "SECTION_32_RENEWABLE_40_WDV",
        corporate_tax_rate_pct: float = 25.17,
        inverter_replacement_year: int = 8,
        inverter_replacement_cost_pct: float = 10.0,
        bess_replacement_threshold_soh: float = 70.0,
        bess_replacement_cost_per_kwh: float = 12000.0,
        salvage_value_pct: float = 5.0
    ) -> Dict[str, Any]:
        """
        Computes 10-15 year lifecycle financial model with:
        - Solar PV annual degradation (0.5%/year)
        - Battery degradation directly driving usable capacity, dispatch, and energy savings over time
        - Tariff escalation
        - Operating & maintenance (O&M) cost escalation
        - Scheduled inverter replacement
        - Battery pack renewal upon reaching SOH replacement threshold
        - Configurable Indian tax depreciation schedules
        - NPV, IRR, simple payback, after-tax cash-flow breakeven, and LCOE.
        """
        total_capex = solar_capex_inr + bess_capex_inr
        discount_r = discount_rate_pct / 100.0
        tariff_esc = tariff_escalation_pct / 100.0
        om_esc = om_escalation_pct / 100.0
        corp_tax_r = corporate_tax_rate_pct / 100.0
        tariff_delta = self.peak_tariff_rate - self.offpeak_tariff_rate

        regime_meta = TAX_REGIMES.get(tax_regime, TAX_REGIMES["NO_TAX_BENEFIT"])
        dep_rate = regime_meta["depreciation_rate_pct"] / 100.0
        effective_corp_tax = corp_tax_r if dep_rate > 0 else 0.0

        opening_wdv = total_capex if dep_rate > 0 else 0.0
        cash_flows_nominal = [-total_capex]
        cash_flow_table = []
        cum_cf = -total_capex
        cum_dcf = -total_capex
        bess_replaced = False
        bess_replacement_year_occurred = None

        total_gross_savings = 0.0
        total_om_costs = 0.0
        total_replacement_costs = 0.0
        total_tax_shields = 0.0
        total_solar_gen_kwh = 0.0
        discounted_gen_kwh_sum = 0.0
        discounted_costs_sum = total_capex

        for yr in range(1, simulation_years + 1):
            # 1. Solar PV degradation (0.5% per annum after Year 1)
            solar_deg_factor = (1.0 - 0.005) ** (yr - 1)
            annual_solar_kwh = base_annual_solar_kwh * solar_deg_factor
            total_solar_gen_kwh += annual_solar_kwh
            discounted_gen_kwh_sum += annual_solar_kwh / ((1.0 + discount_r) ** yr)

            # 2. Battery degradation feedback into dispatch and usable capacity
            soh_entry = soh_trajectory[yr - 1] if yr <= len(soh_trajectory) else soh_trajectory[-1]
            current_soh = soh_entry["soh_pct"]

            bess_rep_cost = 0.0
            if current_soh <= bess_replacement_threshold_soh and not bess_replaced and battery_storage_kwh > 0:
                bess_rep_cost = battery_storage_kwh * bess_replacement_cost_per_kwh
                bess_replaced = True
                bess_replacement_year_occurred = yr
                current_soh = 100.0  # Reset capacity after replacement

            # Usable battery capacity scales peak-shaving energy
            bess_scale_factor = current_soh / 100.0
            annual_battery_kwh = base_annual_battery_kwh * bess_scale_factor

            # 3. Tariff escalation
            eff_peak_tariff = self.peak_tariff_rate * ((1.0 + tariff_esc) ** (yr - 1))
            eff_tariff_delta = tariff_delta * ((1.0 + tariff_esc) ** (yr - 1))

            solar_save = annual_solar_kwh * eff_peak_tariff
            bess_save = annual_battery_kwh * eff_tariff_delta
            shift_save = base_annual_shifted_kwh * eff_tariff_delta
            gross_save = solar_save + bess_save + shift_save
            total_gross_savings += gross_save

            # 4. Operating and maintenance costs with escalation
            om_cost = (total_capex * (om_cost_pct_of_capex / 100.0)) * ((1.0 + om_esc) ** (yr - 1))
            total_om_costs += om_cost

            # 5. Inverter replacement
            inv_rep_cost = 0.0
            if yr == inverter_replacement_year and solar_capacity_kw > 0:
                inv_rep_cost = solar_capex_inr * (inverter_replacement_cost_pct / 100.0)

            total_rep_costs_yr = inv_rep_cost + bess_rep_cost
            total_replacement_costs += total_rep_costs_yr
            total_expenses_yr = om_cost + total_rep_costs_yr
            discounted_costs_sum += total_expenses_yr / ((1.0 + discount_r) ** yr)

            # 6. Tax depreciation and shield
            if dep_rate > 0:
                depreciation = opening_wdv * dep_rate
                closing_wdv = opening_wdv - depreciation
                tax_shield = depreciation * effective_corp_tax
                opening_wdv = closing_wdv
            else:
                depreciation = 0.0
                closing_wdv = 0.0
                tax_shield = 0.0

            total_tax_shields += tax_shield

            # 7. Net annual nominal cash flow
            net_cf = gross_save - total_expenses_yr + tax_shield

            # Terminal salvage value in final simulation year
            salvage_val = 0.0
            if yr == simulation_years and total_capex > 0:
                salvage_val = total_capex * (salvage_value_pct / 100.0)
                net_cf += salvage_val

            cash_flows_nominal.append(round(net_cf, 2))

            # Discounted cash flow
            dcf = net_cf / ((1.0 + discount_r) ** yr)
            cum_cf += net_cf
            cum_dcf += dcf

            cash_flow_table.append({
                "year": yr,
                "solar_generation_kwh": round(annual_solar_kwh, 1),
                "battery_soh_pct": round(current_soh, 2),
                "battery_shaved_kwh": round(annual_battery_kwh, 1),
                "effective_peak_tariff_inr": round(eff_peak_tariff, 2),
                "gross_savings_inr": round(gross_save, 2),
                "om_cost_inr": round(om_cost, 2),
                "inverter_replacement_cost_inr": round(inv_rep_cost, 2),
                "battery_replacement_cost_inr": round(bess_rep_cost, 2),
                "total_expenses_inr": round(total_expenses_yr, 2),
                "depreciation_inr": round(depreciation, 2),
                "tax_shield_inr": round(tax_shield, 2),
                "salvage_value_inr": round(salvage_val, 2),
                "net_cashflow_inr": round(net_cf, 2),
                "net_cashflow_usd": round(net_cf / INR_USD_EXCHANGE_RATE, 2),
                "discounted_cashflow_inr": round(dcf, 2),
                "cumulative_cashflow_inr": round(cum_cf, 2),
                "cumulative_discounted_cashflow_inr": round(cum_dcf, 2)
            })

        npv_inr = round(cum_dcf, 2)
        npv_usd = round(npv_inr / INR_USD_EXCHANGE_RATE, 2)

        # Robust IRR computation
        irr_pct = calculate_irr_safe(cash_flows_nominal)
        irr_status = "CALCULATED" if irr_pct is not None else "NOT_MEANINGFUL"
        irr_explanation = (
            f"Internal Rate of Return is {irr_pct}% based on modeled multi-year cash flows."
            if irr_pct is not None else
            "IRR is not meaningful for this scenario (cumulative operational inflows do not exceed initial capital outlay or cash flows contain no positive returns)."
        )

        # Undiscounted Simple Payback
        yr1_net_savings = cash_flow_table[0]["gross_savings_inr"] - cash_flow_table[0]["om_cost_inr"]
        if total_capex == 0:
            simple_payback = 0.0
        elif yr1_net_savings > 0:
            simple_payback = round(total_capex / yr1_net_savings, 2)
        else:
            simple_payback = None

        # After-Tax Cash-Flow Breakeven (interpolated)
        after_tax_breakeven = None
        if total_capex == 0:
            after_tax_breakeven = 0.0
        else:
            for i in range(len(cash_flow_table)):
                prev_cum = -total_capex if i == 0 else cash_flow_table[i - 1]["cumulative_cashflow_inr"]
                curr_cum = cash_flow_table[i]["cumulative_cashflow_inr"]
                if prev_cum < 0 and curr_cum >= 0:
                    net_inflow = cash_flow_table[i]["net_cashflow_inr"]
                    fraction = abs(prev_cum) / net_inflow if net_inflow > 0 else 0.0
                    after_tax_breakeven = round(i + fraction, 2)
                    break

        # Levelized Cost of Energy (LCOE)
        if discounted_gen_kwh_sum > 0:
            lcoe_inr = round(discounted_costs_sum / discounted_gen_kwh_sum, 4)
            lcoe_usd = round(lcoe_inr / INR_USD_EXCHANGE_RATE, 4)
        else:
            lcoe_inr = 0.0
            lcoe_usd = 0.0

        return {
            "simulation_horizon_years": simulation_years,
            "discount_rate_pct": discount_rate_pct,
            "tariff_escalation_pct": tariff_escalation_pct,
            "om_cost_pct_of_capex": om_cost_pct_of_capex,
            "om_escalation_pct": om_escalation_pct,
            "inverter_replacement_year": inverter_replacement_year,
            "battery_replacement_year": bess_replacement_year_occurred,
            "initial_capex_inr": round(total_capex, 2),
            "initial_capex_usd": round(total_capex / INR_USD_EXCHANGE_RATE, 2),
            "total_lifecycle_gross_savings_inr": round(total_gross_savings, 2),
            "total_lifecycle_om_cost_inr": round(total_om_costs, 2),
            "total_lifecycle_replacements_inr": round(total_replacement_costs, 2),
            "total_tax_shield_inr": round(total_tax_shields, 2),
            "net_present_value_inr": npv_inr,
            "net_present_value_usd": npv_usd,
            "undiscounted_simple_payback_years": simple_payback,
            "after_tax_cashflow_breakeven_years": after_tax_breakeven,
            "internal_rate_of_return_pct": irr_pct,
            "irr_status": irr_status,
            "irr_explanation": irr_explanation,
            "levelized_cost_of_energy_inr_kwh": lcoe_inr,
            "levelized_cost_of_energy_usd_kwh": lcoe_usd,
            "cash_flows_nominal": cash_flows_nominal,
            "cash_flow_table": cash_flow_table
        }

    def calculate_lifecycle_sensitivity(
        self,
        base_solar_kw: float,
        base_battery_kwh: float,
        base_monthly_kwh: float,
        base_load_shift_pct: float,
        base_ambient_temp_c: float = 34.0,
        base_chemistry: str = "LFP",
        base_discount_rate_pct: float = 10.0,
        base_tax_regime: str = "SECTION_32_RENEWABLE_40_WDV"
    ) -> Dict[str, Any]:
        """
        Computes multi-dimensional sensitivity analysis and Tornado Drivers ranking.
        Evaluates parameter swings across CapEx, Tariffs, Solar Yield, Degradation,
        Discount Rate, O&M, and Inverter Replacement Timing.
        """
        def run_model_npv(
            solar_kw=base_solar_kw,
            battery_kwh=base_battery_kwh,
            solar_cost=self.solar_cost_per_kw,
            bess_cost=self.bess_cost_per_kwh,
            peak_tariff=self.peak_tariff_rate,
            offpeak_tariff=self.offpeak_tariff_rate,
            yield_multiplier=1.0,
            discount_r=base_discount_rate_pct,
            om_esc=4.0,
            inv_yr=8,
            tax_reg=base_tax_regime,
            degradation_mult=1.0
        ) -> float:
            solar_capex = solar_kw * solar_cost
            bess_capex = battery_kwh * bess_cost
            total_capex = solar_capex + bess_capex

            if total_capex == 0:
                return 0.0

            # Base yields
            temp_loss = max(0.0, (base_ambient_temp_c - 25.0) * abs(self.pv_temp_coeff))
            derated_yield = 4.5 * (1.0 - temp_loss) * yield_multiplier
            daily_solar = solar_kw * derated_yield
            annual_solar = daily_solar * 365.0

            daily_battery = battery_kwh * 0.85
            annual_battery = daily_battery * 365.0

            annual_shifted = (base_monthly_kwh * 12.0 * (base_load_shift_pct / 100.0)) * 0.4

            # Aging trajectory
            aging = self.simulate_battery_degradation(
                battery_capacity_kwh=battery_kwh,
                chemistry=base_chemistry,
                simulation_years=15
            )
            # Adjust aging trajectory by degradation multiplier
            adjusted_traj = []
            for pt in aging["trajectory"]:
                loss = (100.0 - pt["soh_pct"]) * degradation_mult
                adj_soh = max(40.0, 100.0 - loss)
                adjusted_traj.append({"year": pt["year"], "soh_pct": adj_soh})

            lifecycle = self.calculate_lifecycle_cashflows(
                solar_capacity_kw=solar_kw,
                battery_storage_kwh=battery_kwh,
                solar_capex_inr=solar_capex,
                bess_capex_inr=bess_capex,
                base_annual_solar_kwh=annual_solar,
                base_annual_battery_kwh=annual_battery,
                base_annual_shifted_kwh=annual_shifted,
                soh_trajectory=adjusted_traj,
                simulation_years=15,
                discount_rate_pct=discount_r,
                om_escalation_pct=om_esc,
                inverter_replacement_year=inv_yr,
                tax_regime=tax_reg
            )
            return lifecycle["net_present_value_inr"]

        base_npv = run_model_npv()

        # Tornado parameter variations
        variations = [
            {
                "parameter": "Grid Tariff Rate",
                "key": "tariff",
                "base_value": f"₹{self.peak_tariff_rate:.2f}/kWh",
                "low_label": "-15% (₹9.78)",
                "high_label": "+15% (₹13.23)",
                "fn_low": lambda: run_model_npv(peak_tariff=self.peak_tariff_rate * 0.85),
                "fn_high": lambda: run_model_npv(peak_tariff=self.peak_tariff_rate * 1.15)
            },
            {
                "parameter": "Installed CapEx",
                "key": "capex",
                "base_value": f"₹{self.solar_cost_per_kw:,.0f}/kW Solar, ₹{self.bess_cost_per_kwh:,.0f}/kWh BESS",
                "low_label": "-15% CapEx",
                "high_label": "+15% CapEx",
                "fn_low": lambda: run_model_npv(solar_cost=self.solar_cost_per_kw * 0.85, bess_cost=self.bess_cost_per_kwh * 0.85),
                "fn_high": lambda: run_model_npv(solar_cost=self.solar_cost_per_kw * 1.15, bess_cost=self.bess_cost_per_kwh * 1.15)
            },
            {
                "parameter": "Solar Yield / Insolation",
                "key": "solar_yield",
                "base_value": "4.50 kWh/kW/day (STC)",
                "low_label": "-15% Solar Yield",
                "high_label": "+15% Solar Yield",
                "fn_low": lambda: run_model_npv(yield_multiplier=0.85),
                "fn_high": lambda: run_model_npv(yield_multiplier=1.15)
            },
            {
                "parameter": "Discount Rate (WACC)",
                "key": "discount_rate",
                "base_value": f"{base_discount_rate_pct:.1f}%",
                "low_label": "8.0% (-2.0%)",
                "high_label": "12.0% (+2.0%)",
                "fn_low": lambda: run_model_npv(discount_r=8.0),
                "fn_high": lambda: run_model_npv(discount_r=12.0)
            },
            {
                "parameter": "Battery Degradation Rate",
                "key": "battery_degradation",
                "base_value": "Nominal LFP Arrhenius",
                "low_label": "-25% Wear (Gentle)",
                "high_label": "+25% Wear (Aggressive)",
                "fn_low": lambda: run_model_npv(degradation_mult=0.75),
                "fn_high": lambda: run_model_npv(degradation_mult=1.25)
            },
            {
                "parameter": "O&M Cost Escalation",
                "key": "om_escalation",
                "base_value": "4.0%/yr",
                "low_label": "2.0%/yr",
                "high_label": "6.0%/yr",
                "fn_low": lambda: run_model_npv(om_esc=2.0),
                "fn_high": lambda: run_model_npv(om_esc=6.0)
            },
            {
                "parameter": "Inverter Replacement Timing",
                "key": "inverter_replacement",
                "base_value": "Year 8",
                "low_label": "Year 6 (Early)",
                "high_label": "Year 10 (Extended)",
                "fn_low": lambda: run_model_npv(inv_yr=6),
                "fn_high": lambda: run_model_npv(inv_yr=10)
            }
        ]

        tornado_drivers = []
        for v in variations:
            npv_low = round(v["fn_low"](), 2)
            npv_high = round(v["fn_high"](), 2)
            swing = round(abs(npv_high - npv_low), 2)
            
            impact = "HIGH" if swing > 5000000.0 else ("MEDIUM" if swing > 1000000.0 else "LOW")
            tornado_drivers.append({
                "parameter": v["parameter"],
                "key": v["key"],
                "base_value": v["base_value"],
                "low_label": v["low_label"],
                "high_label": v["high_label"],
                "npv_at_low_inr": npv_low,
                "npv_at_low_usd": round(npv_low / INR_USD_EXCHANGE_RATE, 2),
                "npv_at_high_inr": npv_high,
                "npv_at_high_usd": round(npv_high / INR_USD_EXCHANGE_RATE, 2),
                "npv_swing_inr": swing,
                "npv_swing_usd": round(swing / INR_USD_EXCHANGE_RATE, 2),
                "impact_level": impact
            })

        # Sort descending by NPV swing to generate ranking
        tornado_drivers.sort(key=lambda d: d["npv_swing_inr"], reverse=True)
        for i, d in enumerate(tornado_drivers, 1):
            d["rank"] = i

        # Scenario comparisons: Best Case, Base Case, Worst Case
        best_npv = run_model_npv(
            yield_multiplier=1.10,
            peak_tariff=self.peak_tariff_rate * 1.10,
            solar_cost=self.solar_cost_per_kw * 0.90,
            bess_cost=self.bess_cost_per_kwh * 0.90,
            discount_r=8.0,
            degradation_mult=0.85
        )
        worst_npv = run_model_npv(
            yield_multiplier=0.90,
            peak_tariff=self.peak_tariff_rate * 0.90,
            solar_cost=self.solar_cost_per_kw * 1.10,
            bess_cost=self.bess_cost_per_kwh * 1.10,
            discount_r=12.0,
            degradation_mult=1.20
        )

        scenarios = {
            "base_case": {
                "name": "Base Scenario",
                "description": "Nominal insolation, current TOU tariff, standard equipment pricing",
                "npv_inr": round(base_npv, 2),
                "npv_usd": round(base_npv / INR_USD_EXCHANGE_RATE, 2)
            },
            "best_case": {
                "name": "Optimistic Scenario",
                "description": "+10% solar yield, +10% peak tariffs, -10% CapEx, 8% discount rate",
                "npv_inr": round(best_npv, 2),
                "npv_usd": round(best_npv / INR_USD_EXCHANGE_RATE, 2)
            },
            "worst_case": {
                "name": "Stress / Pessimistic Scenario",
                "description": "-10% solar yield, -10% peak tariffs, +10% CapEx, 12% discount rate, +20% battery aging",
                "npv_inr": round(worst_npv, 2),
                "npv_usd": round(worst_npv / INR_USD_EXCHANGE_RATE, 2)
            }
        }

        return {
            "base_npv_inr": round(base_npv, 2),
            "tornado_drivers": tornado_drivers,
            "top_npv_driver": tornado_drivers[0]["parameter"] if tornado_drivers else "Grid Tariff Rate",
            "scenario_comparison": scenarios
        }

    def simulate_scenario(
        self,
        base_monthly_kwh: float,
        solar_capacity_kw: float,
        battery_storage_kwh: float,
        load_shift_pct: float,
        ambient_temp_c: float = 34.0,
        battery_chemistry: str = "LFP",
        simulation_years: int = 15,
        discount_rate_pct: float = 10.0,
        tariff_escalation_pct: float = 4.0,
        om_cost_pct_of_capex: float = 1.5,
        om_escalation_pct: float = 4.0,
        tax_regime: str = "SECTION_32_RENEWABLE_40_WDV",
        corporate_tax_rate_pct: float = 25.17,
        inverter_replacement_year: int = 8,
        bess_replacement_threshold_soh: float = 70.0
    ) -> Dict[str, Any]:
        """
        Runs digital twin physics simulation based on user inputs.
        Fully integrates Year 1 physics with 10-15 year lifecycle financial validation,
        Arrhenius battery degradation feedback into dispatch/savings, and configurable Indian tax regimes.
        """
        # Validate tax regime selection
        if tax_regime not in TAX_REGIMES:
            tax_regime = "NO_TAX_BENEFIT"
        regime_meta = TAX_REGIMES[tax_regime]

        # 1. Solar Generation with Temperature Derating
        temp_loss_factor = max(0.0, (ambient_temp_c - 25.0) * abs(self.pv_temp_coeff))
        derated_solar_yield = 4.5 * (1.0 - temp_loss_factor)  # kWh/kW/day
        daily_solar_kwh = solar_capacity_kw * derated_solar_yield
        monthly_solar_kwh = daily_solar_kwh * 30.0
        annual_solar_kwh_base = daily_solar_kwh * 365.0

        # 2. Battery Storage Peak Shaving Contribution
        daily_battery_shaved_kwh = battery_storage_kwh * 0.85
        monthly_battery_kwh = daily_battery_shaved_kwh * 30.0
        annual_battery_kwh_base = daily_battery_shaved_kwh * 365.0

        # 3. Load Shift Savings
        monthly_shifted_kwh = (base_monthly_kwh * (load_shift_pct / 100.0)) * 0.4
        annual_shifted_kwh_base = monthly_shifted_kwh * 12.0
        tariff_delta = self.peak_tariff_rate - self.offpeak_tariff_rate
        monthly_load_shift_savings = monthly_shifted_kwh * tariff_delta

        # 4. Financial Calculations (Year 1)
        solar_savings_inr = monthly_solar_kwh * self.peak_tariff_rate
        bess_savings_inr = monthly_battery_kwh * tariff_delta
        total_monthly_savings_inr = solar_savings_inr + bess_savings_inr + monthly_load_shift_savings
        annual_financial_savings_inr = total_monthly_savings_inr * 12.0

        # CAPEX Estimation
        solar_capex = solar_capacity_kw * self.solar_cost_per_kw
        bess_capex = battery_storage_kwh * self.bess_cost_per_kwh
        total_capex = solar_capex + bess_capex

        # 5. Carbon Offset Calculations (Scope 1, 2, 3)
        total_offset_kwh_monthly = monthly_solar_kwh + monthly_battery_kwh
        monthly_co2_saved_kg = total_offset_kwh_monthly * self.grid_factor
        annual_co2_saved_tons = round((monthly_co2_saved_kg * 12.0) / 1000.0, 2)

        # Scope 2 Market vs Location Based
        scope2_location_tons = round((base_monthly_kwh * 12.0 * self.grid_factor) / 1000.0, 2)
        scope2_market_tons = max(0.0, round(scope2_location_tons - annual_co2_saved_tons, 2))

        # Net grid consumption
        net_monthly_kwh = max(0.0, base_monthly_kwh - monthly_solar_kwh)

        # 6. Battery Degradation Simulation
        bess_aging = self.simulate_battery_degradation(
            battery_capacity_kwh=battery_storage_kwh,
            chemistry=battery_chemistry,
            operating_temp_c=ambient_temp_c,
            simulation_years=simulation_years
        )

        # 7. Comprehensive Lifecycle Cash Flows (10-15 years)
        lifecycle = self.calculate_lifecycle_cashflows(
            solar_capacity_kw=solar_capacity_kw,
            battery_storage_kwh=battery_storage_kwh,
            solar_capex_inr=solar_capex,
            bess_capex_inr=bess_capex,
            base_annual_solar_kwh=annual_solar_kwh_base,
            base_annual_battery_kwh=annual_battery_kwh_base,
            base_annual_shifted_kwh=annual_shifted_kwh_base,
            soh_trajectory=bess_aging["trajectory"],
            simulation_years=simulation_years,
            discount_rate_pct=discount_rate_pct,
            tariff_escalation_pct=tariff_escalation_pct,
            om_cost_pct_of_capex=om_cost_pct_of_capex,
            om_escalation_pct=om_escalation_pct,
            tax_regime=tax_regime,
            corporate_tax_rate_pct=corporate_tax_rate_pct,
            inverter_replacement_year=inverter_replacement_year,
            bess_replacement_threshold_soh=bess_replacement_threshold_soh
        )

        # 8. Multi-Variable Sensitivity & Tornado Ranking
        sensitivity = self.calculate_sensitivity_analysis(
            base_capex=total_capex,
            base_annual_savings=annual_financial_savings_inr,
            base_solar_yield=derated_solar_yield,
            base_tariff=self.peak_tariff_rate,
            tax_regime=tax_regime
        )

        tornado_analysis = self.calculate_lifecycle_sensitivity(
            base_solar_kw=solar_capacity_kw,
            base_battery_kwh=battery_storage_kwh,
            base_monthly_kwh=base_monthly_kwh,
            base_load_shift_pct=load_shift_pct,
            base_ambient_temp_c=ambient_temp_c,
            base_chemistry=battery_chemistry,
            base_discount_rate_pct=discount_rate_pct,
            base_tax_regime=tax_regime
        )

        # Tax Audit Structure
        tax_regime_audit = {
            "selected_regime": tax_regime,
            "regime_name": regime_meta["name"],
            "statutory_reference": regime_meta["statutory_reference"],
            "depreciation_rate_pct": regime_meta["depreciation_rate_pct"],
            "corporate_tax_rate_pct": regime_meta["corporate_tax_rate_pct"],
            "year1_depreciation_inr": round(total_capex * (regime_meta["depreciation_rate_pct"] / 100.0), 2),
            "year1_tax_shield_inr": round((total_capex * (regime_meta["depreciation_rate_pct"] / 100.0)) * (regime_meta["corporate_tax_rate_pct"] / 100.0), 2),
            "total_lifecycle_tax_shield_inr": lifecycle["total_tax_shield_inr"],
            "eligibility_disclosure": regime_meta["eligibility_disclosure"],
            "disclaimer": "Modeled estimates for scenario analysis only. Does not constitute tax or investment advice. Eligibility for Section 32 depreciation depends on the company's elected corporate tax regime and asset commissioning timeline."
        }

        # Legacy backward-compatible payback
        payback_years = lifecycle["undiscounted_simple_payback_years"] or 0.0

        return {
            "region": self.region,
            "grid_emission_factor_kg_kwh": self.grid_factor,
            "inputs": {
                "base_monthly_kwh": base_monthly_kwh,
                "solar_capacity_kw": solar_capacity_kw,
                "battery_storage_kwh": battery_storage_kwh,
                "load_shift_pct": load_shift_pct,
                "ambient_temp_c": ambient_temp_c,
                "battery_chemistry": battery_chemistry,
                "pv_temp_derating_pct": round(temp_loss_factor * 100.0, 2),
                "simulation_years": simulation_years,
                "discount_rate_pct": discount_rate_pct,
                "tax_regime": tax_regime
            },
            "energy_metrics": {
                "monthly_solar_generation_kwh": round(monthly_solar_kwh, 2),
                "monthly_bess_shaved_kwh": round(monthly_battery_kwh, 2),
                "monthly_shifted_kwh": round(monthly_shifted_kwh, 2),
                "net_monthly_grid_kwh": round(net_monthly_kwh, 2)
            },
            "financial_metrics": {
                "monthly_savings_inr": round(total_monthly_savings_inr, 2),
                "monthly_savings_usd": round(total_monthly_savings_inr / INR_USD_EXCHANGE_RATE, 2),
                "annual_savings_inr": round(annual_financial_savings_inr, 2),
                "annual_savings_usd": round(annual_financial_savings_inr / INR_USD_EXCHANGE_RATE, 2),
                "estimated_capex_inr": round(total_capex, 2),
                "estimated_capex_usd": round(total_capex / INR_USD_EXCHANGE_RATE, 2),
                "payback_period_years": payback_years,
                "undiscounted_simple_payback_years": lifecycle["undiscounted_simple_payback_years"],
                "after_tax_cashflow_breakeven_years": lifecycle["after_tax_cashflow_breakeven_years"],
                "net_present_value_inr": lifecycle["net_present_value_inr"],
                "net_present_value_usd": lifecycle["net_present_value_usd"],
                "internal_rate_of_return_pct": lifecycle["internal_rate_of_return_pct"],
                "irr_status": lifecycle["irr_status"],
                "irr_explanation": lifecycle["irr_explanation"],
                "levelized_cost_of_energy_inr_kwh": lifecycle["levelized_cost_of_energy_inr_kwh"],
                "levelized_cost_of_energy_usd_kwh": lifecycle["levelized_cost_of_energy_usd_kwh"],
                "inr_metrics": sensitivity.get("indian_tax_regime", {}),
                "sensitivity_analysis": sensitivity
            },
            "lifecycle_analysis": lifecycle,
            "sensitivity_tornado": tornado_analysis,
            "tax_regime_audit": tax_regime_audit,
            "carbon_metrics": {
                "monthly_co2_reduction_kg": round(monthly_co2_saved_kg, 2),
                "annual_co2_reduction_tons": annual_co2_saved_tons,
                "scope2_location_based_tons": scope2_location_tons,
                "scope2_market_based_tons": scope2_market_tons,
                "trees_equivalent_planted": int(annual_co2_saved_tons * 45)
            },
            "battery_lifecycle": bess_aging,
            "disclaimers": {
                "nature_of_results": "MODELED_ESTIMATES",
                "accuracy_notice": "Outputs represent engineering and discounted cash-flow simulations based on user input parameters, published CEA grid factors, and standard industrial asset assumptions. They do not constitute guaranteed savings or formal investment/tax advice.",
                "tax_advisory_notice": "Tax depreciation shield is calculated for illustrative purposes under the specified Income Tax Act regime. Exact deductibility must be validated with a qualified chartered accountant."
            }
        }

    def calculate_sensitivity_analysis(
        self,
        base_capex: float,
        base_annual_savings: float,
        base_solar_yield: float = 4.5,
        base_tariff: float = 11.50,
        tax_regime: str = "SECTION_32_RENEWABLE_40_WDV"
    ) -> Dict[str, Any]:
        """
        Calculates multi-dimensional financial sensitivity for payback period
        under varying grid tariffs, solar yields, and capital expenditures (+/-10%, +/-20%).
        Also computes Indian Accelerated Depreciation vs standard SLM.
        """
        variations = [-0.20, -0.10, 0.0, 0.10, 0.20]

        tariff_sensitivity = []
        for v in variations:
            factor = 1.0 + v
            adj_savings = base_annual_savings * factor
            payback = round(base_capex / max(1.0, adj_savings), 2) if base_capex > 0 else 0.0
            tariff_sensitivity.append({
                "variation_pct": int(v * 100),
                "tariff_rate_inr": round(base_tariff * factor, 2),
                "annual_savings_inr": round(adj_savings, 2),
                "payback_years": payback
            })

        capex_sensitivity = []
        for v in variations:
            factor = 1.0 + v
            adj_capex = base_capex * factor
            payback = round(adj_capex / max(1.0, base_annual_savings), 2) if base_annual_savings > 0 else 0.0
            capex_sensitivity.append({
                "variation_pct": int(v * 100),
                "capex_inr": round(adj_capex, 2),
                "payback_years": payback
            })

        solar_yield_sensitivity = []
        for v in variations:
            factor = 1.0 + v
            adj_savings = base_annual_savings * (0.4 + 0.6 * factor)  # 60% of savings linked to solar generation
            payback = round(base_capex / max(1.0, adj_savings), 2) if base_capex > 0 else 0.0
            solar_yield_sensitivity.append({
                "variation_pct": int(v * 100),
                "solar_yield_kwh_kw_day": round(base_solar_yield * factor, 2),
                "payback_years": payback
            })

        # Selected tax regime shield
        regime_meta = TAX_REGIMES.get(tax_regime, TAX_REGIMES["NO_TAX_BENEFIT"])
        dep_rate = regime_meta["depreciation_rate_pct"] / 100.0
        tax_rate = regime_meta["corporate_tax_rate_pct"] / 100.0
        year1_depreciation_inr = base_capex * dep_rate
        year1_tax_shield_inr = round(year1_depreciation_inr * tax_rate, 2)
        after_tax_year1_savings_inr = round(base_annual_savings + year1_tax_shield_inr, 2)
        effective_year1_payback = round(base_capex / max(1.0, after_tax_year1_savings_inr), 2) if base_capex > 0 else 0.0

        return {
            "base_capex_inr": round(base_capex, 2),
            "base_annual_savings_inr": round(base_annual_savings, 2),
            "tariff_sensitivity": tariff_sensitivity,
            "capex_sensitivity": capex_sensitivity,
            "solar_yield_sensitivity": solar_yield_sensitivity,
            "indian_tax_regime": {
                "section": regime_meta["name"],
                "regime_key": regime_meta["regime_key"],
                "depreciation_rate_pct": regime_meta["depreciation_rate_pct"],
                "effective_corporate_tax_rate_pct": regime_meta["corporate_tax_rate_pct"],
                "year1_tax_shield_inr": year1_tax_shield_inr,
                "effective_after_tax_year1_payback_years": effective_year1_payback,
                "eligibility_disclosure": regime_meta["eligibility_disclosure"]
            }
        }

    def get_grid_audit_data(self) -> Dict[str, Any]:
        """Returns national and regional grid emission breakdown."""
        return {
            "source": "Central Electricity Authority (CEA) Baseline Database v19.0",
            "national_average_kg_kwh": CEA_GRID_EMISSION_FACTORS["National Average"],
            "regional_breakdown": CEA_GRID_EMISSION_FACTORS,
            "state_breakdown": STATE_GRID_FACTORS
        }
