import unittest
import sys
import os

# Ensure backend folder is in path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.rag_engine import rag_engine
from engine.document_parser import parse_electricity_bill
from engine.workspace_manager import list_workspaces, get_current_workspace, switch_workspace

class TestRAGAndWorkspaceManager(unittest.TestCase):

    def test_workspace_manager(self):
        workspaces = list_workspaces()
        self.assertEqual(len(workspaces), 4)
        
        current = get_current_workspace()
        self.assertEqual(current["id"], "indian_steel")
        
        switched = switch_workspace("indian_cement")
        self.assertEqual(switched["id"], "indian_cement")
        self.assertEqual(switched["sector"], "Cement")
        
        # Reset back to steel
        switch_workspace("indian_steel")

    def test_rag_engine_search(self):
        results = rag_engine.search_rules("tariff", category="Tariff")
        self.assertGreater(len(results), 0)
        self.assertIn("MSEDCL", results[0]["title"])

    def test_document_parser(self):
        mock_bytes = b"Sample electricity bill content"
        parsed = parse_electricity_bill(mock_bytes, "Steel_Utility_Bill_May2026.pdf")
        self.assertEqual(parsed["status"], "success")
        self.assertIn("extracted_data", parsed)
        self.assertEqual(parsed["extracted_data"]["contract_demand_kva"], 1500.0)

if __name__ == "__main__":
    unittest.main()
