import unittest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.scheduler import optimize_shift_schedule, get_tariff, get_carbon_intensity

class TestScheduler(unittest.TestCase):
    def test_get_tariff(self):
        # 14:00 is Peak business hours ($0.18)
        self.assertEqual(get_tariff(14), 0.18)
        # 03:00 is Off-peak ($0.06)
        self.assertEqual(get_tariff(3), 0.06)

    def test_get_carbon_intensity(self):
        intensity = get_carbon_intensity(12)
        self.assertGreater(intensity, 0.0)

    def test_optimize_shift_schedule(self):
        res = optimize_shift_schedule(task_load_kw=100.0, task_duration_h=4, solar_capacity_kw=150.0)
        self.assertIsInstance(res, dict)
        self.assertIn("best_start_hour", res)
        self.assertIn("savings", res)
        self.assertIn("best_hourly_details", res)
        self.assertIn("baseline", res)

if __name__ == "__main__":
    unittest.main()
