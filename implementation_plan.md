# REFINED MASTER PRODUCT ROADMAP & EXECUTION PLAN
# PRAGATI AI 🌿
**Autonomous AI Sustainability Officer for Indian Factories**
*Build with Gemini XPRIZE Edition — Minimum Lovable Agent (MLA) Master Blueprint*

---

## 0. 🎯 Design Philosophy: Minimum Lovable Agent (MLA) First

> **"Judges in an AI-operated business competition are scoring agent intelligence, real data, real reasoning, and business viability — not how many microservices you stood up. Depth beats breadth."**

This refined master plan shifts from an over-engineered 3-month enterprise SaaS architecture to an agile **15-Day Execution Blueprint**. By **Day 6**, you have a fully functional, live-demoable core product on authentic Indian government datasets. Days 7–15 focus on business monetization, pilot outreach, hardening, and pitch rehearsal.

---

## 1. 📢 Product Positioning & XPRIZE Alignment

### Core One-Liner
> **"PRAGATI AI is an autonomous AI Sustainability Officer for Indian factories — it watches energy and production data continuously, explains what's going wrong, and asks a human to approve the fix, using only real government industrial data."**

### XPRIZE Judging Criteria vs. Actual Scope

| XPRIZE Criteria | What We Build (In-Scope) | What We Explicitly Defer (Phase 2) |
| :--- | :--- | :--- |
| **Real AI-Operated Business** | 4 working agents making real, traceable recommendations on authentic data. | 10 stubbed agents without deep reasoning loops. |
| **Real Customer Validation** | 1–3 pilot conversations with actual Indian MSME/factory owners (LOIs/Quotes). | "Customer Success AI" scoring churn on zero real users. |
| **Real Commercial Revenue** | Defensible SaaS pricing (₹2,999 / ₹7,999 / ₹19,999) + live Razorpay checkout. | Dual Razorpay + Stripe billing with complex GST automation. |
| **Google Cloud & Gemini** | Gemini 1.5 Pro as the reasoning, tool-routing, and document cognitive layer. | Generic API wrapper without reasoning traces. |
| **Measurable Impact** | Exact ₹ and CO₂ savings computed from real BEE/CEA/ASI benchmark deltas. | Vague ESG buzzwords. |

---

## 2. 🏗️ Streamlined Engineering Architecture

```
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

### 2.1 The 4 Core Agents + 1 Gemini Orchestrator
1. **Orchestrator Agent (Gemini 1.5 Pro)**: Reasoning coordinator, tool selector, workflow synthesizer, and human approval requester.
2. **Forecast Agent**: Reuses proven TA-GRU / Prophet time-series models to project energy demand and grid carbon intensity.
3. **Anomaly Agent**: Isolation Forest model detecting power factor drops, idle machine power leaks, and off-shift spikes.
4. **Optimization Agent**: Reuses validated Mixed-Integer Linear Programming (MILP) shift scheduler to align heavy loads with green tariff windows.
5. **Compliance & Reporting Agent**: Combines BEE PAT guidelines, RAG document search, XAI Card generation, and executive summaries.

*(Note: Energy, Carbon, and Finance metrics are computed directly as traceable data outputs by these 4 agents rather than split into separate unnecessary agents).*

---

### 2.2 Simplified 3-Layer Stack

```
LAYER 1 — Experience        Lightweight Dashboard (HTML5/CSS3 Glassmorphism or React):
                             AI Board Room • Scorecard • Human Approval Queue • Slider-based Digital Twin

LAYER 2 — Agents & ML       Gemini 1.5 Pro (Orchestration & Reasoning) • 4 Core Agents above
                             PostgreSQL (Metadata & Telemetry) • pgvector/Chroma (RAG for BEE/PAT rules)

LAYER 3 — Business          Single Razorpay Checkout (INR ₹) • Starter, Pro, Enterprise Tiers
                             One Live Payment Rail (India-First)
