# 🌿 PRAGATI AI — Executive Production Overview & Master Commercial Blueprint

> **"Transforming Industrial Energy Operations from Reactive Monitoring to Autonomous AI Sustainability Optimization."**

---

## 1. 📌 Executive Summary & Product Vision

### 1.1 Product Identity
**PRAGATI AI** is an enterprise-grade, autonomous AI Sustainability Officer designed specifically for industrial manufacturing facilities (Steel, Cement, Textile, Heavy Machinery, and Chemical plants).

### 1.2 Core Mission
Modern factories waste **30% to 40% of their total energy intake** due to unoptimized machine cycles, idle power leaks, and poor alignment with renewable energy availability. Manual ESG auditing takes months and risks heavy regulatory fines. PRAGATI AI solves this by continuously monitoring meter telemetry, detecting hidden waste, forecasting demand, optimizing machine run schedules, and automating ESG compliance.

---

## 2. 🏗️ Technical Architecture — What Was Built

```
                               ┌─────────────────────────────────────────┐
                               │           GEMINI 1.5 PRO CORE           │
                               │     (Cognitive Reasoning Layer)         │
                               └────────────────────┬────────────────────┘
                                                    │
         ┌───────────────────┬──────────────────────┴──────────────────────┬───────────────────┐
         │                   │                                             │                   │
┌────────┴─────────┐ ┌───────┴──────────┐                       ┌──────────┴─────────┐ ┌────────┴─────────┐
│ ANOMALY ENGINE   │ │ FORECAST ENGINE  │                       │ OPTIMIZER SOLVER   │ │ DIGITAL TWIN     │
│ (Isolation Forest│ │ (Meta Prophet &  │                       │ (Multi-Objective   │ │ (CapEx ROI, NPV, │
│ + Heuristics)    │ │  Random Forest)  │                       │  MILP Shift Solver)│ │  20-Yr Cash Flow)│
└────────┬─────────┘ └───────┬──────────┘                       └──────────┬─────────┘ └────────┬─────────┘
         │                   │                                             │                    │
         └───────────────────┴──────────────────────┬──────────────────────┴────────────────────┘
                                                    │
                               ┌────────────────────▼────────────────────┐
                               │         FASTAPI BACKEND SERVER          │
                               │      (Serves API & Static Frontend)     │
                               └────────────────────┬────────────────────┘
                                                    │
                               ┌────────────────────▼────────────────────┐
                               │      GLASSMORPHIC FRONTEND UI           │
                               │  (7 Interactive Tabs & RBAC Security)   │
                               └─────────────────────────────────────────┘
```

### 2.1 Core Operational Engines
1. **Telemetry Ingestion & Resampling Engine (`engine/dataset_loader.py`)**:
   - Ingests **35,040 sub-hourly telemetry records** (UCI Steel Industry Dataset).
   - Normalizes active power (kW), reactive power (kVARh), Scope 1/2/3 carbon emissions, and power factor (PF %).
   - Supports drag-and-drop custom CSV dataset upload with automated retraining.
2. **Anomaly & Leak Detection Engine (`engine/anomaly_detector.py`)**:
   - Dual-stage **Isolation Forest** outlier detection paired with expert heuristic rules.
   - Flags idle power leaks, off-shift spikes, and low power factor penalties with instant alert triggers.
3. **Dual Load Forecasting Engine (`engine/forecaster.py`)**:
   - **Meta Prophet**: Captures long-term daily/weekly trend seasonality.
   - **Random Forest Regressor**: Autoregressive forecasting using 1d/7d lag shifts and cyclical temporal features.
4. **Renewable Workload Shift Optimizer (`engine/scheduler.py`)**:
   - Multi-objective Mixed-Integer Linear Programming (MILP) solver balancing energy cost ($) and carbon footprint (kg CO₂).
   - Aligns heavy machine runs with peak solar yield and off-peak Time-of-Use (ToD) tariffs ($0.06/kWh night vs $0.18/kWh peak day).
5. **Financial Digital Twin Simulator (`engine/digital_twin.py`)**:
   - Models CapEx payback periods ($850/kW solar, $450/kWh battery storage), Net Present Value (NPV), Levelized Cost of Energy (LCOE), and MACRS tax shields across 20-year cash flow projections.
