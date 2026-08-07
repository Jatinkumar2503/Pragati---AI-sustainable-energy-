# PRAGATI AI 🌿
### Autonomous AI Sustainability Officer for Indian Factories
**Build with Gemini XPRIZE Edition | Minimum Lovable Agent (MLA) Master Architecture**

---

## 🎯 Executive Overview & Product Positioning

> **"PRAGATI AI is an autonomous AI Sustainability Officer for Indian factories — it watches energy and production data continuously, explains what's going wrong, and asks a human to approve the fix, using only real government industrial data."**

PRAGATI AI moves beyond passive energy monitoring dashboards. It operates as an AI employee running continuous background workflows, orchestrating specialized machine learning engines and **Google Gemini 1.5 Pro** cognitive reasoning to lower energy bills, eliminate off-shift power leaks, optimize machine run schedules, and streamline Scope 1/2/3 ESG reporting.

---

## 🚀 Key Differentiators & Principles

1. **AI-Native Operations**: Continuous background monitoring and tool-calling rather than a simple chatbot or passive charts.
2. **Zero Fake Data Policy**: Powered strictly by authentic Indian government industrial datasets:
   * **Bureau of Energy Efficiency (BEE)** PAT Scheme disclosures
   * **Annual Survey of Industries (ASI)** factory-level aggregates
   * **Central Electricity Authority (CEA)** grid emission factors
   * **State Electricity Board (DISCOM)** Time-of-Use (ToD) tariff schedules
3. **Seamless Customer Transition**: Frictionless onboarding from pre-loaded Indian sector demo workspaces to private customer data (CSV, IoT, ERP, SCADA).
4. **Explainable AI (XAI) Cards**: Every agent recommendation produces a standardized, human-auditable XAI card displaying confidence scores, root cause explanations, financial impact (INR ₹), and carbon reduction (kg CO₂).
5. **Commercial SaaS Business Model**: Built to generate recurring revenue immediately upon launch, featuring 3 Indian pricing tiers (₹2,999 / ₹7,999 / ₹19,999 per month) with single Razorpay integration and GST invoicing.

---

## 🏗️ Multi-Agent System Architecture

```text
                    ┌─────────────────────────────┐
                    │     ORCHESTRATOR AGENT      │
                    │ (Gemini 1.5 Pro — plans,    │
                    │  routes, synthesizes,       │
                    │  requests human approval)   │
                    └───────────────┬─────────────┘
                                    │
      ┌─────────────────┬───────────┴───────────┬─────────────────┐
      │                 │                       │                 │
┌─────┴──────┐   ┌──────┴───────┐      ┌────────┴────────┐  ┌─────┴──────┐
│ FORECAST   │   │  ANOMALY     │      │  OPTIMIZATION   │  │ COMPLIANCE  │
│ AGENT      │   │  AGENT       │      │  AGENT          │  │ & REPORTING │
│ (Prophet / │   │ (Isolation   │      │ (OR-Tools MILP  │  │ AGENT       │
│  TA-GRU)   │   │  Forest)     │      │  Shift Solver)  │  │ (BEE PAT +  │
│            │   │              │      │                 │  │  XAI Cards) │
└────────────┘   └──────────────┘      └─────────────────┘  └─────────────┘
```

### The 4 Core Agents + 1 Gemini Orchestrator
1. **Orchestrator Agent (Gemini 1.5 Pro)**: Reasoning coordinator, tool selector, workflow synthesizer, and human approval requester.
2. **Forecast Agent** (`backend/agents/forecast_agent.py`): Projects temporal load curves and grid carbon intensity using Prophet & GRU neural networks.
3. **Anomaly Agent** (`backend/agents/anomaly_agent.py`): Isolation Forest model detecting power factor drops, idle machine power leaks, and off-shift spikes.
4. **Optimization Agent** (`backend/agents/optimization_agent.py`): Mixed-Integer Linear Programming (MILP) solver aligning heavy machine shifts with green tariff windows.
5. **Compliance & Reporting Agent** (`backend/agents/compliance_agent.py`): Audits BEE PAT target compliance, calculates the composite **PRAGATI Score (0–1000)**, and outputs executive scorecards.
6. **Digital Twin Agent** (`backend/agents/digital_twin_agent.py`): Evaluates Solar PV, BESS Battery Storage, and Load Shifting scenarios with financial and carbon ROI projections.
7. **Alert Management Agent** (`backend/agents/alert_agent.py`): Triages high-frequency meter threshold alerts and generates emergency mitigation XAI Cards.

---

## 📊 PRAGATI Composite Sustainability Scorecard

Facilities are evaluated against a standardized 6-factor composite score:

$$\text{PRAGATI Score (0–100)} = 0.25(\text{Efficiency}) + 0.20(\text{Carbon}) + 0.20(\text{Financial}) + 0.15(\text{Renewable}) + 0.10(\text{Compliance}) + 0.10(\text{Operational})$$

$$\text{PRAGATI Score (0–1000 Range)} = \text{PRAGATI Score (0–100)} \times 10$$

---

## 📁 Repository Structure

