"""
PRAGATI AI — Digital Twin Agent
Evaluates scenario options (Solar PV, BESS, Load Shifting) and generates XAI Cards.
"""

from typing import Dict, Any
from .base_agent import BaseAgent, XAICard
from engine.digital_twin import DigitalTwinEngine

class DigitalTwinAgent(BaseAgent):
    """
    Agent responsible for running digital twin scenario analysis
    and generating actionable XAI Cards for energy optimization investments.
    """
    def __init__(self):
        super().__init__(
            name="DigitalTwinAgent",
            description="Simulates Solar PV, BESS Battery, and Load Shifting scenarios with financial and carbon ROI projections."
        )

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        region = input_data.get("region", "Western")
        base_monthly_kwh = float(input_data.get("base_monthly_kwh", 150000.0))
        solar_capacity_kw = float(input_data.get("solar_capacity_kw", 250.0))
        battery_storage_kwh = float(input_data.get("battery_storage_kwh", 100.0))
        load_shift_pct = float(input_data.get("load_shift_pct", 20.0))

        engine = DigitalTwinEngine(region=region)
        sim_results = engine.simulate_scenario(
            base_monthly_kwh=base_monthly_kwh,
            solar_capacity_kw=solar_capacity_kw,
            battery_storage_kwh=battery_storage_kwh,
            load_shift_pct=load_shift_pct
        )

        fin = sim_results["financial_metrics"]
        carb = sim_results["carbon_metrics"]

        xai_card = XAICard(
            agent_name=self.name,
            recommendation=f"Deploy {solar_capacity_kw} kW Solar PV + {battery_storage_kwh} kWh BESS with {load_shift_pct}% Peak Load Shifting",
            reasoning_why=f"Simulation in {region} grid zone reduces peak grid draw, saving ₹{fin['monthly_savings_inr']:,.2f}/mo with a payback of {fin['payback_period_years']} years.",
            confidence_score=0.93,
            financial_impact_inr=f"₹{fin['annual_savings_inr']:,.2f} / year savings",
            carbon_impact_kg=f"{carb['monthly_co2_reduction_kg']:,.2f} kg CO2/mo offset ({carb['annual_co2_reduction_tons']} tons/yr)",
            risk_level="LOW",
            human_approval_required=True,
            supporting_data=sim_results
        )

        self.log_step("Scenario Simulation", {"region": region, "annual_savings_inr": fin["annual_savings_inr"]})

        return {
            "agent": self.name,
            "simulation": sim_results,
            "xai_card": xai_card.model_dump()
        }
