"""
PRAGATI AI — Real-time Telemetry Streaming & Threshold Alert Engine
Provides live meter stream simulation, over-voltage spikes, power factor drops,
3-phase current imbalance, and transformer thermal overload detectors.
"""

import time
import random
from typing import Dict, Any, List, Optional

class TelemetryStreamer:
    """
    Simulates high-frequency industrial telemetry streaming and manages
    active facility operational alerts.
    """
    def __init__(self):
        self.active_alerts: List[Dict[str, Any]] = [
            {
                "alert_id": "ALT-1001",
                "timestamp": "2026-07-25 12:45:00",
                "type": "Thermal Overload",
                "severity": "CRITICAL",
                "equipment": "Transformer T-02",
                "value": "94.2 °C",
                "threshold": "85.0 °C",
                "status": "TRIGGERED",
                "mitigation": "Engage secondary cooling fan bank and shed 50 kW auxiliary load."
            },
            {
                "alert_id": "ALT-1002",
                "timestamp": "2026-07-25 12:48:15",
                "type": "Power Factor Drop",
                "severity": "HIGH",
                "equipment": "Induction Motor Panel M-04",
                "value": "0.74 PF",
                "threshold": "0.90 PF",
                "status": "TRIGGERED",
                "mitigation": "Switch 75 kVAr APFC capacitor bank Step 3 to avoid DISCOM penalty."
            },
            {
                "alert_id": "ALT-1003",
                "timestamp": "2026-07-25 12:50:30",
                "type": "Phase Imbalance",
                "severity": "MEDIUM",
                "equipment": "Rolling Mill Line 1",
                "value": "8.4 %",
                "threshold": "5.0 %",
                "status": "TRIGGERED",
                "mitigation": "Rebalance single-phase lighting auxiliary loads across R-Y-B phases."
            }
        ]

    def get_live_telemetry(self) -> Dict[str, Any]:
        """
        Generates simulated real-time telemetry stream reading.
        """
        base_kw = 245.0 + random.uniform(-15.0, 20.0)
        voltage = 415.0 + random.uniform(-5.0, 8.0)
        pf = round(min(0.99, max(0.70, 0.92 + random.uniform(-0.05, 0.04))), 2)
        current_r = round(base_kw * 1.5 + random.uniform(-10, 10), 1)
        current_y = round(base_kw * 1.5 + random.uniform(-10, 10), 1)
        current_b = round(base_kw * 1.5 + random.uniform(-10, 10), 1)
        temp_c = round(65.0 + (base_kw / 10.0) + random.uniform(-2.0, 3.0), 1)

        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "active_load_kw": round(base_kw, 2),
            "grid_voltage_v": round(voltage, 1),
            "power_factor": pf,
            "phase_currents_a": {
                "r_phase": current_r,
                "y_phase": current_y,
                "b_phase": current_b
            },
            "transformer_temp_c": temp_c,
            "meter_status": "ONLINE"
        }

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Returns list of active triggered alerts."""
        return [a for a in self.active_alerts if a["status"] in ("TRIGGERED", "ACKNOWLEDGED")]

    def acknowledge_alert(self, alert_id: str, operator_name: str = "Operator") -> Dict[str, Any]:
        """
        Acknowledges an alert by ID.
        """
        for alert in self.active_alerts:
            if alert["alert_id"] == alert_id:
                alert["status"] = "ACKNOWLEDGED"
                alert["acknowledged_by"] = operator_name
                alert["acknowledged_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                return {"status": "success", "alert": alert}
        return {"status": "error", "message": f"Alert ID {alert_id} not found."}

# Singleton instance
telemetry_streamer = TelemetryStreamer()
