"""
PRAGATI AI — Digital Twin Scenario Simulation & Carbon Analytics Engine
Provides physical modeling for Solar PV, BESS Battery Storage, Load Shifting, and CEA Grid Emission Factors.
"""

import math
from typing import Dict, Any, List

# Central Electricity Authority (CEA) CO2 Baseline Database for Indian Power Sector (kg CO2/kWh)
CEA_GRID_EMISSION_FACTORS = {
    "Northern": 0.71,
    "Western": 0.79,
    "Southern": 0.68,
    "Eastern": 0.85,
    "North-Eastern": 0.62,
    "National Average": 0.73
}

class DigitalTwinEngine:
    """
    Digital Twin Engine for factory energy scenario simulation.
    Models Solar PV generation, BESS battery charging/discharging,
    Time-of-Day load shifting, and Scope 1/2 carbon reductions.
    """
    def __init__(self, region: str = "Western"):
        self.region = region
        self.grid_factor = CEA_GRID_EMISSION_FACTORS.get(region, 0.73)
        self.solar_cost_per_kw = 45000.0  # INR per kW installed solar
        self.bess_cost_per_kwh = 18000.0  # INR per kWh installed BESS
        self.peak_tariff_rate = 11.50     # INR per kWh peak ToD tariff
        self.offpeak_tariff_rate = 6.20   # INR per kWh offpeak ToD tariff
        
    def simulate_scenario(
        self,
        base_monthly_kwh: float,
        solar_capacity_kw: float,
        battery_storage_kwh: float,
        load_shift_pct: float
    ) -> Dict[str, Any]:
        """
        Runs digital twin physics simulation based on user inputs.
        """
        # 1. Solar Generation Estimate (Avg 4.5 kWh/kW/day in India)
        daily_solar_kwh = solar_capacity_kw * 4.5
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
        
        # 5. Carbon Offset Calculations
        # Total clean energy / offset kWh
        total_offset_kwh_monthly = monthly_solar_kwh + monthly_battery_kwh
        monthly_co2_saved_kg = total_offset_kwh_monthly * self.grid_factor
        annual_co2_saved_tons = round((monthly_co2_saved_kg * 12.0) / 1000.0, 2)
        
        # New net grid consumption
        net_monthly_kwh = max(0.0, base_monthly_kwh - monthly_solar_kwh)
        
        return {
            "region": self.region,
            "grid_emission_factor_kg_kwh": self.grid_factor,
            "inputs": {
                "base_monthly_kwh": base_monthly_kwh,
                "solar_capacity_kw": solar_capacity_kw,
                "battery_storage_kwh": battery_storage_kwh,
                "load_shift_pct": load_shift_pct
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
                "trees_equivalent_planted": int(annual_co2_saved_tons * 45)
            }
        }

    def get_grid_audit_data(self) -> Dict[str, Any]:
        """Returns national and regional grid emission breakdown."""
        return {
            "source": "Central Electricity Authority (CEA) Baseline Database v19.0",
            "national_average_kg_kwh": CEA_GRID_EMISSION_FACTORS["National Average"],
            "regional_breakdown": CEA_GRID_EMISSION_FACTORS
        }
