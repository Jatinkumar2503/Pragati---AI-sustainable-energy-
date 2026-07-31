import unittest
import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.anomaly_detector import run_anomaly_detection

class TestAnomalies(unittest.TestCase):
    def setUp(self):
        dates = pd.date_range(start="2026-01-01", periods=100, freq="15min")
        self.df = pd.DataFrame({
            "date": dates,
            "usage_kwh": np.random.uniform(50, 150, 100),
            "reactive_lagging_kvarh": np.random.uniform(10, 40, 100),
            "reactive_leading_kvarh": np.random.uniform(5, 20, 100),
            "power_factor_lagging": np.random.uniform(75, 95, 100),
            "load_type": ["Medium_Load"] * 100,
            "week_status": ["Weekday"] * 100,
            "day_of_week": ["Monday"] * 100
        })
        
        # Inject an anomaly spike
        self.df.loc[10, "usage_kwh"] = 500.0

    def test_run_anomaly_detection(self):
        anomalies = run_anomaly_detection(self.df, contamination=0.05)
        self.assertIsInstance(anomalies, list)
        self.assertGreater(len(anomalies), 0)
        
        # Verify schema keys
        first = anomalies[0]
        self.assertIn("timestamp", first)
        self.assertIn("usage_kwh", first)
        self.assertIn("anomaly_type", first)
        self.assertIn("severity", first)
        self.assertIn("explanation", first)
        self.assertIn("recommendation", first)

if __name__ == "__main__":
    unittest.main()