```

---

### 2.3 Real Data Policy & Demo Workspaces

* **Zero Fake Data Policy**: Powered strictly by public Indian industrial datasets:
  * **Bureau of Energy Efficiency (BEE)** PAT Scheme disclosures
  * **Annual Survey of Industries (ASI)** factory-level aggregates
  * **Central Electricity Authority (CEA)** grid emission factors
  * **State Electricity Board (DISCOM)** Time-of-Use (ToD) tariff schedules
* **4 Pre-loaded Workspaces**:
  1. *Indian Steel Industry Demo* (BEE PAT Steel Cohort data)
  2. *Indian Cement Industry Demo* (BEE PAT Cement Cohort data)
  3. *Indian Textile Industry Demo* (Public Textile cluster data)
  4. *Customer Sandbox* (Blank workspace for live CSV upload during demo)

---

### 2.4 Explainable AI (XAI) Cards

Every recommendation produces a standardized, fully traceable **XAI Card**:

```json
{
  "recommendation": "Shift Electric Arc Furnace Melt Cycle from 14:00 to 22:00",
  "reasoning_why": "Grid carbon intensity peaks between 14:00-18:00 (780g CO2/kWh), while state ToD tariff imposes a 20% peak surcharge.",
  "confidence_score": 0.94,
  "financial_impact_inr": "₹42,500 / shift savings",
  "carbon_impact_kg": "1,850 kg CO2 reduction",
  "risk_level": "LOW",
  "human_approval_required": true
}
```

---

### 2.5 Corrected PRAGATI Sustainability Score Math

$$\text{PRAGATI Score (0–100)} = 0.25(\text{Efficiency}) + 0.20(\text{Carbon}) + 0.20(\text{Financial}) + 0.15(\text{Renewable}) + 0.10(\text{Compliance}) + 0.10(\text{Operational})$$

$$\text{PRAGATI Score (0–1000 Range)} = \text{PRAGATI Score (0–100)} \times 10$$

---

## 🗓️ Refined 15-Day Execution Roadmap

```
 Day 1-2        Day 3-4         Day 5-6          Day 7-8         Day 9-10        Day 11-12       Day 13-15
