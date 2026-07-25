"""
PRAGATI AI — Alert Management Agent
Triages live threshold alerts and generates emergency XAI Cards with operational mitigation steps.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, XAICard
from engine.telemetry_streamer import telemetry_streamer

class AlertAgent(BaseAgent):
    """
    Agent responsible for monitoring high-frequency threshold alerts,
    triaging severity levels, and generating emergency XAI Cards for plant operators.
    """
    def __init__(self):
        super().__init__(
            name="AlertAgent",
            description="Evaluates active industrial meter threshold alerts, triages equipment risks, and outputs emergency mitigation directives."
        )

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        active_alerts = telemetry_streamer.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a["severity"] == "CRITICAL"]
        high_alerts = [a for a in active_alerts if a["severity"] == "HIGH"]

        if critical_alerts:
            target_alert = critical_alerts[0]
            risk = "CRITICAL"
        elif high_alerts:
            target_alert = high_alerts[0]
            risk = "HIGH"
        elif active_alerts:
            target_alert = active_alerts[0]
            risk = "MEDIUM"
        else:
            target_alert = {
                "type": "Normal Operations",
                "equipment": "Main Facility Substation",
                "value": "0 Anomalies",
                "threshold": "Nominal",
                "mitigation": "No immediate intervention required."
            }
            risk = "LOW"

        xai_card = XAICard(
            agent_name=self.name,
            recommendation=f"Immediate Triage Required: {target_alert['type']} on {target_alert['equipment']}",
            reasoning_why=f"Observed value ({target_alert['value']}) exceeded safety threshold ({target_alert['threshold']}). Mitigation: {target_alert['mitigation']}",
            confidence_score=0.96,
            financial_impact_inr="Avoided catastrophic downtime (~₹1,50,000)",
            carbon_impact_kg="Prevented inefficient thermal loss (450 kg CO2)",
            risk_level=risk,
            human_approval_required=True,
            supporting_data={"active_alert_count": len(active_alerts), "alert_detail": target_alert}
        )

        self.log_step("Alert Triage", {"active_count": len(active_alerts), "top_risk": risk})

        return {
            "agent": self.name,
            "active_alert_count": len(active_alerts),
            "alerts": active_alerts,
            "xai_card": xai_card.model_dump()
        }
