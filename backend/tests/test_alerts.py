"""
Unit tests for TelemetryStreamer and AlertAgent.
"""

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.telemetry_streamer import TelemetryStreamer
from agents.alert_agent import AlertAgent

class TestAlerts(unittest.TestCase):

    def setUp(self):
        self.streamer = TelemetryStreamer()

    def test_telemetry_streamer(self):
        stream = self.streamer.get_live_telemetry()
        self.assertIn("active_load_kw", stream)
        self.assertIn("grid_voltage_v", stream)
        self.assertIn("power_factor", stream)
        self.assertIn("phase_currents_a", stream)
        self.assertEqual(stream["meter_status"], "ONLINE")

    def test_active_alerts(self):
        alerts = self.streamer.get_active_alerts()
        self.assertGreater(len(alerts), 0)
        self.assertIn(alerts[0]["status"], ("TRIGGERED", "ACKNOWLEDGED"))

    def test_acknowledge_alert(self):
        alerts = self.streamer.get_active_alerts()
        alert_id = alerts[0]["alert_id"]
        res = self.streamer.acknowledge_alert(alert_id, "Rajesh Engineer")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["alert"]["status"], "ACKNOWLEDGED")

    def test_alert_agent(self):
        agent = AlertAgent()
        out = agent.run({})
        self.assertEqual(out["agent"], "AlertAgent")
        self.assertIn("xai_card", out)
        self.assertEqual(out["xai_card"]["agent_name"], "AlertAgent")

if __name__ == "__main__":
    unittest.main()
