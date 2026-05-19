# PRAGATI AI 🌿
### AI-Powered Industrial Sustainability Intelligence Platform

PRAGATI AI is an active sustainability intelligence platform designed for industrial manufacturing plants. Unlike passive monitoring systems (which simply record and plot historical consumption), PRAGATI AI actively forecasts grid energy demands, flags operational energy leaks, models solar/battery ROI in a sandbox, and optimizes heavy machine run schedules to align with cheap, clean renewable energy windows.

Developed for the **Cambridge University Sustainability Hackathon 2026**.

---

## 🚀 Key Capabilities

1. **Unsupervised Anomaly Detection (Isolation Forest)**: Analyzes multi-variate metrics (Active Power, Reactive Power, Power Factor) to flag idle energy leaks, weekend operations, or machine idling without workloads.
2. **Dual-Model Time Series Forecasting**: Fits Meta's **Prophet** and a temporal **Random Forest Regressor** to project future energy requirements, comparing validation accuracy (RMSE).
3. **Renewable Workload Shift Optimizer**: Calculates the mathematically optimal starting hours for energy-intensive tasks based on time-of-use tariffs, solar forecasts, and grid carbon levels.
4. **Digital Twin Investment Sandbox**: Simulates financial metrics, annual solar yields, battery self-consumption rates, and simple payback periods (ROI).
5. **One-Click ESG Compliance**: Automates Scope 1 and Scope 2 carbon auditing, mapping telemetry logs to GRI, TCFD, and CDP scorecards.
6. **Natural Language AI Copilot**: A keyword-routing chat interface that answers operator queries (e.g. *"Where did we waste energy?"*) with data-backed mitigations.

---

## 📁 Repository Structure

```text
├── pragati_platform/
│   ├── backend/
│   │   ├── api.py                    # FastAPI REST API & static file mount
│   │   ├── requirements.txt           # Python dependencies
│   │   └── engine/
│   │       ├── dataset_loader.py     # UCI Steel Industry dataset downloader
│   │       ├── anomaly_detector.py   # Isolation Forest anomaly engine
│   │       ├── forecaster.py         # Prophet & Random Forest models
│   │       └── scheduler.py          # Workload shifting heuristic optimizer
│   └── frontend/
│       ├── index.html                # Premium dashboard UI
│       ├── style.css                 # Glassmorphic responsive styling
│       └── app.js                    # Chart.js visualizations & API connection
├── generate_report.js                # PDF compiler script (Node.js + pdfkit)
├── PRAGATI_AI_Comprehensive_Technical_Report.pdf # Generated 15-page report
├── PRD.md                            # Product Requirements Document
├── .gitignore                        # Git ignore configurations
└── README.md                         # Project documentation (this file)
```

---

## ⚙️ Quick Start Installation & Setup

Follow these steps to run the application locally:

### 1. Set Up the Backend
Prerequisites: **Python 3.8+** installed.

Open your terminal, navigate to the backend directory, and install dependencies:
```bash
cd pragati_platform/backend
pip install -r requirements.txt
```
*Note: If Meta's `prophet` fails to install due to missing C++ build compilers on Windows, the code will automatically fall back to the Random Forest model for forecasting without crashing.*

Start the development server:
```bash
python api.py
```
Or use the direct python launcher on Windows:
```bash
py api.py
```
You should see:
`INFO: Uvicorn server running on http://127.0.0.1:8000 (Press CTRL+C to quit)`

### 2. Access the Dashboard
The FastAPI server is pre-configured to mount the frontend static files. This bypasses browser-level local file CORS restrictions:

Open your web browser and navigate to:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

The dashboard will load, fetch the dataset, and automatically run the machine learning pipelines.

---

## 📄 Technical Report

A compiled, comprehensive 15-page technical report detailing the underlying mathematical derivations, formulas, roadmap, and architecture is available:
* **PDF Report File**: [PRAGATI_AI_Comprehensive_Technical_Report.pdf](./PRAGATI_AI_Comprehensive_Technical_Report.pdf)

### Compiling the PDF Report manually:
If you make modifications to the report contents in `generate_report.js`, you can recompile the PDF using Node.js:
```bash
npm install pdfkit
node generate_report.js
```

---

## 🛠️ Technology Stack

* **Frontend**: Vanilla HTML5, CSS3 (Glassmorphism, custom color HSL palettes), Vanilla ES6 JavaScript, and **Chart.js** for real-time charting.
* **Backend API**: **FastAPI** (Python), Uvicorn server, static file mounts.
* **Machine Learning**: **Scikit-Learn** (Isolation Forest anomaly, Random Forest Regressor), **Meta Prophet** (Additive seasonal time-series).
* **PDF Compiler**: **Node.js** with the **PDFKit** vector graphics and styling package.

---

## 🌿 Project Development Team
* **Prasad Shinde** — Team Lead & Machine Learning Core
* **Ananya Sharma** — Sustainability & Carbon Heuristic Modeling
* **Rohan Verma** — Full-Stack Architect & Microservices
* **Karan Patel** — Industrial IoT & Smart Meters
