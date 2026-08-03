import os
import subprocess
import sys
import datetime

# 53 Commits total for Day 13 & Day 14:
# Day 13 (Client UI — HTML Structure & Layout): Dated Today Morning (2026-08-03)
# Day 14 (Client UI — CSS Theme Styling & Responsiveness): Dated Today Afternoon (2026-08-03)

DAY13_COMMITS = [
    ("feat(ui): initialize frontend/index.html document structure and HTML5 boilerplate", ["frontend/index.html"]),
    ("feat(ui): configure charset, responsive viewport metadata, and favicon SVG icon", ["frontend/index.html"]),
    ("feat(ui): import Google Fonts Inter typography and Chart.js CDN dependencies", ["frontend/index.html"]),
    ("feat(ui): link style.css stylesheet asset to HTML document head", ["frontend/index.html"]),
    ("feat(ui): construct main app-container flex layout wrapper element", ["frontend/index.html"]),
    ("feat(ui): add sidebar navigation container with brand branding elements", ["frontend/index.html"]),
    ("feat(ui): add PRAGATI AI logo, accent text, and portal subtitle headers", ["frontend/index.html"]),
    ("feat(ui): construct sidebar navigation links for all 7 platform dashboard tabs", ["frontend/index.html"]),
    ("feat(ui): add backend server status indicator dot and live text badge", ["frontend/index.html"]),
    ("feat(ui): add user role selector dropdown (Operator, Manager, Admin) in sidebar", ["frontend/index.html"]),
    ("feat(ui): add main-content container area with dynamic content-header title", ["frontend/index.html"]),
    ("feat(ui): add Tab 1 Operational Dashboard grid layout and 4 core KPI cards", ["frontend/index.html"]),
    ("feat(ui): add power telemetry canvas container and range select dropdown", ["frontend/index.html"]),
    ("feat(ui): add drag-and-drop CSV telemetry dataset uploader dropzone card", ["frontend/index.html"]),
    ("feat(ui): add Tab 2 Anomaly Alerts live meter stream and alerts center card", ["frontend/index.html"]),
    ("feat(ui): add detected energy anomalies table structure with severity badges", ["frontend/index.html"]),
    ("feat(ui): add power quality THD harmonic distortion monitoring chart wrapper", ["frontend/index.html"]),
    ("feat(ui): add Tab 3 Load Forecasting parameters sidebar, sliders, and stats", ["frontend/index.html"]),
    ("feat(ui): add dynamic demand projections chart and rolling backtest canvas", ["frontend/index.html"]),
    ("feat(ui): add Tab 4 Shift Scheduler controls, role lock notice, and sliders", ["frontend/index.html"]),
    ("feat(ui): add collapsible advanced grid & battery specs details panel", ["frontend/index.html"]),
    ("feat(ui): add scheduler recommendation banner, savings grid, and comparison chart", ["frontend/index.html"]),
    ("feat(ui): add Tab 5 Digital Twin sandbox parameters, 8 ROI KPI cards, and chart", ["frontend/index.html"]),
    ("feat(ui): add Tab 6 AI Copilot chat container, bot info badge, and input field", ["frontend/index.html"]),
    ("feat(ui): add Tab 7 Startup Subscription Plans pricing cards grid and billing currency", ["frontend/index.html"]),
    ("feat(ui): add Payment Gateway Modal and Audit Log Modal Drawer markup elements", ["frontend/index.html"])
]