┌─────────┐   ┌─────────┐    ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐    ┌─────────┐
│ Core    │   │ Data +  │    │ Demo-   │     │ Business│     │ Polish +│     │ Pilot   │    │ Pitch + │
│ Agents  │   │ RAG +   │    │ Ready   │     │ Layer   │     │ Hardening│    │ Outreach│    │ Video & │
│ Live    │   │ XAI     │    │ MVP     │     │ (Razorpay│    │         │     │ & LOIs  │    │ Rehearsal│
└─────────┘   └─────────┘    └─────────┘     └─────────┘     └─────────┘     └─────────┘    └─────────┘
```

### 🗓️ Days 1–2 — Core Agent Framework
* **Tasks**: Wire Orchestrator + 4 Core Agents to Gemini 1.5 Pro. Port existing MILP scheduler and GRU/Prophet forecasting pipeline into Optimization and Forecast agents. Configure Isolation Forest anomaly detector on real BEE/ASI data.
* **Milestone**: All 4 agents produce one real recommendation each on the command line.

### 🗓️ Days 3–4 — Data, RAG & Explainability
* **Tasks**: Load BEE/ASI/CEA datasets into Steel, Cement, and Textile workspaces. Build pgvector/Chroma RAG store for BEE PAT rules and ToD tariff schedules. Standardize XAI card outputs across all agents.
* **Milestone**: Every agent output produces a traceable XAI card linked to real data.

### 🗓️ Days 5–6 — Demo-Ready MVP (Critical Soft Deadline)
* **Tasks**: Build AI Executive Board Room UI (Morning Brief, Prioritized Risks, Human Approval Queue). Calculate live PRAGATI Score (0–1000). Implement slider-based "What-If" Digital Twin simulator (Solar %, Tariff change, Shift schedule).
* **Milestone**: A stranger can open the dashboard, switch between workspaces, and understand the product in 2 minutes without narration.

### 🗓️ Days 7–8 — Business Layer & Monetization
* **Tasks**: Implement single Razorpay checkout. Display 3 subscription tiers (Starter ₹2,999/mo, Pro Growth ₹7,999/mo, Enterprise ₹19,999/mo) with Starter/Pro functionally connected. Generate clean PDF GST-compliant invoices.
* **Milestone**: A user can execute a payment test and receive a GST invoice.

### 🗓️ Days 9–10 — Polish, Security & Hardening
* **Tasks**: Implement basic auth (Google OAuth2 / JWT with Owner vs. Viewer roles). Add error handling, fallback states, and single `/health` status endpoint.
* **Milestone**: The platform survives clicks and inputs without crashing.

### 🗓️ Days 11–12 — Pilot Outreach & Real Industry Validation
* **Tasks**: Reach out to 5–10 Indian MSME manufacturers (via university alumni network, local MSME clusters, or industry contacts) for a 15-minute feedback call. Obtain quotes or Letters of Intent (LOIs).
* **Milestone**: At least 1 real quote or LOI from an actual factory operator.

### 🗓️ Days 13–15 — Pitch, Demo Video & Rehearsal
* **Tasks**: Record a 5-minute video demo. Implement backup JSON response caching for offline demo reliability. Rehearse live pitch 3x.
* **Milestone**: Pitch deck + Demo Video + Live Workspace completely synced.

---

## 💳 Refined SaaS Business Model

### Tiered Pricing Matrix

| Subscription Tier | Price (INR) | Value & Features Unlocked |
| :--- | :---: | :--- |
| **Starter Tier** | **₹2,999 / month** | Up to 10 endpoints • Forecasting + Isolation Forest Anomaly Detection • Scope 1/2 Carbon Audit |
| **Pro Growth Tier** | **₹7,999 / month** | Up to 35 endpoints • **MILP Shift Optimizer** • **What-If Digital Twin Simulator** • **AI Board Room** |
| **Enterprise Tier** | **₹19,999 / month** | **Unlimited endpoints** • Full Compliance RAG • Custom Subdomain • Headless REST API |

---

## 🎬 5-Minute Pitch & Demo Script (Judges' Workflow)

1. **0:00–0:30 (The Problem & One-Liner)**: State the problem (Indian factories lose ₹X Lakhs/year to idle power leaks) and introduce PRAGATI AI as the autonomous AI Sustainability Officer.
2. **0:30–1:30 (The AI Board Room)**: Open the Steel Industry workspace powered by BEE PAT data. Show the morning brief and flagged anomaly.
3. **1:30–2:30 (Agent Reasoning & XAI Card)**: Click into the anomaly $\rightarrow$ reveal Gemini's actual tool-calling trace $\rightarrow$ show the XAI Card with exact ₹ and CO₂ savings.
4. **2:30–3:15 (Human Approval & What-If Simulation)**: Approve recommendation $\rightarrow$ open Digital Twin slider simulator $\rightarrow$ watch PRAGATI Score update live.
5. **3:15–4:00 (Customer Sandbox & CSV Upload)**: Switch to Workspace 4 $\rightarrow$ drag-and-drop a new CSV telemetry file live $\rightarrow$ show the pipeline executing in real-time.
6. **4:00–4:45 (Monetization & Pilot Validation)**: Show pricing page, Razorpay checkout, and quote/LOI from a real factory owner.
7. **4:45–5:00 (Closing Vision)**: Reiterate the 2040 vision.

---

## 🛡️ Judge Q&A Defense Strategy

| Likely Judge Question | Prepared Strategic Defense |
| :--- | :--- |
| **"Is this dataset synthetic?"** | "No, all demo workspaces use authentic BEE PAT disclosures, ASI aggregates, and CEA grid carbon factors. Let me show you the source data links." |
| **"What does Gemini do vs. hardcoded code?"** | "Gemini serves as the Cognitive Orchestrator—it plans agent tasks, routes calls to our ML models, parses documents, and generates XAI explanations." |
| **"Why 4 agents instead of 10?"** | "We prioritized agent depth over breadth. These 4 agents perform real reasoning over real datasets rather than stubbing 10 superficial endpoints." |
| **"What if the anomaly detector makes a mistake?"** | "That is why we enforce a Human-in-the-Loop approval gate for all operational recommendations." |

---

## 🎯 Verification & Deliverables Checklist

- [x] **Core Architecture**: 4 Core Agents + Gemini Orchestrator.
- [x] **Data Integrity**: Powered by authentic BEE, ASI, and CEA datasets.
- [x] **Explainability**: XAI Cards with financial & carbon impact calculations.
- [x] **Scorecard Math**: Standardized 0–100 / 0–1000 composite score formula.
- [x] **Business Monetization**: Razorpay INR pricing (₹2,999 / ₹7,999 / ₹19,999).
- [x] **Demo Readiness**: 5-Minute pitch script + offline fallback caching.

---

## User Approval Requested

Please review this **Refined Minimum Lovable Agent (MLA) Master Plan**. Click **Proceed** to approve this plan so we can begin execution of **Days 1–2 (Core Agent Framework & Gemini Wiring)**!
