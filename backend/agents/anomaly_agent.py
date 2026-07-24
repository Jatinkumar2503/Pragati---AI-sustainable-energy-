from typing import Dict, Any, List
import pandas as pd
from .base_agent import BaseAgent, XAICard
from engine.anomaly_detector import run_anomaly_detection

class AnomalyAgent(BaseAgent):
    """
    Anomaly Agent: Monitors factory power consumption telemetry using unsupervised
    Isolation Forest models to flag idle power leaks, off-shift spikes, and power factor drops.
    """
    def __init__(self):
        super().__init__(
            name="Anomaly Agent",
            description="Detects anomalous energy consumption spikes and machinery left idling off-shift."
        )

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        df_sample = input_data.get("df_sample")
        self.log_step("start_anomaly_detection", {"sample_count": len(df_sample) if df_sample is not None else 0})
        
        if df_sample is None:
            # Fallback mock/sample structure if no DataFrame provided directly
            from engine.dataset_loader import load_dataset
            df_sample = load_dataset().head(1000)
            
        anomalies = run_anomaly_detection(df_sample)
        anomaly_count = len(anomalies)
        
        highest_severity = "LOW"
        if anomaly_count > 10:
            highest_severity = "HIGH"
        elif anomaly_count > 0:
            highest_severity = "MEDIUM"
            
        est_leak_kw = anomaly_count * 15.5
        est_monthly_savings = est_leak_kw * 720 * 8.5 # ₹8.5 / kWh industrial tariff
        
        xai_card = XAICard(
            agent_name=self.name,
            recommendation=f"Audit {anomaly_count} detected operational power anomalies and shut down idle sub-assemblies off-shift.",
            reasoning_why=f"Isolation Forest identified {anomaly_count} multivariate outlier timestamps where reactive power and active load diverged from baseline.",
            confidence_score=0.93,
            financial_impact_inr=f"Recovers estimated ₹{est_monthly_savings:,.0f}/month in leaked standby power",
            carbon_impact_kg=f"Reduces {int(est_leak_kw * 720 * 0.82)} kg CO2 emissions monthly",
            risk_level=highest_severity,
            human_approval_required=True,
            supporting_data={
                "anomaly_count": anomaly_count,
                "est_leak_kw": est_leak_kw,
                "contamination_rate": 0.04
            }
        )
        
        self.log_step("complete_anomaly_detection", {"anomaly_count": anomaly_count})
        return {
            "agent": self.name,
            "status": "success",
            "anomalies_found": anomaly_count,
            "anomalies": anomalies[:5], # top 5 sample
            "xai_card": xai_card.model_dump()
        }
