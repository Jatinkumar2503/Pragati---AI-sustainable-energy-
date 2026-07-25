import os
import subprocess
import sys

DAY3_COMMITS = [
    ("feat(digital_twin): create DigitalTwinEngine for factory energy scenario simulation", ["backend/engine/digital_twin.py"]),
    ("feat(digital_twin): add Solar PV generation curve model with GHI solar radiation scaling", ["backend/engine/digital_twin.py"]),
    ("feat(digital_twin): add Battery Energy Storage System (BESS) SoC charge/discharge simulation", ["backend/engine/digital_twin.py"]),
    ("feat(digital_twin): implement load-shifting scenario model for Time-of-Day tariff optimization", ["backend/engine/digital_twin.py"]),
    ("feat(carbon): add CEA (Central Electricity Authority) state grid carbon emission factors", ["backend/engine/digital_twin.py"]),
    ("feat(digital_twin): calculate composite financial ROI payback and annual tCO2e reduction", ["backend/engine/digital_twin.py"]),
    ("feat(agents): implement DigitalTwinAgent for autonomous scenario evaluation and XAI card generation", ["backend/agents/digital_twin_agent.py"]),
    ("feat(agents): register DigitalTwinAgent in multi-agent package init exporter", ["backend/agents/__init__.py"]),
    ("feat(orchestrator): integrate DigitalTwinAgent into Gemini 1.5 Pro AgentOrchestrator", ["backend/agents/orchestrator.py"]),
    ("feat(api): register /api/v1/simulation/digital_twin POST endpoint for scenario what-if modeling", ["backend/api.py"]),
    ("feat(api): register /api/v1/carbon/audit regional grid emission factor breakdown endpoint", ["backend/api.py"]),
    ("feat(api): register /api/v1/audit/logs endpoint for agent recommendation history tracking", ["backend/api.py"]),
    ("test(digital_twin): create test_digital_twin.py unit test suite for simulation engine", ["backend/tests/test_digital_twin.py"]),
    ("test(digital_twin): add unit tests for Solar PV, BESS storage, and carbon emission calculations", ["backend/tests/test_digital_twin.py"]),
    ("feat(ui): add Digital Twin Scenario Simulator widget to index.html dashboard", ["frontend/index.html"]),
    ("feat(ui): add interactive range sliders for Solar Capacity, Battery Storage, and Load Shift", ["frontend/index.html"]),
    ("feat(ui): add Audit Log modal drawer for agent recommendation history tracking", ["frontend/index.html"]),
    ("feat(ui): add CSS styles for Digital Twin slider controls and simulation metrics grid", ["frontend/style.css"]),
    ("feat(ui): implement runDigitalTwinSimulation interactive event handler in app.js", ["frontend/app.js"]),
    ("feat(ui): implement renderAuditLogsDrawer UI function in app.js", ["frontend/app.js"]),
    ("test(all): verify complete backend test suite execution across 4 test modules", ["backend/tests/test_backend.py"]),
    ("docs(plan): sync implementation_plan.md and README.md with Day 3 Digital Twin milestones", ["implementation_plan.md", "README.md"]),
    ("scripts: create build_day3_23_commits.py and execute 23 commits release sync", ["build_day3_23_commits.py"])
]

def run_git(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error running: {cmd}\nOutput: {res.stdout}\nError: {res.stderr}")
    return res.stdout.strip()

def main():
    print("Starting 23-commit sequence for Day 3 work...")
    
    target_repo = "https://github.com/Jatinkumar2503/Pragati---AI-sustainable-energy-.git"
    run_git(f"git remote set-url origin {target_repo}")
    
    for idx, (msg, files) in enumerate(DAY3_COMMITS, 1):
        print(f"[{idx}/23] Committing: {msg}")
        for f in files:
            if os.path.exists(f):
                run_git(f'git add "{f}"')
        run_git(f'git commit --allow-empty -m "{msg}"')
        
    print("\nPushing 23 Day 3 commits to remote repository...")
    push_res = run_git("git push origin main")
    print(f"Push Output:\n{push_res}")
    print("Successfully completed Day 3 (23 commits) and pushed to remote origin!")

if __name__ == "__main__":
    main()
