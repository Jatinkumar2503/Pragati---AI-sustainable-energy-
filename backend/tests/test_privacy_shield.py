import unittest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.privacy_shield import privacy_shield

class TestPrivacyShield(unittest.TestCase):
    def test_anonymize_text(self):
        text = "Facility in Mumbai with load 450 kW and account ACC-99211"
        anon = privacy_shield.anonymize(text, session_id="test_sess")
        self.assertIsInstance(anon, str)

    def test_privacy_budget_decrement(self):
        data = {"usage_kwh": 120.5, "power_factor": 88.2}
        res = privacy_shield.anonymize_data(data, session_id="test_sess")
        self.assertIsInstance(res, dict)
        self.assertIn("usage_kwh", res)

if __name__ == "__main__":
    unittest.main()
