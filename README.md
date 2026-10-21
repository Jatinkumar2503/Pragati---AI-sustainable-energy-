# PRAGATI AI 🌿
### AI-Powered Industrial Energy Intelligence & Decision-Support Platform
**CodeWord 2.0 Hackathon Submission**  
**Team:** Polaris  
**Team Leader:** Jatin Kumar  
**Team Members:** Rupesh Gahlawat, Aadarsh Raj  

---

## 🎯 Executive Overview & Product Positioning

> **"PRAGATI AI is an autonomous industrial energy intelligence and operational decision-support platform for modern manufacturing facilities. It monitors energy consumption and power quality, forecasts multi-horizon load curves, detects electrical anomalies with duplicate suppression, optimizes production scheduling under physical constraints, models renewable digital twin investments with statutory Indian tax benefits, and requires human-in-the-loop managerial approval before any dispatch action is committed to an immutable audit trail."**

PRAGATI AI moves beyond passive dashboards. It pairs machine learning forecasting (Prophet, Random Forest, RNN) and mathematical optimization (SciPy MILP with strict precedence and machine mutual exclusion) with human-in-the-loop decision-making and statutory Indian regulatory norms (BEE PAT Cycle-VII, Central Electricity Authority CO₂ factors, and Section 32 40% WDV accelerated depreciation).

---

## 🏗️ System Architecture & 9-Stage E2E Workflow

```text
[Industrial Telemetry / CSV Ingestion]
       │ (Modbus-TCP / MQTT / CSV — Read-Only Safety Interlock)
       ▼
[Data Validation & Preprocessing] (Missing imputation, physical bounds checking, IEEE 519 compliance)
       │
       ├──► [Load Forecasting Engine] (Prophet + Random Forest + GRU with Chronological Holdout)
       │
       └──► [Anomaly Detection & Triage] (Isolation Forest, MAD, CUSUM drift + 15-min Deduplication Window)
               │
               ▼
[MILP Production Scheduler] (Multi-stage EAF ➔ LRF ➔ CCM DAG, Maintenance Windows, 20%-90% BESS Buffer)
       │
       ▼
[Constraint Feasibility Audit] (Strict verification: Zero violations required before presenting savings)
       │
       ▼
[Renewable Digital Twin] (Solar PV + BESS lifecycle simulation, NPV, IRR, Section 32 40% WDV Tax Shield)
       │
       ▼
[Decision Center] (Transparent XAI recommendations with clear rationale and assumptions)
       │
       ▼
[Human-in-the-Loop Decision] (Managerial Approve or Reject with mandatory operational reasoning)
       │
       ▼
[Dynamic Audit Trail] (Traceable historical log with actor, timestamps, financial impact, and resolution notes)
```

---

## 🚀 Key Technical Capabilities

### 1. Robust Multi-Stage Scheduling (MILP)
- **Mathematical Solver**: Mixed-Integer Linear Program formulated with SciPy `milp` optimizing production shifts over a 24-hour horizon.
- **Precedence & Buffer Constraints**: Supports multi-stage DAGs (e.g., Electric Arc Melting $\rightarrow$ Ladle Refining $\rightarrow$ Continuous Casting) with configurable minimum and maximum thermal buffer lag windows ($[\tau_{min}, \tau_{max}]$).
- **Physical Operational Constraints**: Enforces contract maximum demand limits, machine mutual exclusion (no concurrent jobs on the same machine), scheduled plant maintenance overhaul blackouts, and BESS 20%–90% State-of-Charge battery health buffers.
- **Feasibility Verification**: Independent constraint audit engine evaluates every schedule. The platform **strictly prohibits** claiming cost savings from infeasible schedules.

### 2. Time-Series Forecasting & Anomaly Detection
- **Multi-Model Tournament**: Compares Meta Prophet, Random Forest Regressor, and Autoregressive RNN models using strict chronological train/test separation (no future data leakage).
- **Anomaly Detection**: Multidimensional Isolation Forest detecting off-shift consumption surges, low power factor ($PF < 0.85$), and uncompensated reactive power draw.
- **Alert Deduplication**: Deterministic 15-minute suppression window triages repeated threshold alarms, tracking event lifecycle (`TRIGGERED` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `RESOLVED`) without alert fatigue.
- **Sensor Drift Tracking**: Page's Cumulative Sum (CUSUM) change-point detector identifies persistent meter calibration drift and phase imbalances.

