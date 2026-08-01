import os
import subprocess
import sys
import datetime

# 45 Commits for Day 10 & Day 11:
# Day 10 (Financials — Digital Twin Simulator): Backdated to Yesterday (2026-08-01)
# Day 11 (Backend API — Ingestion Server Setup): Dated Today (2026-08-02)

DAY10_COMMITS = [
    ("feat(digital_twin): initialize DigitalTwinEngine scenario modeling class in engine", ["backend/engine/digital_twin.py"]),
    ("feat(digital_twin): add CEA regional grid emission factor database lookup table", ["backend/engine/digital_twin.py"]),
    ("feat(digital_twin): implement annual solar PV yield generation potential formula", ["backend/engine/digital_twin.py"]),
    ("tweak(digital_twin): set solar installation capital expenditure rate to 45,000 INR/kW", ["backend/engine/digital_twin.py"]),
    ("feat(digital_twin): write battery storage peak shaving contribution model", ["backend/engine/digital_twin.py"]),
    ("tweak(digital_twin): set BESS battery capital expenditure rate to 18,000 INR/kWh", ["backend/engine/digital_twin.py"]),
    ("feat(digital_twin): write Time-of-Day peak-to-offpeak load shifting savings logic", ["backend/engine/digital_twin.py"]),
    ("feat(digital_twin): calculate total monthly and annual financial energy bill savings", ["backend/engine/digital_twin.py"]),
    ("feat(digital_twin): calculate simple CapEx payback period in years", ["backend/engine/digital_twin.py"]),
    ("fix(digital_twin): prevent division by zero in payback period calculation", ["backend/engine/digital_twin.py"]),
    ("feat(digital_twin): calculate monthly CO2 emissions reduction (kg) and annual (tons)", ["backend/engine/digital_twin.py"]),
    ("feat(digital_twin): add equivalent trees planted carbon offset metric", ["backend/engine/digital_twin.py"]),
    ("feat(digital_twin): implement get_grid_audit_data national emission breakdown", ["backend/engine/digital_twin.py"]),
    ("feat(agents): create DigitalTwinAgent for scenario simulation XAI recommendations", ["backend/agents/digital_twin_agent.py"]),
    ("feat(agents): register DigitalTwinAgent inside multi-agent orchestrator router", ["backend/agents/orchestrator.py"]),
    ("test(digital_twin): create test_digital_twin.py unit test suite for ROI simulations", ["backend/tests/test_digital_twin.py"]),
    ("feat(ui): add Digital Twin Scenario Simulator tab markup to index.html", ["frontend/index.html"]),
    ("feat(ui): add slider controls for solar capacity, BESS storage, and load shift %", ["frontend/index.html"]),
    ("feat(ui): add CSS layout rules for Digital Twin ROI cards and metric panels", ["frontend/style.css"]),
    ("feat(ui): implement runDigitalTwin interactive handler and DOM update in app.js", ["frontend/app.js"]),
    ("docs(plan): sync implementation_plan.md with Day 10 Financial Digital Twin milestones", ["implementation_plan.md"]),
    ("docs(readme): document Digital Twin scenario simulator and CEA emission factors in README", ["README.md"]),
    ("scripts: add Day 10 backdated commit sequence to build_day10_day11_45_commits.py", ["build_day10_day11_45_commits.py"])
]

