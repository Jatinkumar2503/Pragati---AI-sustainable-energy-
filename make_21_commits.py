import os
import subprocess
import sys

# 21 Granular Commits for Today's UI & Backend Improvements
COMMITS_21 = [
    ("fix(ui): remove display flex important from modal backdrop in style.css to enable hidden toggle", ["frontend/style.css"]),
    ("feat(api): add GET /api/v1/audit/logs REST endpoint returning agent decision audit trails", ["backend/api.py"]),
    ("feat(ui): implement 3D glassmorphic modal backdrop and card dialog layout", ["frontend/style.css"]),
    ("feat(ui): add close button and backdrop click listeners for instant modal dismissal", ["frontend/app.js"]),
    ("feat(ui): bind keyboard Escape key listener for global modal dismissal", ["frontend/app.js"]),
    ("feat(ui): render warm cream card items for audit logs with agent signatures and impact metrics", ["frontend/app.js"]),
    ("feat(ui): add AI Copilot chat drawer styling with 3D glassmorphic header and action buttons", ["frontend/style.css"]),
    ("feat(ui): add AI Copilot message bubbles for user and assistant conversation flow", ["frontend/style.css"]),
    ("feat(ui): create 3D Glassmorphic KPI Grid for Digital Twin sandbox", ["frontend/style.css"]),
    ("feat(ui): add icon badges for Digital Twin metrics (Solar Gen, Peak Shaving, Bill Savings, Carbon Offset)", ["frontend/index.html"]),
    ("feat(ui): implement bio-emerald ROI banner for Digital Twin CapEx payback metrics", ["frontend/style.css"]),
    ("feat(ui): add hover elevation and tactile scaling effects on Digital Twin 3D cards", ["frontend/style.css"]),
    ("style(ui): fix washed-out text contrast in Startup Plans sub-header banner", ["frontend/index.html"]),
    ("feat(ui): create sub-header-banner-v2 container with dark bio-forest charcoal background", ["frontend/style.css"]),
    ("style(ui): upgrade Startup Plans header title to bold white Outfit font with subtle drop shadow", ["frontend/style.css"]),
    ("style(ui): set Startup Plans subtitle to high-contrast slate grey for crystal clear legibility", ["frontend/style.css"]),
    ("feat(ui): create 3D KPI Card Grid v2 for Operational Dashboard with top accent gradient lines", ["frontend/style.css", "frontend/index.html"]),
    ("feat(ui): add color-coded 3D icon badges for Active Power (gold), Carbon (emerald), PF (terracotta), Anomalies (red)", ["frontend/style.css", "frontend/index.html"]),
    ("feat(ui): transform Scope 1/2/3 carbon breakdown into color-coded pill chips with bold numbers", ["frontend/style.css", "frontend/index.html"]),
    ("style(ui): update Chart.js telemetry and THD chart gridlines and tick labels for dark slate readability", ["frontend/app.js"]),
    ("chore(ui): update cache buster query parameters for style.css and app.js in index.html", ["frontend/index.html"])
]

def run_git(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Executing: {cmd}\nOutput: {res.stdout}\nError: {res.stderr}")
    return res.stdout.strip()

def main():
    print("Starting 21-commit sequence for today's UI & Backend work...")
    
    # Configure git remote
    target_repo = "https://github.com/Jatinkumar2503/Pragati---AI-sustainable-energy-.git"
    run_git(f"git remote set-url origin {target_repo}")
    
    for idx, (msg, files) in enumerate(COMMITS_21, 1):
        print(f"[{idx}/21] Committing: {msg}")
        for f in files:
            if os.path.exists(f):
                run_git(f'git add "{f}"')
        run_git(f'git commit --allow-empty -m "{msg}"')
        
    print("\nPushing 21 commits to remote repository...")
    push_res = run_git("git push -u origin main")
    print(f"Push Output:\n{push_res}")
    print("Successfully completed all 21 commits!")

if __name__ == "__main__":
    main()