### 3. Digital Twin & Financial Model Verification
- **Dual-Currency Accounting**: Synchronized INR (₹) and USD ($) financial metrics using benchmark exchange rate (₹83.0 – ₹83.50 / USD).
- **Comprehensive Lifecycle Financials**: Computes Initial Capex, Annual Energy Cost Savings, Simple Payback Period, Net Present Value (NPV), and Internal Rate of Return (IRR).
- **Statutory Indian Tax Depreciation**: Incorporates Indian Income Tax Act 1961 Section 32(1) accelerated depreciation (40% Written Down Value for solar/renewables vs. 15% standard corporate WDV), with explicit disclaimers regarding Section 115BAA corporate tax regimes.
- **Electrochemical Battery Degradation**: Arrhenius temperature-dependent calendar aging combined with cycle depth-of-discharge ($\Delta DOD$) fatigue modeling.

### 4. Continuous Industrial Telemetry Ingestion Worker & Protocols
- **Background Worker**: Multi-threaded, non-blocking telemetry ingestion daemon (`TelemetryIngestionWorker`) polling field meters on a configurable schedule (default 15 minutes = 900s).
- **Protocol Support**: Read-only Modbus-TCP register polling (0x04 Input Registers, 0x03 Holding Registers) and MQTT telemetry consumer.
- **Hardware Safety Interlock**: Enforces physical read-only safety; any attempted actuator write command explicitly raises a `SafetyControlViolationError (PermissionError)` (HTTP 403 Forbidden).
- **Fault Isolation**: Built-in 3-state Circuit Breaker (`CLOSED`, `OPEN`, `HALF_OPEN`) prevents hanging API worker threads during field network partitions.
- **Duplicate Suppression**: Deterministic MD5 reading fingerprinting suppresses duplicate IoT packet ingestion.
- **Physical Bounds Validation**: Validates telemetry against physical electrical limits (voltage 100–11,000 V, frequency 45–65 Hz, power factor 0.10–1.00, THD 0–100%).
- **Explicit Provenance**: Every telemetry packet is explicitly tagged with `is_read_only=True` and `is_live_physical_hardware=False` (labeled sandbox/replay).
- **Worker Management API**: Start (`POST /api/v1/telemetry/worker/start`), Stop (`POST /api/v1/telemetry/worker/stop`), and Status (`GET /api/v1/telemetry/worker/status`).

### 5. Data Persistence & Recovery Across Restarts
- **SQLite WAL Architecture**: High-concurrency Write-Ahead Logging (WAL) with immediate transactional write safety and exponential backoff locking retries.
- **Decision History Persistence**: All managerial recommendations, approval signatures, and rejection rationales are persisted in the `decision_history` table and restored across server restarts.
- **Alert Lifecycle Persistence**: Active alerts, duplicate occurrence counts, and full operator transition audit histories persist in the `alerts` table.
- **Operational Metrics Store**: Tracks continuous model drift, forecast error, and background worker performance in `operational_metrics`.

### 6. System & Operational Monitoring (Observability)
- **Comprehensive Health Check (`GET /api/v1/monitoring/health`)**: Multi-component diagnostic evaluating SQLite database, telemetry adapter, circuit breaker, forecasting engine, and alert streamer. Distinguishes `HEALTHY` vs `DEGRADED` states without API disruption.
- **Operational Metrics (`GET /api/v1/monitoring/metrics`)**: Real-time reporting on telemetry freshness, bad readings, alert deduplication efficiency ratio, Random Forest MAE/RMSE drift vs persistence baseline, and MILP solver execution times.

### 7. Decision Center & Dynamic Audit History
- **Human-in-the-Loop Review**: Industrial managers review AI recommendations with understandable explanations, assumptions, and financial/carbon impact.
- **Traceable Actions**: Supports both managerial Approval and Rejection with operational justification.
- **Live Aggregated Audit Trail**: The `/api/v1/audit/logs` endpoint dynamically merges decision approvals/rejections, alert lifecycle events, and regulatory baseline compliance records.

---

## ⚙️ Installation & Startup

### Prerequisites
- **Python 3.10+** (Tested on Python 3.14.6 x64 on Windows)
- Modern web browser (Chrome, Edge, Firefox)

### Quick Launch (Windows)
Double-click `start_pragati.bat` or run from terminal:
```cmd
start_pragati.bat
```

### Manual Installation & Server Startup
```bash
# 1. Clone repository & change directory
cd "c:\Users\Asus\Documents\sustainable platform"

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Create .env from template (if not already present)
copy .env.example .env

# 4. Start FastAPI server with live dashboard static mounting
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
```

