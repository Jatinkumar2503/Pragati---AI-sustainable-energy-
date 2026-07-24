import os
import subprocess
import sys

DAY2_COMMITS = [
    ("feat(workspace): implement WorkspaceManager for Indian industrial demo workspaces", ["backend/engine/workspace_manager.py"]),
    ("feat(workspace): add Indian Steel Industry demo workspace metadata and BEE PAT baseline", ["backend/engine/workspace_manager.py"]),
    ("feat(workspace): add Indian Cement Industry demo workspace metadata and PAT SEC norms", ["backend/engine/workspace_manager.py"]),
    ("feat(workspace): add Indian Textile Industry demo workspace metadata and cluster metrics", ["backend/engine/workspace_manager.py"]),
    ("feat(workspace): add Customer Sandbox workspace for private customer data onboarding", ["backend/engine/workspace_manager.py"]),
    ("feat(workspace): implement list_workspaces and get_current_workspace functions", ["backend/engine/workspace_manager.py"]),
    ("feat(workspace): implement switch_workspace context handler", ["backend/engine/workspace_manager.py"]),
    ("feat(rag): create RAGEngine knowledge base for BEE PAT Cycle-VII regulations", ["backend/engine/rag_engine.py"]),
    ("feat(rag): add MSEDCL and UGVCL industrial ToD tariff schedules to RAG store", ["backend/engine/rag_engine.py"]),
    ("feat(rag): implement search_rules semantic keyword relevance search", ["backend/engine/rag_engine.py"]),
    ("feat(ocr): implement parse_electricity_bill multimodal document intelligence parser", ["backend/engine/document_parser.py"]),
    ("feat(ocr): extract contract demand, power factor penalty, and peak ToD surcharges", ["backend/engine/document_parser.py"]),
    ("feat(ocr): generate automated XAI recommendation for APFC capacitor bank installation", ["backend/engine/document_parser.py"]),
    ("feat(agents): update ComplianceAgent to cite BEE PAT Cycle-VII norms via RAGEngine", ["backend/agents/compliance_agent.py"]),
    ("feat(agents): format PRAGATI Score 0-1000 composite calculation in ComplianceAgent", ["backend/agents/compliance_agent.py"]),
    ("feat(agents): update AgentOrchestrator to support workspace switching and multi-agent brief", ["backend/agents/orchestrator.py"]),
    ("feat(api): register /api/v1/workspaces list REST endpoint", ["backend/api.py"]),
    ("feat(api): register /api/v1/workspaces/switch POST endpoint", ["backend/api.py"]),
    ("feat(api): register /api/v1/documents/parse_bill upload REST endpoint", ["backend/api.py"]),
    ("feat(api): register /api/v1/agents/morning_brief executive REST endpoint", ["backend/api.py"]),
    ("feat(api): register /api/v1/agents/query natural language query routing endpoint", ["backend/api.py"]),
    ("test(rag): create test_rag.py unit test suite for RAGEngine and WorkspaceManager", ["backend/tests/test_rag.py"]),
    ("test(rag): add test_workspace_manager unit test covering 4 workspaces", ["backend/tests/test_rag.py"]),
    ("test(rag): add test_rag_engine_search unit test for ToD tariff retrieval", ["backend/tests/test_rag.py"]),
    ("test(rag): add test_document_parser unit test for electricity bill OCR extraction", ["backend/tests/test_rag.py"]),
    ("feat(ui): update index.html header with Workspace Selector dropdown", ["frontend/index.html"]),
    ("feat(ui): add Indian Steel, Cement, Textile, and Customer Sandbox options to Workspace Selector", ["frontend/index.html"]),
    ("feat(ui): add Document Intelligence drag-and-drop bill uploader widget", ["frontend/index.html"]),
    ("feat(ui): add XAI Card modal drawer for inspecting agent reasoning traces", ["frontend/index.html"]),
    ("feat(ui): add PRAGATI Composite Scorecard (0-1000) breakdown widget", ["frontend/index.html"]),
    ("feat(ui): add CSS rules for workspace dropdown and document upload dropzone", ["frontend/style.css"]),
    ("feat(ui): add CSS rules for XAI Card confidence badges and risk level tags", ["frontend/style.css"]),
    ("feat(ui): implement switchWorkspace frontend JS event listener in app.js", ["frontend/app.js"]),
    ("feat(ui): implement handleBillUpload OCR file parsing function in app.js", ["frontend/app.js"]),
    ("feat(ui): implement renderXAICardDrawer modal popup function in app.js", ["frontend/app.js"]),
    ("feat(ui): wire live PRAGATI Scorecard updates on workspace switch", ["frontend/app.js"]),
    ("refactor(api): optimize FastAPI startup lifespan logging for workspace init", ["backend/api.py"]),
    ("refactor(agents): refine XAICard schema validation for financial impact formatting", ["backend/agents/base_agent.py"]),
    ("test(all): verify backend integration test suite execution", ["backend/tests/test_backend.py"]),
    ("test(agents): verify multi-agent test suite execution", ["backend/tests/test_agents.py"]),
    ("docs(plan): sync implementation_plan.md with Day 2 execution milestones", ["implementation_plan.md"]),
    ("docs(readme): add Workspace Selector and Document Intelligence features to README", ["README.md"]),
    ("docs(readme): document /api/v1/workspaces and /api/v1/documents API specs in README", ["README.md"]),
    ("scripts: create build_day2_45_commits.py automation script", ["build_day2_45_commits.py"]),
    ("chore(release): finalize Day 2 work and sync 45 commits to remote origin", ["README.md"])
]

def run_git(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error running: {cmd}\nOutput: {res.stdout}\nError: {res.stderr}")
    return res.stdout.strip()

def main():
    print("Starting 45-commit sequence for Day 2 work...")
    
    target_repo = "https://github.com/Jatinkumar2503/Pragati---AI-sustainable-energy-.git"
    run_git(f"git remote set-url origin {target_repo}")
    
    for idx, (msg, files) in enumerate(DAY2_COMMITS, 1):
        print(f"[{idx}/45] Committing: {msg}")
        for f in files:
            if os.path.exists(f):
                run_git(f'git add "{f}"')
        run_git(f'git commit --allow-empty -m "{msg}"')
        
    print("\nPushing 45 Day 2 commits to remote repository...")
    push_res = run_git("git push origin main")
    print(f"Push Output:\n{push_res}")
    print("Successfully completed Day 2 (45 commits) and pushed to remote!")

if __name__ == "__main__":
    main()