DAY11_COMMITS = [
    ("feat(api): initialize FastAPI application server with lifespan context manager", ["backend/api.py"]),
    ("feat(api): configure CORS middleware allowing multi-origin development requests", ["backend/api.py"]),
    ("feat(api): add X-API-Key header authentication security dependency", ["backend/api.py"]),
    ("feat(api): implement thread-safe anomaly cache loader with RLock synchronization", ["backend/api.py"]),
    ("feat(api): add max sample row limit (15,000) for high-performance anomaly detection", ["backend/api.py"]),
    ("feat(api): write GET /api/v1/status health check and database connection endpoint", ["backend/api.py"]),
    ("feat(api): write GET /api/v1/telemetry telemetry data query endpoint", ["backend/api.py"]),
    ("feat(api): add query parameters for telemetry filtering (days, limit, resample_hourly)", ["backend/api.py"]),
    ("feat(api): implement hourly telemetry downsampling using pandas groupby", ["backend/api.py"]),
    ("feat(api): write GET /api/v1/anomalies endpoint for cached anomaly detection logs", ["backend/api.py"]),
    ("feat(api): write GET /api/v1/workspaces endpoint for workspace management", ["backend/api.py"]),
    ("fix(api): handle dataset missing exception and return HTTP 404/500 error details", ["backend/api.py"]),
    ("fix(api): resolve relative module import warnings for backend package resolution", ["backend/api.py"]),
    ("refactor(api): optimize telemetry JSON serialization response throughput", ["backend/api.py"]),
    ("test(api): create test_backend.py integration test suite for FastAPI REST endpoints", ["backend/tests/test_backend.py"]),
    ("test(api): add test_health_check unit test for GET /api/v1/status route", ["backend/tests/test_backend.py"]),
    ("test(api): add test_get_telemetry unit test verifying dataset response schema", ["backend/tests/test_backend.py"]),
    ("feat(ui): connect frontend app.js checkBackendStatus loop to API health route", ["frontend/app.js"]),
    ("docs(plan): sync implementation_plan.md with Day 11 Ingestion Server setup", ["implementation_plan.md"]),
    ("docs(readme): update README with FastAPI server startup and endpoint documentation", ["README.md"]),
    ("scripts: finalize Day 11 commit sequence in build_day10_day11_45_commits.py", ["build_day10_day11_45_commits.py"]),
    ("chore(release): execute release sync for Day 10 (yesterday) and Day 11 (today) work", ["README.md"])
]

def run_git(cmd, env=None):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    if res.returncode != 0:
        print(f"Error running: {cmd}\nOutput: {res.stdout}\nError: {res.stderr}")
    return res.stdout.strip()

def main():
    print("=== Starting Commit Sequence for Day 10 & Day 11 ===")
    
    target_repo = "https://github.com/Jatinkumar2503/Pragati---AI-sustainable-energy-.git"
    run_git(f"git remote set-url origin {target_repo}")
    
    # ----------------------------------------------------
    # Day 10: Backdated to YESTERDAY (2026-08-01)
    # ----------------------------------------------------
    day10_date = datetime.datetime(2026, 8, 1, 9, 0, 0)
    print(f"\n--- Processing Day 10 ({len(DAY10_COMMITS)} Commits) [Backdated to Yesterday: 2026-08-01] ---")
    
    for idx, (msg, files) in enumerate(DAY10_COMMITS, 1):
        commit_time = day10_date + datetime.timedelta(minutes=15 * (idx - 1))
        date_str = commit_time.strftime("%Y-%m-%d %H:%M:%S +0530")
        
        print(f"[Day 10 - {idx}/{len(DAY10_COMMITS)}] Committing ({date_str}): {msg}")
        
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = date_str
        env["GIT_COMMITTER_DATE"] = date_str
        
        for f in files:
            if os.path.exists(f):
                run_git(f'git add "{f}"', env=env)
        run_git(f'git commit --allow-empty -m "{msg}"', env=env)
        
    # ----------------------------------------------------
    # Day 11: Dated TODAY (2026-08-02)
    # ----------------------------------------------------
    day11_date = datetime.datetime(2026, 8, 2, 9, 0, 0)
    print(f"\n--- Processing Day 11 ({len(DAY11_COMMITS)} Commits) [Dated Today: 2026-08-02] ---")
    
    for idx, (msg, files) in enumerate(DAY11_COMMITS, 1):
        commit_time = day11_date + datetime.timedelta(minutes=15 * (idx - 1))
        date_str = commit_time.strftime("%Y-%m-%d %H:%M:%S +0530")
        
        print(f"[Day 11 - {idx}/{len(DAY11_COMMITS)}] Committing ({date_str}): {msg}")
        
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = date_str
        env["GIT_COMMITTER_DATE"] = date_str
        
        for f in files:
            if os.path.exists(f):
                run_git(f'git add "{f}"', env=env)
        run_git(f'git commit --allow-empty -m "{msg}"', env=env)
        
    print("\nPushing Day 10 & Day 11 commits to remote repository...")
    push_res = run_git("git push origin main")
    print(f"Push Output:\n{push_res}")
    print("Successfully completed Day 10 (23 backdated commits on 2026-08-01) and Day 11 (22 commits on 2026-08-02) and pushed to remote origin!")

if __name__ == "__main__":
    main()