### Accessing the Application
- **Interactive Web Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Reference**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **System Monitoring Health**: [http://127.0.0.1:8000/api/v1/monitoring/health](http://127.0.0.1:8000/api/v1/monitoring/health)
- **Operational Metrics Dashboard**: [http://127.0.0.1:8000/api/v1/monitoring/metrics](http://127.0.0.1:8000/api/v1/monitoring/metrics)

---

## 🧪 Automated Testing & Verification

The test suite covers unit tests, mathematical optimization benchmarks, financial models, safety interlocks, background workers, persistence across restarts, and complete end-to-end integration workflows.

### Running the Complete Test Suite
```bash
python -m pytest backend/tests -v
```

### Verified Test Results
- **Total Test Cases**: **182 passed** (0 failed, 0 errors, 0 skipped)
- **Execution Time**: ~5m 04s (includes real Prophet cross-validation, SciPy MILP solves, and background worker concurrency tests)
- **Historical Baseline**: 152 tests passed
- **Phase 8 Regression Baseline**: 170 tests passed
- **Final Production Hardening**: **+12 new tests** (`test_production_readiness.py`)

```text
================= 182 passed, 1 warning in 304.12s (0:05:04) ==================
```

---

## 🎬 Running the Repeatable Multi-Stage Demo

PRAGATI AI includes an automated 5-minute repeatable demonstration controller executing the complete industrial intelligence sequence:

```bash
# Execute full demo sequence via API
curl -X POST http://127.0.0.1:8000/api/v1/demo/run_sequence
```

Or step-by-step:
1. `GET  /api/v1/demo/scenario` — Loads versioned Faridabad Steel smelting benchmark fixture.
2. `POST /api/v1/demo/step/anomaly` — Triggers electrical anomaly with duplicate suppression.
3. `GET  /api/v1/demo/step/forecast` — Evaluates Prophet and Random Forest load forecasting.
4. `POST /api/v1/demo/step/schedule` — Optimizes EAF $\rightarrow$ LRF $\rightarrow$ CCM sequence with maintenance blackout.
5. `POST /api/v1/demo/step/simulation` — Computes 15-year Digital Twin solar/BESS lifecycle economics.
6. `POST /api/v1/demo/step/approve` — Records managerial approval into dynamic audit log.

---

## 🔐 Security & Production Hardening

- **Authentication & RBAC**: Configurable API key (`X-API-Key`) and JWT bearer token authorization protecting administrative endpoints.
- **Safety Interlocks**: Industrial Telemetry Adapter inhibits all actuator control and setpoint write commands, preventing unauthorized physical hardware intervention.
- **Circuit Breakers**: Fault-isolation pattern trips after 3 consecutive connection failures to prevent backend resource exhaustion.
- **Input Validation**: Pydantic v2 schemas reject non-positive task durations, invalid timestamps, impossible lag windows, and out-of-bounds electrical metrics.
- **Differential Privacy Shield**: Laplace mechanism protects proprietary factory consumption data during aggregate benchmark reporting.
- **Environment Secrets**: Zero hardcoded credentials; template configuration provided in `.env.example`.

---

## 📋 Data Provenance & Statutory Disclaimers

1. **BEE PAT Cycle-VII Norms**: Specific Energy Consumption (SEC) benchmark values derived from authentic Bureau of Energy Efficiency regulations for Indian designated consumers (Iron & Steel: 0.585 TOE/ton, Cement: 68.5 kWh/ton).
2. **CEA Grid Emission Factors**: Scope 2 emission intensity values derived from Central Electricity Authority CO₂ Baseline Database v20.0 (Northern: 0.724 kg/kWh, Western: 0.758 kg/kWh, Southern: 0.702 kg/kWh).
3. **Simulated Financial Outcomes**: Digital Twin outputs represent simulated lifecycle scenario projections based on modeled solar irradiance and time-of-use tariffs, not guaranteed real-world commercial returns.
4. **Income Tax Act Disclaimers**: Renewable asset depreciation is modeled under Section 32(1) (40% WDV); actual eligibility depends on the facility's elected corporate tax regime (e.g., Section 115BAA concessional rate vs. standard rate).

---

## 👥 Polaris Team & Hackathon Submission

- **Event**: CodeWord 2.0 Hackathon
- **Team**: Polaris
- **Team Leader**: Jatin Kumar
- **Team Members**: Rupesh Gahlawat, Aadarsh Raj
- **Repository**: [Jatinkumar2503/Pragati---AI-sustainable-energy-](https://github.com/Jatinkumar2503/Pragati---AI-sustainable-energy-)
