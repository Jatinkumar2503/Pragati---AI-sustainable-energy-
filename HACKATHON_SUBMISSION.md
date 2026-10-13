# 🏆 PRAGATI AI — Technical Overview & Hackathon Submission Blueprint

> **System Title:** PRAGATI AI — Industrial Energy Intelligence & Decision-Support Platform  
> **Repository:** [Jatinkumar2503/Pragati---AI-sustainable-energy-](https://github.com/Jatinkumar2503/Pragati---AI-sustainable-energy-)  
> **Evaluation Benchmark Fixture:** `STEEL_BENCHMARK_FIXTURE_V1` (Faridabad Heavy Steel Smelting Plant)  
> **Evidence Register:** [`EVIDENCE_REGISTER.md`](file:///c:/Users/Asus/Documents/sustainable%20platform/EVIDENCE_REGISTER.md)  
> **Methodology Matrix:** [`METHODOLOGY_AND_LIMITATIONS.md`](file:///c:/Users/Asus/Documents/sustainable%20platform/METHODOLOGY_AND_LIMITATIONS.md)  

---

## 1. 🎯 Technical Overview (For Judges & Technical Reviewers)

### 1.1 The Industrial Challenge
Heavy manufacturing facilities (smelting, foundries, chemical processing) consume massive electrical loads under complex Time-of-Day (ToD) tariffs and strict contract demand ceilings. Operational planners struggle with:
1. **Unpredictable peak demand penalties** and low power factor surcharges.
2. **Idle equipment energy waste** and thermal overload risks on sub-station transformers.
3. **Rigid production schedules** that run high-draw equipment during peak tariff windows rather than solar hours.
4. **Capital uncertainty** when evaluating multi-year Solar PV and Battery Energy Storage System (BESS) investments.

### 1.2 The PRAGATI AI Solution
PRAGATI AI is an industrial decision-support and optimization system that bridges machine learning, mathematical programming, and large multimodal models into a unified operational workflow:
- **Load Forecasting Engine:** Tri-model pipeline combining Meta Prophet (seasonal harmonics), Random Forest (autoregressive lags), and a pure NumPy GRU Recurrent Neural Network (64 hidden units), blended via variance-weighted ensembling. Evaluated via 3-fold chronological holdouts with zero forward lookahead leakage.
- **Multivariate Anomaly Detection:** Isolation Forest coupled with rolling 3-sigma statistical control bounds and physical threshold rules (PF < 0.90, transformer temperature > 85°C). Incorporates deterministic sliding-window alert deduplication and full operator lifecycle tracking (`TRIGGERED` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `RESOLVED`).
- **MILP Production Shift Scheduler:** Mixed-Integer Linear Programming optimizer that dispatches sequential machine tasks (e.g., Electric Arc Furnace $\rightarrow$ Ladle Refining Furnace $\rightarrow$ Continuous Casting Machine) to minimize electricity cost and Scope 2 carbon while enforcing machine precedence DAGs, min/max inter-stage buffer lags, contract demand ceilings (450 kW), and maintenance blackout windows.
- **Physics-Informed Digital Twin:** 15-year discounted cash flow simulation for Solar PV + BESS microgrids incorporating semi-empirical Arrhenius calendar aging and cycle-fatigue battery degradation, automated pack replacement triggers, statutory tax shields (Section 32 40% WDV), and One-At-A-Time (OAT) Tornado sensitivity ranking.
- **Decision Center & Industrial Privacy Shield:** Append-only human-in-the-loop governance mechanism logging manager approvals (`ACT-2026-xxx`) with constraint audit verification. Protects proprietary factory parameters by tokenizing sensitive equipment and meter IDs before external LLM queries.

---

## 2. 🤖 Gemini AI Architecture & Multimodal Reasoning

```
                       ┌─────────────────────────────────────────┐
                       │           GEMINI 1.5 PRO CORE           │
                       │     (Cognitive Reasoning Layer)         │
                       └────────────────────┬────────────────────┘
                                            │
         ┌───────────────────┬──────────────┴──────────────┬───────────────────┐
         │                   │                             │                   │
┌────────┴─────────┐ ┌───────┴──────────┐       ┌──────────┴─────────┐ ┌────────┴─────────┐
│ MULTIMODAL BILL  │ │  ORCHESTRATOR    │       │ EXPLAINABLE AI     │ │  COPILOT NLP     │
│ PARSER           │ │  AGENT ROUTER    │       │ (XAI) CARDS        │ │  CONVERSATIONAL  │
│ (Scans PDF bills │ │ (Routes sub-     │       │ (Synthesizes risk, │ │ (Natural language│
│ & SLD diagrams)  │ │  agent tasks)    │       │  cost & CO2 impact)│ │  operator chat)  │
└──────────────────┘ └──────────────────┘       └────────────────────┘ └──────────────────┘
```

### 2.1 Key Cognitive Capabilities
- **Multimodal Document Parsing:** Ingests utility electricity bills (PDF/PNG) to extract billed maximum demand, power factor penalties, and ToD slab tariffs.
- **Explainable AI (XAI) Recommendation Cards:** Synthesizes complex MILP constraint audits and forecast variances into plain-language actionable recommendations with operator checklists and financial payback rationales.
- **Industrial Copilot NLP Assistant:** Context-aware natural language interface allowing plant engineers to query live telemetry, request schedule re-optimization, or investigate alert root causes.

---

## 3. 📊 Benchmark Performance & Reported Metrics

All reported performance metrics are evaluated against the versioned benchmark fixture `STEEL_BENCHMARK_FIXTURE_V1` and the UCI Steel Industry Dataset (35,040 observations).

| Subsystem | Metric | Evaluated Value | Evaluation Condition / Provenance |
| :--- | :--- | :---: | :--- |
| **Forecasting Ensemble** | Weighted Absolute Percentage Error (WAPE) | **0.105 (10.5%)** | 3-fold rolling chronological holdout (2,880 samples) |
| **Forecasting Ensemble** | Safe Mean Absolute Percentage Error (Safe MAPE) | **10.7%** | Denominators $<1.0\text{ kWh}$ clipped to prevent zero-division |
| **Forecasting Ensemble** | Mean Absolute Error (MAE) | **11.90 kWh** | Chronological holdout on UCI Steel dataset |
| **Forecasting Ensemble** | Root Mean Squared Error (RMSE) | **15.65 kWh** | Chronological holdout on UCI Steel dataset |
| **MILP Shift Scheduler** | Batch Electricity Cost Savings | **$48.50 / batch** | EAF $\rightarrow$ LRF $\rightarrow$ CCM batch run vs unoptimized flat schedule |
| **MILP Shift Scheduler** | Constraint Feasibility | **100% Feasible** | Precedence, buffer lags, and 450 kW ceiling strictly satisfied |
| **Digital Twin (15-Yr)** | Internal Rate of Return (IRR) | **18.6%** | Safe numerical bisection algorithm over $[-50\%, +200\%]$ |
| **Digital Twin (15-Yr)** | Net Present Value (NPV) | **$382,000+** | 350 kW Solar + 150 kWh BESS at 10% discount rate |
| **Digital Twin (15-Yr)** | Simple Payback Period | **4.8 Years** | Undiscounted capital recovery |
| **Digital Twin (15-Yr)** | After-Tax Breakeven Period | **4.2 Years** | Incorporates Section 32 40% WDV tax depreciation shield |
| **BESS Degradation** | 15-Year Final State of Health (SOH) | **78.23%** | LFP chemistry @ 35 °C ambient, Arrhenius calendar + cycle fade |
| **Carbon Accounting** | Scope 2 Abatement | **268 tons CO₂/yr** | Traced to CEA CO2 Baseline Database v19 (0.716 kg CO₂/kWh) |

---

## 4. ⚖️ Methodology, Limitations & Truth-in-Advertising

To maintain uncompromising scientific honesty:

1. **Synthetic Telemetry Disclosure:** The Faridabad Heavy Steel Smelting Plant scenario (`STEEL_BENCHMARK_FIXTURE_V1`) is a **deterministic synthetic benchmark fixture**. It is not claimed to be live hardware telemetry from an unverified physical plant.
2. **Benchmark-Specific Forecast Metrics:** The reported WAPE (10.5%) and safe MAPE (10.7%) are benchmark-specific metrics derived from the historical UCI Steel Industry Dataset. They demonstrate model pipeline capability and cannot be construed as a guarantee of identical accuracy at an uncalibrated industrial plant.
3. **Simulated Financial Outcomes:** Projected NPV, IRR, payback periods, and operational savings are forward-looking engineering simulations that depend on user-configured inputs (discount rate, tariff escalation, solar insolation). They do not represent guaranteed commercial returns.
4. **Statutory Tax Modeling Notice:** Modeling of Section 32 40% Written Down Value (WDV) depreciation under the Indian Income Tax Act 1961 represents a statutory engineering assumption that requires corporate eligibility verification and does not constitute formal tax or legal advice.
5. **Emissions Factor Provenance:** Scope 2 emissions calculations are based on the national weighted baseline emission factor of 0.716 kg CO₂/kWh from the Central Electricity Authority (CEA), Ministry of Power, Government of India, CO2 Baseline Database Version 19 (October 2023).

For complete claim-by-claim traceability, refer to [`EVIDENCE_REGISTER.md`](file:///c:/Users/Asus/Documents/sustainable%20platform/EVIDENCE_REGISTER.md) and [`METHODOLOGY_AND_LIMITATIONS.md`](file:///c:/Users/Asus/Documents/sustainable%20platform/METHODOLOGY_AND_LIMITATIONS.md).

---

## 5. 🚀 Reproducible 5-Minute Demo & Deployment

The platform includes a self-contained, automated 5-minute demo runner that exercises the entire pipeline end-to-end:

```bash
# Execute the automated 5-minute industrial demonstration runner
python backend/engine/demo_runner.py
```

### Verified Demo Execution Sequence:
1. **System Health Verification:** Validates backend components and database connectivity.
2. **Benchmark Ingestion:** Loads `STEEL_BENCHMARK_FIXTURE_V1` (1,250 kW transformer, 450 kW demand ceiling).
3. **Telemetry & Deduplicated Alert:** Ingests overload spike ($94.2\text{ }^\circ\text{C}$), confirms deduplication window suppression and lifecycle tracking.
4. **Holdout-Evaluated Forecast:** Evaluates ensemble forecast with model provenance and safe MAPE metrics.
5. **MILP Production Optimization:** Dispatches EAF $\rightarrow$ LRF $\rightarrow$ CCM batch with strict precedence and lag audit.
6. **Digital Twin Financial Simulation:** Evaluates 15-year DCF, battery degradation, Section 32 tax shield, and Tornado sensitivity.
7. **Managerial Audit Trail:** Submits action card `ACT-2026-082`, registers managerial signoff, and verifies append-only audit log.

### API & Swagger Documentation:
- **FastAPI Documentation:** `http://127.0.0.1:8000/docs`
- **Health Check Endpoint:** `http://127.0.0.1:8000/health`