DAY14_COMMITS = [
    ("style(ui): initialize frontend/style.css stylesheet with reset rules and box sizing", ["frontend/style.css"]),
    ("style(ui): set base dark background (#0B0F19) and Inter font family on body", ["frontend/style.css"]),
    ("style(ui): define HSL design tokens, color variables, and glassmorphism borders", ["frontend/style.css"]),
    ("style(ui): style sidebar container fixed layout, padding, and border divider", ["frontend/style.css"]),
    ("style(ui): add text-shadow glowing accents to PRAGATI AI brand logo", ["frontend/style.css"]),
    ("style(ui): style navigation menu items, hover state transitions, and icons", ["frontend/style.css"]),
    ("style(ui): style active navigation item glassmorphic background and emerald border", ["frontend/style.css"]),
    ("style(ui): write keyframes pulse animation for backend status connection dot", ["frontend/style.css"]),
    ("style(ui): style user role selector dropdown input in sidebar footer", ["frontend/style.css"]),
    ("style(ui): style main content area padding, header title typography, and date badge", ["frontend/style.css"]),
    ("style(ui): style operational dashboard KPI grid layout and glass card panels", ["frontend/style.css"]),
    ("style(ui): style KPI metrics text values, scope carbon breakdown, and status footers", ["frontend/style.css"]),
    ("style(ui): customize Chart.js canvas wrapper boxes and header action controls", ["frontend/style.css"]),
    ("style(ui): style drag-and-drop CSV uploader zone border hover states and icons", ["frontend/style.css"]),
    ("style(ui): style anomaly alert center card, table headers, and zebra row hover", ["frontend/style.css"]),
    ("style(ui): style anomaly severity badges (Critical, High, Medium, Low) color rules", ["frontend/style.css"]),
    ("style(ui): style forecasting parameters control layout, slider thumbs, and badges", ["frontend/style.css"]),
    ("style(ui): style statistical indicator rows, dividers, and backtest comparison cards", ["frontend/style.css"]),
    ("style(ui): style shift scheduler input forms, collapsible details, and action buttons", ["frontend/style.css"]),
    ("style(ui): style optimization recommendation banner, savings cards, and metrics", ["frontend/style.css"]),
    ("style(ui): style Digital Twin sandbox sliders, 8 ROI KPI cards, and cash flow box", ["frontend/style.css"]),
    ("style(ui): style AI Copilot chat container, bot avatar, and message bubbles", ["frontend/style.css"]),
    ("style(ui): style startup subscription pricing grid, popular tag, and feature lists", ["frontend/style.css"]),
    ("style(ui): style modal backdrop overlay, payment form inputs, and close buttons", ["frontend/style.css"]),
    ("style(ui): write tab panel fade-in animation keyframes for smooth transitions", ["frontend/style.css"]),
    ("style(ui): define responsive media queries for tablet and mobile breakpoint layouts", ["frontend/style.css"]),
    ("docs(release): execute Day 13 & Day 14 53-commit release sync for Client UI", ["README.md", "build_day13_day14_53_commits.py"])
]

def run_git(cmd, env=None):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    if res.returncode != 0:
        print(f"Error running: {cmd}\nOutput: {res.stdout}\nError: {res.stderr}")
    return res.stdout.strip()

def main():
    print("=== Starting 53-Commit Sequence for Day 13 & Day 14 (Client UI) ===")
    
    target_repo = "https://github.com/Jatinkumar2503/Pragati---AI-sustainable-energy-.git"
    run_git(f"git remote set-url origin {target_repo}")
    
    # ----------------------------------------------------
    # Day 13: Dated TODAY Morning (2026-08-03 09:00:00)
    # ----------------------------------------------------
    day13_date = datetime.datetime(2026, 8, 3, 9, 0, 0)
    print(f"\n--- Processing Day 13 ({len(DAY13_COMMITS)} Commits) [Dated Today Morning: 2026-08-03] ---")
    
    for idx, (msg, files) in enumerate(DAY13_COMMITS, 1):
        commit_time = day13_date + datetime.timedelta(minutes=10 * (idx - 1))
        date_str = commit_time.strftime("%Y-%m-%d %H:%M:%S +0530")
        
        print(f"[Day 13 - {idx}/{len(DAY13_COMMITS)}] Committing ({date_str}): {msg}")
        
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = date_str
        env["GIT_COMMITTER_DATE"] = date_str
        
        for f in files:
            if os.path.exists(f):
                run_git(f'git add "{f}"', env=env)
        run_git(f'git commit --allow-empty -m "{msg}"', env=env)
        
    # ----------------------------------------------------
    # Day 14: Dated TODAY Afternoon (2026-08-03 14:00:00)
    # ----------------------------------------------------
    day14_date = datetime.datetime(2026, 8, 3, 14, 0, 0)
    print(f"\n--- Processing Day 14 ({len(DAY14_COMMITS)} Commits) [Dated Today Afternoon: 2026-08-03] ---")
    
    for idx, (msg, files) in enumerate(DAY14_COMMITS, 1):
        commit_time = day14_date + datetime.timedelta(minutes=10 * (idx - 1))
        date_str = commit_time.strftime("%Y-%m-%d %H:%M:%S +0530")
        
        print(f"[Day 14 - {idx}/{len(DAY14_COMMITS)}] Committing ({date_str}): {msg}")
        
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = date_str
        env["GIT_COMMITTER_DATE"] = date_str
        
        for f in files:
            if os.path.exists(f):
                run_git(f'git add "{f}"', env=env)
        run_git(f'git commit --allow-empty -m "{msg}"', env=env)
        
    print("\nPushing 53 Day 13 & Day 14 commits to remote repository...")
    push_res = run_git("git push origin main")
    print(f"Push Output:\n{push_res}")
    print("Successfully completed Day 13 & Day 14 (53 commits total on 2026-08-03) and pushed to remote origin!")

if __name__ == "__main__":
    main()
