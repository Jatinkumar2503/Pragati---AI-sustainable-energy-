# PRAGATI AI — Evidence Register & Verification Traceability Matrix

> **Document Version:** 1.0.0 (Phase 5 Hackathon Master Register)  
> **Repository:** [Jatinkumar2503/Pragati---AI-sustainable-energy-](https://github.com/Jatinkumar2503/Pragati---AI-sustainable-energy-)  
> **Benchmark Fixture Reference:** `STEEL_BENCHMARK_FIXTURE_V1` (Faridabad Heavy Steel Smelting Plant)  
> **Audience:** Hackathon Technical Judges, Industrial Safety Reviewers, ESG Governance Committees  

---

## 1. Evidence Hierarchy & Evaluation Framework

To maintain strict scientific objectivity and prevent unsupported marketing claims, all technical assertions in PRAGATI AI are categorized according to a five-tier evidence hierarchy:

```
┌────────────────────────────────────────────────────────────────────────┐
│ Level 5: Real-World Pilot Evidence (Factory Telemetry & Utility Bills) │
├────────────────────────────────────────────────────────────────────────┤
│ Level 4: External-Source Verification (CEA v19, Sec 32, GHG Protocol)  │
├────────────────────────────────────────────────────────────────────────┤
│ Level 3: Independent Mathematical Benchmark (First-Principles Python)  │
├────────────────────────────────────────────────────────────────────────┤
│ Level 2: Automated Unit & Integration Tests (148 Passing Test Cases)   │
├────────────────────────────────────────────────────────────────────────┤
│ Level 1: Implemented Software Capability (Executable Code in Repo)     │
└────────────────────────────────────────────────────────────────────────┘
```

- **Level 1 — Implemented Capability:** Code exists, executes without runtime exceptions, and generates specified outputs.
- **Level 2 — Automated Test Evidence:** Verified by deterministic unit and integration tests executing in CI/CD (`backend/tests/`).
- **Level 3 — Independent Mathematical Benchmark:** Verified by separate, standalone first-principles mathematical validation scripts (`test_independent_financial_benchmarks.py`) with zero circular dependency on production classes.
- **Level 4 — External-Source Verification:** Grounded in recognized statutory publications, regulatory databases, or peer-reviewed literature (e.g., Central Electricity Authority Database v19, Indian Income Tax Act 1961 Section 32(1)).
- **Level 5 — Real-World Pilot Evidence:** Calibrated against physical smart meter hardware, industrial SCADA feeds, and commercial utility bills in an operating manufacturing plant.

---

## 2. Master Evidence Register

| Claim ID | Material Claim Statement | Source Implementation | Test / Verification File | Current Evidence Level | Verification Method | Outstanding Validation / Next Step |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| **CLM-FCST-01** | Tri-model ensemble (Prophet, Random Forest, GRU RNN) achieves WAPE 0.105 (10.5%), safe MAPE 10.7%, MAE 11.90 kWh, RMSE 15.65 kWh on UCI Steel benchmark. | `backend/engine/forecast.py` | `backend/tests/test_forecast.py`<br>`backend/tests/test_phase2_trustworthy_ai.py` | **Level 2 & Level 3** | Rolling 3-fold chronological holdout evaluation (2,880 samples) with zero forward lookahead leakage. Safe MAPE clips denominators $<1.0\text{ kWh}$. | Real-world continuous evaluation on live factory smart meters over a 90-day seasonal weather cycle. |
| **CLM-FCST-02** | Chronological holdout evaluation strictly prevents lookahead data leakage by splitting on datetime boundaries. | `backend/engine/forecast.py` | `backend/tests/test_phase2_trustworthy_ai.py` | **Level 2** | Unit test verifies training indices strictly precede test indices across all 3 cross-validation folds. | Multi-plant cross-validation on disparate industrial SIC codes. |
| **CLM-ANOM-01** | Multivariate Isolation Forest combined with rolling 3-sigma limits and physical thresholds detects active power spikes and low PF (<0.90). | `backend/engine/anomaly.py` | `backend/tests/test_anomalies.py`<br>`backend/tests/test_repeatable_demo.py` | **Level 2** | Synthetic telemetry injection of overload spikes ($94.2\text{ }^\circ\text{C}$ transformer temp, 460 kW spike) triggers structured alert objects. | Validation against historical protection relay trip records and plant maintenance logs. |
| **CLM-ANOM-02** | Alert deduplication engine suppresses repeated alarms within configurable sliding window (1,800s–3,600s) and tracks lifecycle state transitions. | `backend/engine/alerts.py` | `backend/tests/test_alerts.py`<br>`backend/tests/test_repeatable_demo.py` | **Level 2** | Deterministic arrival tests confirm duplicate alerts update `duplicate_count` and preserve operator acknowledgement history. | Production stress testing under high-frequency SCADA alarm storms (1,000+ msgs/sec). |
| **CLM-SCHED-01** | Mixed-Integer Linear Program (MILP) minimizes electricity cost and Scope 2 carbon under ToD tariffs while enforcing 450 kW demand ceiling and maintenance blackouts. | `backend/engine/scheduler.py` | `backend/tests/test_scheduler.py`<br>`backend/tests/test_operational_realism.py` | **Level 2** | Solver comparison against flat baseline schedule demonstrates cost reduction of $48.50 per batch run on synthetic benchmark. | Real-world dispatch validation on physical factory floor with variable heat tap times. |
| **CLM-SCHED-02** | Task precedence DAG (EAF $\rightarrow$ LRF $\rightarrow$ CCM) and inter-stage buffer lag windows are strictly enforced in the MILP solver and audited. | `backend/engine/scheduler.py` | `backend/tests/test_operational_realism.py`<br>`backend/tests/test_repeatable_demo.py` | **Level 2 & Level 3** | Constraint audit verifies `C-PRECEDENCE-01` satisfied, `C-BUFFER-LAG-01` binding, and cyclic dependency DAGs detected via Kahn's algorithm as `INFEASIBLE`. | Integration with plant Programmable Logic Controllers (PLCs) and Manufacturing Execution Systems (MES). |
| **CLM-FIN-01** | 15-year Digital Twin discounted cash flow model computes CapEx, annual savings, O&M escalation (3%/yr), tariff escalation (4%/yr), salvage value, and NPV. | `backend/engine/digital_twin.py` | `backend/tests/test_digital_twin.py`<br>`backend/tests/test_financial_validation.py`<br>`backend/tests/test_independent_financial_benchmarks.py` | **Level 2 & Level 3** | Replicated in standalone first-principles benchmark script; zero-generation edge cases yield negative NPV matching initial CapEx. | Binding EPC contractor turnkey quotation and commercial bank project finance audit. |
| **CLM-FIN-02** | Internal Rate of Return (IRR) uses safe numerical bisection algorithm over $[-50\%, +200\%]$ with sign-change safeguards, returning `null` when mathematically undefined. | `backend/engine/digital_twin.py` | `backend/tests/test_financial_validation.py`<br>`backend/tests/test_independent_financial_benchmarks.py` | **Level 2 & Level 3** | Hand-calculated non-convex and strictly negative cash flow profiles tested against closed-form benchmarks. | Commercial investment banking DCF model audit. |
| **CLM-FIN-03** | One-At-A-Time (OAT) sensitivity analysis varies key inputs (solar insolation, CapEx, tariffs, discount rate) and generates deterministic Tornado impact rankings. | `backend/engine/digital_twin.py` | `backend/tests/test_financial_validation.py`<br>`backend/tests/test_independent_financial_benchmarks.py` | **Level 2 & Level 3** | Verified that Solar Insolation is the dominant financial driver (swing: $211,137), followed by Grid Tariff (swing: $138,591). | Monte Carlo multi-parameter joint distribution simulation. |
| **CLM-BATT-01** | BESS degradation combines Arrhenius temperature calendar fade and power-law cycle fatigue, feeding SOH into annual storage capacity and financial arbitrage. | `backend/engine/digital_twin.py` | `backend/tests/test_digital_twin.py`<br>`backend/tests/test_financial_validation.py`<br>`backend/tests/test_repeatable_demo.py` | **Level 2 & Level 3** | SOH degradation trajectory (97.69% Year 1 $\rightarrow$ 84.49% Year 10 $\rightarrow$ 78.23% Year 15) benchmarked against closed-form degradation formulas. | Cell manufacturer accelerated life testing data and battery management system (BMS) telemetry. |
| **CLM-BATT-02** | Battery pack replacement cost is scheduled when SOH breaches configured end-of-life threshold (80% or 70%). | `backend/engine/digital_twin.py` | `backend/tests/test_financial_validation.py`<br>`backend/tests/test_repeatable_demo.py` | **Level 2** | Test verifies replacement CapEx incurred in Year 14 under 80% threshold, deferred under 70% threshold. | Historical commercial BESS replacement and warranty claim records. |
| **CLM-CO2-01** | Scope 2 greenhouse gas emissions use national baseline factor of 0.716 kg CO2/kWh, reducing baseline annual emissions from 1,289 to 1,021 tons CO2 (-20.8%). | `backend/engine/digital_twin.py`<br>`backend/api/routes.py` | `backend/tests/test_digital_twin.py`<br>`backend/tests/test_backend.py` | **Level 2 & Level 4** | Factor verified against official Government of India Ministry of Power Central Electricity Authority (CEA) CO2 Baseline Database v19 (Oct 2023). | Third-party accredited ISO 14064-1 / 14064-3 greenhouse gas verification audit. |
| **CLM-TAX-01** | Section 32(1) Indian Income Tax Act 1961 40% Written Down Value (WDV) accelerated depreciation schedule produces cumulative tax shield of $55,615 at 25.17% corporate rate. | `backend/engine/digital_twin.py` | `backend/tests/test_financial_validation.py`<br>`backend/tests/test_independent_financial_benchmarks.py` | **Level 3 & Level 4** | WDV multi-year depreciation schedules verified against statutory rules in Income Tax Rules 1962 (Rule 5 & Appendix I). Modeled as engineering estimate. | Formal legal opinion and corporate tax filing review by a certified Chartered Accountant (CA). |
| **CLM-AUDIT-01** | Decision Center enforces human-in-the-loop managerial signoff (`PENDING_APPROVAL` $\rightarrow$ `APPROVED`/`REJECTED`) with immutable audit trails. | `backend/engine/decision_center.py`<br>`backend/agents/orchestrator.py` | `backend/tests/test_decision_center.py`<br>`backend/tests/test_operational_realism.py`<br>`backend/tests/test_repeatable_demo.py` | **Level 2** | Full lifecycle transitions and operator attribution recorded and verified across API endpoints. | Enterprise single sign-on (SAML/Okta) and WORM cryptographic audit log integration. |
| **CLM-SEC-01** | Industrial Privacy Shield de-identifies plant identifiers, meter IDs, and equipment numbers via reversible tokenization prior to external LLM calls. | `backend/engine/privacy_shield.py` | `backend/tests/test_privacy_shield.py`<br>`backend/tests/test_repeatable_demo.py` | **Level 2** | Unit test verifies regex tokenization masks proprietary parameters and successfully restores them in local memory. | Third-party SOC 2 Type II audit and security penetration test. |
| **CLM-SEC-02** | JWT authentication with role-based access control (Admin, Energy Manager, Operator, Auditor) protects API endpoints, and `/health` probes return 200 OK. | `backend/main.py`<br>`backend/api/routes.py` | `backend/tests/test_deployment_hardening.py`<br>`backend/tests/test_repeatable_demo.py` | **Level 2** | Tests verify token expiration, unauthorized 401 rejections, role restrictions, and health endpoint status. | Automated dynamic application security testing (DAST) and vulnerability scans. |

---

## 3. Disclosed Benchmark Fixtures & Provenance

### 3.1 Historical Benchmark: UCI Steel Industry Dataset
- **Repository Source:** UCI Machine Learning Repository (Steel Industry Energy Consumption Dataset)
- **Observations:** 35,040 rows (1-year duration at 15-minute intervals).
- **Recorded Variables:** Active power, reactive power, power factor, leading/lagging current, ToD tariff status.
- **Role in Platform:** Serves as the primary training and chronological holdout validation dataset for load forecasting algorithms.

### 3.2 Synthetic Benchmark: `STEEL_BENCHMARK_FIXTURE_V1`
- **Facility Type:** Secondary steel smelting plant located in Faridabad Industrial Zone, Haryana, India.
- **Contractual Demand Ceiling:** $450.0\text{ kW}$
- **Connected Transformer Capacity:** $1,250\text{ kW}$ (11 kV / 415 V)
- **Primary Equipment:**
  - Electric Arc Furnace (EAF): 450 kW, 2-hour melt cycle
  - Ladle Refining Furnace (LRF): 300 kW, 2-hour refining cycle
  - Continuous Casting Machine (CCM): 200 kW, 3-hour casting run
- **Grid Supply:** DHBVN HT Industrial Category, two-part ToD tariff.
- **Role in Platform:** Serves as the repeatable, deterministic scenario fixture for end-to-end integration tests, MILP shift optimization, alert deduplication, and the 5-minute demo runner.
- **Explicit Disclosure:** All operational metrics associated with `STEEL_BENCHMARK_FIXTURE_V1` represent **synthetic simulation results**, not live telemetry from an unverified physical factory.

---

## 4. Unresolved Limitations & Road to Level 5 Validation

Before PRAGATI AI can make claims of proven physical factory performance or commercial financial guarantees:

1. **Physical SCADA Telemetry Pilot:** Deploy Modbus TCP / MQTT edge gateway in an operational plant to evaluate forecast accuracy and anomaly detection under real-world harmonic distortion and electrical noise.
2. **Factory Dispatch Trial:** Execute MILP-optimized production schedules on an active shop floor to validate operator compliance, scrap rates, and actual tap-to-tap cycle variations.
3. **Certified ESG Verification:** Undergo third-party ISO 14064 greenhouse gas audit to certify emissions reduction methodologies.
4. **Independent CA Tax Certification:** Have a certified corporate tax counsel certify accelerated depreciation eligibility for specific customer equipment classes.
