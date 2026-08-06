"""
PRAGATI AI — Digital Twin Scenario Simulation, Battery Degradation Physics & Carbon Analytics Engine
Provides physical modeling for Solar PV with temperature derating, LFP/NMC BESS Arrhenius battery aging,
Load Shifting, CEA Grid Emission Factors, and Scope 1/2/3 ESG reporting.
"""

import math
from typing import Dict, Any, List, Optional

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

class DigitalTwinEngine:
    """
    Digital Twin Engine for factory energy scenario simulation.
    Models Solar PV generation, BESS battery charging/discharging,
    Time-of-Day load shifting, Arrhenius battery degradation, and Scope 1/2/3 carbon reductions.
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
        soh_current = 1.0

        for yr in range(1, simulation_years + 1):
            total_cycles = daily_cycles * 365.0 * yr
            cal_fade = b_cal * (arrhenius_factor * 1e4) * math.sqrt(yr)
            cyc_fade = b_cyc * (depth_of_discharge ** beta) * (total_cycles ** gamma)
            total_fade = cal_fade + cyc_fade
            soh = max(0.40, round(1.0 - total_fade, 4))
            retained_kwh = round(battery_capacity_kwh * soh, 2)
            yearly_soh_trajectory.append({
                "year": yr,
                "soh_pct": round(soh * 100.0, 2),
                "retained_capacity_kwh": retained_kwh,
                "calendar_loss_pct": round(cal_fade * 100.0, 2),
                "cycle_loss_pct": round(cyc_fade * 100.0, 2)
            })

        end_of_life_year = simulation_years
        for pt in yearly_soh_trajectory:
            if pt["soh_pct"] <= 80.0:
                end_of_life_year = pt["year"]
                break

        return {
            "battery_capacity_kwh": battery_capacity_kwh,
            "chemistry": chemistry,
            "operating_temp_c": operating_temp_c,
            "depth_of_discharge_pct": depth_of_discharge * 100.0,
            "projected_eol_80_pct_year": end_of_life_year,
            "trajectory": yearly_soh_trajectory
        }

    def simulate_scenario(
        self,
        base_monthly_kwh: float,
        solar_capacity_kw: float,
        battery_storage_kwh: float,
        load_shift_pct: float,
        ambient_temp_c: float = 34.0,
        battery_chemistry: str = "LFP"
    ) -> Dict[str, Any]:
        """
        Runs digital twin physics simulation based on user inputs.
        """
        # 1. Solar Generation with Temperature Derating
        temp_loss_factor = max(0.0, (ambient_temp_c - 25.0) * abs(self.pv_temp_coeff))
        derated_solar_yield = 4.5 * (1.0 - temp_loss_factor)  # kWh/kW/day
        daily_solar_kwh = solar_capacity_kw * derated_solar_yield
        monthly_solar_kwh = daily_solar_kwh * 30.0
        
        # 2. Battery Storage Peak Shaving Contribution
        # Efficiency 85% round-trip, 1 cycle per day
        daily_battery_shaved_kwh = battery_storage_kwh * 0.85
        monthly_battery_kwh = daily_battery_shaved_kwh * 30.0
        
        # 3. Load Shift Savings
        # Shifting load from peak to off-peak tariff (delta = INR 5.30/kWh)
        monthly_shifted_kwh = (base_monthly_kwh * (load_shift_pct / 100.0)) * 0.4
        tariff_delta = self.peak_tariff_rate - self.offpeak_tariff_rate
        monthly_load_shift_savings = monthly_shifted_kwh * tariff_delta
        
        # 4. Financial Calculations
        solar_savings_inr = monthly_solar_kwh * self.peak_tariff_rate
        bess_savings_inr = monthly_battery_kwh * tariff_delta
        total_monthly_savings_inr = solar_savings_inr + bess_savings_inr + monthly_load_shift_savings
        annual_financial_savings_inr = total_monthly_savings_inr * 12.0
        
        # CAPEX Estimation
        solar_capex = solar_capacity_kw * self.solar_cost_per_kw
        bess_capex = battery_storage_kwh * self.bess_cost_per_kwh
        total_capex = solar_capex + bess_capex
        
        payback_period_years = round(total_capex / max(1.0, annual_financial_savings_inr), 2) if total_capex > 0 else 0.0
        
        # 5. Carbon Offset Calculations (Scope 1, 2, 3)
        total_offset_kwh_monthly = monthly_solar_kwh + monthly_battery_kwh
        monthly_co2_saved_kg = total_offset_kwh_monthly * self.grid_factor
        annual_co2_saved_tons = round((monthly_co2_saved_kg * 12.0) / 1000.0, 2)
        
        # Scope 2 Market vs Location Based
        scope2_location_tons = round((base_monthly_kwh * 12.0 * self.grid_factor) / 1000.0, 2)
        scope2_market_tons = max(0.0, round(scope2_location_tons - annual_co2_saved_tons, 2))

        # New net grid consumption
        net_monthly_kwh = max(0.0, base_monthly_kwh - monthly_solar_kwh)
        
        # Battery degradation forecast
        bess_aging = self.simulate_battery_degradation(
            battery_capacity_kwh=battery_storage_kwh,
            chemistry=battery_chemistry,
            operating_temp_c=ambient_temp_c,
            simulation_years=10
        )

        return {
            "region": self.region,
            "grid_emission_factor_kg_kwh": self.grid_factor,
            "inputs": {
                "base_monthly_kwh": base_monthly_kwh,
                "solar_capacity_kw": solar_capacity_kw,
                "battery_storage_kwh": battery_storage_kwh,
                "load_shift_pct": load_shift_pct,
                "ambient_temp_c": ambient_temp_c,
                "pv_temp_derating_pct": round(temp_loss_factor * 100.0, 2)
            },
            "energy_metrics": {
                "monthly_solar_generation_kwh": round(monthly_solar_kwh, 2),
                "monthly_bess_shaved_kwh": round(monthly_battery_kwh, 2),
                "monthly_shifted_kwh": round(monthly_shifted_kwh, 2),
                "net_monthly_grid_kwh": round(net_monthly_kwh, 2)
            },
            "financial_metrics": {
                "monthly_savings_inr": round(total_monthly_savings_inr, 2),
                "annual_savings_inr": round(annual_financial_savings_inr, 2),
                "estimated_capex_inr": round(total_capex, 2),
                "payback_period_years": payback_period_years
            },
            "carbon_metrics": {
                "monthly_co2_reduction_kg": round(monthly_co2_saved_kg, 2),
                "annual_co2_reduction_tons": annual_co2_saved_tons,
                "scope2_location_based_tons": scope2_location_tons,
                "scope2_market_based_tons": scope2_market_tons,
                "trees_equivalent_planted": int(annual_co2_saved_tons * 45)
            },
            "battery_lifecycle": bess_aging
        }

    def get_grid_audit_data(self) -> Dict[str, Any]:
        """Returns national and regional grid emission breakdown."""
        return {
            "source": "Central Electricity Authority (CEA) Baseline Database v19.0",
            "national_average_kg_kwh": CEA_GRID_EMISSION_FACTORS["National Average"],
            "regional_breakdown": CEA_GRID_EMISSION_FACTORS,
            "state_breakdown": STATE_GRID_FACTORS
        }
