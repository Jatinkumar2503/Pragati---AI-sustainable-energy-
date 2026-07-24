import unittest
import sys
import os

# Ensure backend folder is in path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, XAICard
from agents.forecast_agent import ForecastAgent
from agents.anomaly_agent import AnomalyAgent
from agents.optimization_agent import OptimizationAgent
from agents.compliance_agent import ComplianceAgent
from agents.orchestrator import AgentOrchestrator

class TestMultiAgentFramework(unittest.TestCase):
    
    def test_xai_card_validation(self):
        card = XAICard(
            agent_name="TestAgent",
            recommendation="Test directive",
            reasoning_why="Test root cause",
            confidence_score=0.95,
            financial_impact_inr="₹10,000 savings",
            carbon_impact_kg="250 kg CO2",
            risk_level="LOW",
            human_approval_required=True
        )
        self.assertEqual(card.confidence_score, 0.95)
        self.assertTrue(card.human_approval_required)
        
    def test_forecast_agent(self):
        agent = ForecastAgent()
        res = agent.run({"hours": 24})
        self.assertEqual(res["status"], "success")
        self.assertIn("xai_card", res)
        self.assertEqual(res["xai_card"]["agent_name"], "Forecast Agent")
        
    def test_anomaly_agent(self):
        agent = AnomalyAgent()
        res = agent.run({})
        self.assertEqual(res["status"], "success")
        self.assertIn("anomalies_found", res)
        self.assertEqual(res["xai_card"]["agent_name"], "Anomaly Agent")
        
    def test_optimization_agent(self):
        agent = OptimizationAgent()
        res = agent.run({"task_load_kw": 100.0, "duration_hours": 2})
        self.assertEqual(res["status"], "success")
        self.assertIn("schedule", res)
        self.assertEqual(res["xai_card"]["agent_name"], "Optimization Agent")
        
    def test_compliance_agent(self):
        agent = ComplianceAgent()
        res = agent.run({"sector": "Steel"})
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(res["pragati_score_1000"], 0)
        self.assertLessEqual(res["pragati_score_1000"], 1000)
        
    def test_orchestrator_morning_brief(self):
        orchestrator = AgentOrchestrator()
        brief = orchestrator.generate_morning_brief("Steel")
        self.assertEqual(brief["status"], "success")
        self.assertIn("approval_queue", brief)
        self.assertGreaterEqual(len(brief["approval_queue"]), 2)

if __name__ == "__main__":
    unittest.main()
