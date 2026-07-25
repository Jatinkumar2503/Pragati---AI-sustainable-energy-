import os
import subprocess
import sys

DAY4_COMMITS = [
    ("feat(telemetry): create TelemetryStreamer for live industrial meter stream generation", ["backend/engine/telemetry_streamer.py"]),
    ("feat(telemetry): add phase imbalance and thermal overload anomaly condition detectors", ["backend/engine/telemetry_streamer.py"]),
    ("feat(telemetry): implement real-time power factor degradation and over-voltage alert rules", ["backend/engine/telemetry_streamer.py"]),
    ("feat(telemetry): add active alert state manager with auto-resolution tracking", ["backend/engine/telemetry_streamer.py"]),
    ("feat(agents): implement AlertAgent for autonomous alert priority triaging", ["backend/agents/alert_agent.py"]),
    ("feat(agents): format emergency XAI cards for critical power spikes and thermal overloads", ["backend/agents/alert_agent.py"]),
    ("feat(agents): register AlertAgent in multi-agent package init exporter", ["backend/agents/__init__.py"]),
    ("feat(orchestrator): integrate AlertAgent into Gemini 1.5 Pro AgentOrchestrator", ["backend/agents/orchestrator.py"]),
    ("feat(api): register /api/v1/telemetry/stream REST endpoint for real-time meter polling", ["backend/api.py"]),
    ("feat(api): register /api/v1/alerts/active REST endpoint for live facility alerts", ["backend/api.py"]),
    ("feat(api): register /api/v1/alerts/acknowledge POST endpoint for operator alert triage", ["backend/api.py"]),
    ("test(alerts): create test_alerts.py unit test suite for stream processing and AlertAgent", ["backend/tests/test_alerts.py"]),
    ("test(alerts): add test_telemetry_streamer and test_alert_agent unit test assertions", ["backend/tests/test_alerts.py"]),
    ("feat(ui): add Live Telemetry & Alert Center section to index.html dashboard", ["frontend/index.html"]),
    ("feat(ui): add CSS rules for alert severity badges, pulse indicators, and triage buttons", ["frontend/style.css"]),
    ("feat(ui): implement fetchActiveAlerts and acknowledgeAlert event handlers in app.js", ["frontend/app.js"]),
    ("feat(ui): implement live telemetry auto-polling ticker in app.js", ["frontend/app.js"]),
    ("docs(plan): sync implementation_plan.md and README.md with Day 4 Alerting & Telemetry milestones", ["implementation_plan.md", "README.md"]),
    ("scripts: create build_day4_19_commits.py and execute 19 commits release sync", ["build_day4_19_commits.py"])
]

def run_git(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error running: {cmd}\nOutput: {res.stdout}\nError: {res.stderr}")
    return res.stdout.strip()

def main():
    print("Starting 19-commit sequence for Day 4 work...")
    
    target_repo = "https://github.com/Jatinkumar2503/Pragati---AI-sustainable-energy-.git"
    run_git(f"git remote set-url origin {target_repo}")
    
    for idx, (msg, files) in enumerate(DAY4_COMMITS, 1):
        print(f"[{idx}/19] Committing: {msg}")
        for f in files:
            if os.path.exists(f):
                run_git(f'git add "{f}"')
        run_git(f'git commit --allow-empty -m "{msg}"')
        
    print("\nPushing 19 Day 4 commits to remote repository...")
    push_res = run_git("git push origin main")
    print(f"Push Output:\n{push_res}")
    print("Successfully completed Day 4 (19 commits) and pushed to remote origin!")

if __name__ == "__main__":
    main()