```text
├── backend/
│   ├── api.py                    # FastAPI REST API, Static Mounts, API Key Security
│   ├── requirements.txt           # Python dependencies
│   ├── agents/                   # Multi-Agent Framework
│   │   ├── __init__.py           # Package exporter
│   │   ├── base_agent.py         # Abstract BaseAgent & XAICard model
│   │   ├── forecast_agent.py     # Forecast Agent (Prophet + GRU)
│   │   ├── anomaly_agent.py      # Anomaly Agent (Isolation Forest)
│   │   ├── optimization_agent.py # Optimization Agent (MILP Shift Scheduler)
│   │   ├── compliance_agent.py   # Compliance Agent (BEE PAT Audit & PRAGATI Scorecard)
│   │   ├── digital_twin_agent.py # Digital Twin Agent (Scenario Modeling & ROI)
│   │   ├── alert_agent.py        # Alert Agent (Emergency Threshold Triage & XAI Cards)
│   │   └── orchestrator.py       # Gemini 1.5 Pro AgentOrchestrator
│   ├── engine/                   # Specialized ML Core & Solvers
│   │   ├── dataset_loader.py     # Public Indian Industrial Dataset loader (BEE/ASI/CEA)
│   │   ├── anomaly_detector.py   # Isolation Forest engine with MAD statistics
│   │   ├── forecaster.py         # Prophet, Random Forest & GRU neural network models
│   │   ├── scheduler.py          # MILP Solver (OR-Tools / SciPy) & ToD Tariff Calculator
│   │   ├── digital_twin.py       # Digital Twin Engine (Solar PV, BESS & Carbon Factors)
│   │   ├── privacy_shield.py     # Differential Privacy Shield (Laplace Mechanism)
│   │   └── telemetry_db.py       # SQLite / PostgreSQL Telemetry Storage Engine
│   └── tests/
│       ├── test_backend.py       # REST API integration test suite
│       └── test_agents.py        # Multi-Agent framework unit test suite
├── frontend/
│   ├── index.html                # Responsive Glassmorphic Dashboard UI
│   ├── style.css                 # Glassmorphism & Pricing CSS design system
│   └── app.js                    # Chart.js visualizations, Tab routing & Payment modal logic
├── PRD.md                        # Product Requirements Document
├── README.md                     # Project documentation (this file)
└── build_40_day_git_history.py  # Structured Commit Generator script
```

---

## ⚙️ Quick Start Installation & Execution

### 1. Backend Setup
Prerequisites: **Python 3.10+** installed.

```bash
cd backend
pip install -r requirements.txt
```

Start the FastAPI server:
```bash
python api.py
```
You will see:
`INFO: Uvicorn server running on http://127.0.0.1:8000 (Press CTRL+C to quit)`

### 2. Access the Portal
Open your web browser and navigate to:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 💳 SaaS Subscription Pricing (INR ₹)

| Subscription Tier | Price (INR) | Features & Quotas Unlocked |
| :--- | :---: | :--- |
| **Starter Tier** | **₹2,999 / month** | Up to 10 endpoints • Forecasting + Isolation Forest Anomaly Engine • Scope 1/2 Carbon Audit |
| **Pro Growth Tier** | **₹7,999 / month** | Up to 35 endpoints • **MILP Shift Optimizer** • **What-If Digital Twin Simulator** • **AI Board Room** |
| **Enterprise Tier** | **₹19,999 / month** | **Unlimited endpoints** • Full Compliance RAG • Custom Subdomain • Headless REST API |

---

## 🧪 Running Automated Tests

Run the complete backend and multi-agent test suite:
```bash
python -m unittest discover backend/tests
```

---

## 📊 Enterprise Regulatory Compliance & Physical Formulations

### 1. BEE PAT Cycle-VII Specific Energy Consumption (SEC) & ESCerts
- **Iron & Steel Norm**: $SEC_{target} = 0.585 \text{ TOE/ton crude steel}$
- **Cement Norm**: $SEC_{target} = 68.5 \text{ kWh/ton cement}$ and $725 \text{ kcal/kg clinker}$
- **Textile Norm**: $SEC_{target} = 14.2 \text{ MJ/kg fabric}$
- **Energy Saving Certificates (ESCerts)**:
  $$\Delta \text{TOE} = (SEC_{target} - SEC_{actual}) \times \text{Production (tons)}$$
  $$\text{Market Valuation (INR)} = \Delta \text{TOE} \times ₹1,840/\text{ESCert}$$

### 2. Reactive Power & Automatic Power Factor Controller (APFC) Sizing
$$Q_c (\text{kVAR}) = P (\text{kW}) \times \left[ \tan(\arccos(PF_{actual})) - \tan(\arccos(PF_{target})) \right]$$
- Standard 6-stage / 8-stage microprocessor stepped capacitor relay sizing.
- Eliminates DISCOM low power factor penalties and earns up to 7% PF incentive rebates.

### 3. Utility BESS Arrhenius Electrochemical Aging Physics
$$SOH(t) = 1.0 - \left[ B_{cal} \cdot \exp\left(-\frac{E_a}{R \cdot T}\right) \cdot t^{0.5} + B_{cyc} \cdot (\Delta DOD)^\beta \cdot N_{cycles}^\gamma \right]$$
- Accurately models Lithium Iron Phosphate (LFP) vs Nickel Manganese Cobalt (NMC) 10-year battery capacity fade and End-of-Life (EOL at 80% SOH) projections.

### 4. SEBI BRSR Core Principle 6 ESG Reporting
- Comprehensive disclosure of Scope 1 (Direct fuel / diesel combustion), Scope 2 (Location-based & Market-based grid electricity using CEA regional factors), and Scope 3 (Upstream transmission losses).
- Computes GHG emission intensity per crore rupees of enterprise revenue.

---

## 📜 License
Developed for the **Build with Gemini XPRIZE Edition 2026**. All Rights Reserved.
