import unittest
import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.forecaster import generate_forecast

class TestForecast(unittest.TestCase):
    def setUp(self):
        dates = pd.date_range(start="2026-01-01", periods=200, freq="1h")
        self.df = pd.DataFrame({
            "date": dates,
            "usage_kwh": 100.0 + 20.0 * np.sin(np.linspace(0, 10, 200)) + np.random.normal(0, 5, 200)
        })

    def test_generate_forecast(self):
        res = generate_forecast(self.df, forecast_hours=24, backtest_folds=2)
        self.assertIsInstance(res, dict)
        self.assertIn("forecast", res)
        self.assertIn("validation_rmse", res)

if __name__ == "__main__":
    unittest.main()
