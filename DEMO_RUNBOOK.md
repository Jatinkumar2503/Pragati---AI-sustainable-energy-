# PRAGATI AI — Repeatable Five-Minute Industrial Demo Runbook

> **Target Audience:** Hackathon Judges, Industrial Energy Auditors, Sustainability Engineers  
> **Evaluation Horizon:** 5 Minutes  
> **Dataset Provenance:** Deterministic Synthetic Engineering Benchmark Fixture (`STEEL_BENCHMARK_FIXTURE_V1`)  
> **Status:** Fully Automated, Verified, and Repeatable  

---

## 1. Executive Summary & Value Proposition

PRAGATI AI is an industrial decision-support and energy intelligence platform built for heavy industrial facilities (such as steel smelting, induction melting, and continuous casting). It tackles high-tariff energy wastage, peak demand penalties, power factor surcharges, and decarbonization planning through:

1. **Deterministic Alert Deduplication & Lifecycle Tracking**
2. **Leakage-Free Chronological Holdout Load Forecasting**
3. **MILP Production Task Sequencing with Machine Precedence & Buffer Lags**
4. **15-Year Digital Twin Lifecycle Modeling with Indian Statutory Depreciation (Section 32)**
5. **Traceable Human-in-the-Loop Managerial Signoff with Immutable Audit Trails**

---

## 2. Environment Setup & Clean Cold-Start (30 Seconds)

### Step 2.1: Start the Platform

On Windows:
```cmd
start_pragati.bat
```

On Linux / macOS:
```bash
chmod +x start_pragati.sh
./start_pragati.sh
```

Or directly via Python:
```bash
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

### Step 2.2: Verify Readiness & Reset Demo State

Verify health endpoints:
```bash
curl -s http://127.0.0.1:8000/health
```
*Expected Output:* `{"status":"healthy","dataset_rows":...,"columns":[...]}`

Reset demo state to clean baseline (non-destructive, preserves historical database):
```bash
curl -X POST http://127.0.0.1:8000/api/v1/demo/reset
```
*Expected Output:* `{"status":"success","message":"Demo state successfully reset to initial deterministic baseline.","fixture_id":"STEEL_BENCHMARK_FIXTURE_V1"}`

---

## 3. Five-Minute Live Demonstration Walkthrough

```
  Minute 1                  Minute 2               Minute 3               Minute 4               Minute 5