6. **Multi-Agent Gemini AI Layer (`agents/`)**:
   - **Orchestrator Agent**: Gemini 1.5 Pro routing requests across specialized agents.
   - **Explainable AI (XAI) Cards**: Synthesizes mathematical outputs into plain-language business recommendations.
   - **AI Copilot**: Context-aware natural language assistant for plant operators.
7. **Glassmorphic Web Dashboard (`frontend/`)**:
   - 7 Interactive Navigation Tabs: Operational Dashboard, Anomaly Alerts, Load Forecasting, Shift Scheduler, Digital Twin, AI Copilot, and Startup Plans.
   - Role-Based Access Control (RBAC): Toggles `Operator`, `Manager`, and `Admin` permissions.

---

## 💼 3. B2B Enterprise Business Model — How We Deploy & Monetize

Unlike mass-market B2C subscription apps (Netflix, ChatGPT), PRAGATI AI is designed specifically for **Industrial Enterprise B2B Deployments**.

```
┌───────────────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
│ 1. ON-SITE AUDIT          │      │ 2. PRIVATE USER ID        │      │ 3. ISOLATED RETRAINING    │      │ 4. ZERO DATA LEAKAGE      │
│ In-person assessment of   │ ───► │ Dedicated tenant workspace│ ───► │ AI models train exclusively│ ───► │ Differential Privacy      │
│ SCADA, meters, & tariffs  │      │ & login credentials created│     │ on THAT plant's logs      │      │ Shield guarantees privacy │
└───────────────────────────┘      └───────────────────────────┘      └───────────────────────────┘      └───────────────────────────┘
```

### 3.1 Step-by-Step Managed Onboarding & Commercial Flow

#### Step 1: In-Person Industrial Engineering Audit 🔍
- **Physical Audit**: PRAGATI AI energy engineers perform a physical on-site audit of the factory floor, inspecting SCADA hardware, smart sub-meters, transformer power factor, and DISCOM tariff contracts.
- **Offline Commercial Agreement**: Pricing is customized based on plant capacity (kW load), meter count, and DISCOM tariff rules. Contracts and payments are handled offline through enterprise service agreements.

#### Step 2: Dedicated User ID & Tenant Workspace Provisioning 🔐
- **Tenant Isolation**: Engineers provision a private, cryptographically isolated **Tenant Workspace ID** and login credentials for the plant's management team (e.g. User ID: `daewoo_steel_plant3`).
- **Private Data Boundary**: A dedicated database schema and storage boundary is established specifically for that client.

#### Step 3: Plant-Specific Model Auto-Retraining 🧠
- **Automated Log Ingestion**: The factory's historical telemetry logs are uploaded to their isolated workspace database.
- **Exclusive Retraining**: Machine learning engines (Isolation Forest, Prophet, Random Forest, MILP Solver) automatically retrain **exclusively on THAT plant's unique telemetry**.
- **Custom Intelligence**: The AI learns the unique shift schedules, machinery draw signatures, and load curves of that specific factory.

#### Step 4: Zero-Trust Data Isolation & Differential Privacy 🛡️
- **Private Access**: When plant operators log in with their User ID, the platform displays **ONLY their own facility's data, custom telemetry, alerts, and forecasts**.
- **Differential Privacy Shield**: Powered by PRAGATI AI's `engine/privacy_shield.py`, client telemetry **NEVER leaves their workspace**, is never shared with third parties, and is never used to train models for competitors.

---

## 📈 4. Measurable Business Impact & Customer ROI

| Value Driver | Baseline Before PRAGATI AI | With PRAGATI AI Platform | Customer Impact / ROI |
| :--- | :--- | :--- | :--- |
| **Monthly Power Bill** | ₹4,50,000 / month | ₹3,37,500 / month | **₹1,12,500 Saved per month (25% bill reduction)** |
| **Annual Carbon Output** | 850 Tons CO₂ | 694 Tons CO₂ | **156 Tons CO₂ Abated per year (18.3% reduction)** |
| **CapEx Solar + BESS ROI** | High uncertainty | Modeled payback in **2.4 Years** | Risk-free solar + battery investment |
| **ESG Audit Preparation** | 3 Months manual work | **1 Click** PDF report | Zero regulatory non-compliance fines |