┌──────────────┐         ┌──────────────┐       ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  Benchmark   │  ────►  │  Anomaly &   │ ───►  │ Trustworthy  │ ───►  │ EAF-LRF-CCM  │ ───►  │ 15-Yr Twin & │
│   Scenario   │         │ Deduplicated │       │ Forecasting  │       │  Precedence  │       │  Managerial  │
│   Overview   │         │    Alerts    │       │ Provenance   │       │ Optimization │       │   Signoff    │
└──────────────┘         └──────────────┘       └──────────────┘       └──────────────┘       └──────────────┘
```

---

### Minute 1: Benchmark Scenario & Facility Context
- **Objective:** Introduce the target industrial plant and establish data provenance.
- **API Call:**
  ```bash
  curl -s http://127.0.0.1:8000/api/v1/demo/scenario
  ```
- **Demonstration Highlights:**
  - **Facility:** Faridabad Alloy & Heavy Steel Works (1,250 kW connected load, 450 kW contractual demand ceiling).
  - **Discom Tariff:** DHBVN High-Tension Industrial Time-of-Day (Peak: $0.18/kWh, Off-Peak: $0.08/kWh).
  - **Equipment Chain:** Electric Arc Furnace (EAF, 450 kW) → Ladle Refining Furnace (LRF, 300 kW) → Continuous Casting Machine (CCM, 200 kW).
  - **Truth in Advertising:** Fixture is clearly flagged as `is_synthetic: true` with provenance `SYNTHETIC_BENCHMARK_FIXTURE_V1`.

---

### Minute 2: Thermal Anomaly & Alert Deduplication
- **Objective:** Demonstrate anomaly detection, deterministic alert deduplication, and operator lifecycle transitions.
- **API Call:**
  ```bash
  curl -X POST http://127.0.0.1:8000/api/v1/demo/step/anomaly
  ```
- **Demonstration Highlights:**
  - **Critical Anomaly:** EAF Substation Transformer breaches temperature threshold (98.4 °C > 85.0 °C) with concurrent power factor drop (0.74 PF).
  - **Deduplication Filter:** When a duplicate spike arrives within 3,600 seconds, PRAGATI AI suppresses duplicate ticket spam (`deduplicated: true`), increments occurrence count, and preserves identity.
  - **Lifecycle Audit:** Tracks `TRIGGERED` → `ACKNOWLEDGED` (Operations Lead) → `RESOLVED` (Energy Manager) with full audit notes.

---

### Minute 3: Holdout Forecasting & Model Limitations
- **Objective:** Showcase ML demand forecasting with strict data provenance and no invented metrics.
- **API Call:**
  ```bash
  curl -s http://127.0.0.1:8000/api/v1/demo/step/forecast
  ```
- **Demonstration Highlights:**
  - **Tri-Model Tournament:** Meta Prophet (Fourier seasonality), Random Forest (24h/168h lags), and NumPy GRU Neural Network.
  - **Rigorous Evaluation:** Evaluated on 2,880 chronological holdout samples across 3 folds with zero data leakage.
  - **Selected Model:** Weighted Ensemble Blend achieves lowest WAPE (0.105) and safe MAPE (10.7%).
  - **Explicit Limitations Stated:** Model explicitly states it does not forecast unplanned mechanical breakdowns and clips near-zero denominators.

---

### Minute 4: Multi-Stage Task Sequencing & Constraint Audit
- **Objective:** Demonstrate the MILP scheduler solving multi-stage industrial dependencies with inter-stage lag buffers.
- **API Call:**
  ```bash
  curl -X POST http://127.0.0.1:8000/api/v1/demo/step/schedule
  ```
- **Demonstration Highlights:**
  - **Machine Precedence:** EAF (2h) must finish before LRF (2h) starts; LRF must finish before CCM (3h) starts.
  - **Inter-Stage Thermal Buffers:** Enforces 1h minimum cooling/degas lag and 3h maximum allowable window.
  - **Constraint Audit Log:**
    - `C-PRECEDENCE-01`: **SATISFIED** (EAF finishes at hour 9, LRF starts at hour 10).
    - `C-BUFFER-LAG-01`: **BINDING** (1-hour buffer respected).
    - `C-DEMAND-01`: **SATISFIED** (peak draw remains under 450 kW contractual ceiling).
    - `C-MAINT-01`: **SATISFIED** (02:00-05:00 maintenance overhaul window completely avoided).
  - **Outcome:** Shifts smelting cycle from high-tariff evening peak ($0.18/kWh) to midday solar surplus window ($0.08/kWh), delivering measurable cost and carbon reductions.

---

### Minute 5: 15-Year Digital Twin & Managerial Signoff
- **Objective:** Present lifecycle financial metrics with Indian statutory tax shields and record human-in-the-loop executive signoff.
- **API Call (Simulation):**
  ```bash
  curl -X POST http://127.0.0.1:8000/api/v1/demo/step/simulation
  ```
- **Demonstration Highlights:**
  - **Asset Sizing:** 350 kW Rooftop Solar PV + 150 kWh LFP BESS.
  - **Indian Statutory Tax Shield:** Models Section 32 40% Written Down Value (WDV) renewable depreciation, delivering substantial early-year cash tax shields.
  - **Battery Aging Feedback:** Semi-empirical degradation model projects battery replacement at Year 14 and end-of-life SOH at 78.2%.
  - **Financial Metrics:** Net Present Value ($641k+ USD / ₹5.36 Cr INR), IRR (48.79%), undiscounted simple payback (2.47 years), after-tax breakeven (2.03 years). Conservative standalone solar baseline reference without dynamic load shifting: NPV $382k+, IRR 18.6%, payback 4.8 years.
  - **Tornado Sensitivity Analysis:** Parameters ranked in descending order of NPV swing (Solar Insolation > Discount Rate > Installed CapEx).

- **API Call (Managerial Signoff):**
  ```bash
  curl -X POST http://127.0.0.1:8000/api/v1/demo/step/approve
  ```
- **Audit Verification:**
  - Chief Sustainability Officer (CSO) records digital approval.
  - Action is committed to the immutable dispatch log.
  - Historical audit trail:
    ```bash
    curl -s http://127.0.0.1:8000/api/v1/decision/history
    ```

---

## 4. One-Click Automated Verification

For automated CI/CD validation or rapid hackathon presentation, run the entire 7-step sequence in a single call:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/demo/run_sequence
```

*Expected Result:*
```json
{
  "demo_manifest": "PRAGATI_AI_5_MINUTE_INDUSTRIAL_DEMO_V1",
  "status": "COMPLETE_AND_VERIFIED",
  "execution_duration_seconds": 1.82,
  "steps_executed": [
    {"step": 1, "title": "Environment Readiness & Demo Reset", "status": "VERIFIED"},
    {"step": 2, "title": "Benchmark Scenario Loaded", "status": "VERIFIED"},
    {"step": 3, "title": "Anomaly Ingestion & Deduplication", "status": "VERIFIED"},
    {"step": 4, "title": "Holdout Forecasting & Limitations", "status": "VERIFIED"},
    {"step": 5, "title": "EAF-LRF-CCM Precedence Optimization", "status": "VERIFIED"},
    {"step": 6, "title": "15-Year Digital Twin Financial Model", "status": "VERIFIED"},
    {"step": 7, "title": "Managerial Signoff & Audit History", "status": "VERIFIED"}
  ]
}
```

---

## 5. Automated Regression Test Command

Execute the dedicated test suite:
```bash
python -m pytest backend/tests/test_repeatable_demo.py -v
```
*Expected Result:* **12 passed in < 7 seconds.**

---

## 6. Known Limitations & Truth in Advertising

1. **Synthetic Engineering Fixture:** Telemetry and task parameters are deterministic benchmark fixtures designed for algorithmic verification. They do not claim live uncalibrated physical hardware feeds.
2. **Engineering Estimates:** Financial metrics (NPV, IRR, cash flows) represent forward-looking engineering estimates under stated assumptions, not guaranteed commercial yields or formal tax opinions.
3. **Statutory Reference:** Renewable depreciation is governed under Section 32(1) read with Rule 5 and Appendix I of the Indian Income Tax Act.
