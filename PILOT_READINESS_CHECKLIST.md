# PRAGATI AI — Industrial Pilot Readiness & Safety Commissioning Checklist
**Standard Operating Procedure & Engineering Safety Protocol**  
**Team Polaris | CodeWord 2.0 Hackathon**

---

## 1. Safety Mandate & Scope Boundary

> [!CAUTION]
> **READ-ONLY TELEMETRY INTERLOCK ENFORCEMENT:**  
> PRAGATI AI is engineered as an intelligent **Decision-Support Platform**, NOT an autonomous supervisory control system (SCADA/DCS actuator). Under no circumstances shall automated control or write commands be dispatched to industrial relays, breakers, VFDs, or PLCs without physical interlocks, hardware bypass keys, and formal on-site electrical engineering authorization. The software maintains a hardcoded `SafetyControlViolationError` interlock blocking all write operations.

---

## 2. Nine-Stage Commissioning Protocol

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                INDUSTRIAL PILOT STAGES                                  │
├─────────────────┬─────────────────┬──────────────────┬─────────────────┬───────────────┤
│ 1. Site Access  │ 2. Read-Only    │ 3. Signal & Unit │ 4. Time Sync &  │ 5. 30-Day     │
│    & Network    │    Commissioning│    Mapping       │    Data Quality │    Baseline   │
├─────────────────┼─────────────────┼──────────────────┼─────────────────┼───────────────┤
│ 6. Shadow-Mode  │ 7. Forecast &   │ 8. Schedule      │ 9. Sign-off &   │               │
│    Evaluation   │    Alert Review │    Feasibility   │    Rollback     │               │
└─────────────────┴─────────────────┴──────────────────┴─────────────────┴───────────────┘
```

---

### Stage 1: Authorized Site Access & Network Firewall Approval
- [ ] **Facility Work Permit:** Obtain signed Electrical Work Permit (EWP) and IT/OT cybersecurity clearance from the Plant Operations Manager.
- [ ] **Network Segmentation:** Ensure PRAGATI AI edge gateway / telemetry listener is placed on a dedicated, demilitarized OT VLAN (e.g. VLAN 40 - Energy Management System) separated from corporate office networks.
- [ ] **Firewall Whitelisting:**
  - Inbound: Strictly prohibited from public internet into the factory OT bus.
  - Outbound/Internal: Whitelist Modbus-TCP port `502` or MQTT TLS port `8883` exclusively between the PRAGATI telemetry adapter and authorized digital multi-function meters (MFMs).
- [ ] **Zero Default Passwords:** Verify that industrial routers, switches, and edge gateways have default passwords revoked and replaced with enterprise-grade credentials.

---

### Stage 2: Read-Only Telemetry Commissioning
- [ ] **Physical Read-Only Hardware Configuration:** If connecting via RS-485 to Ethernet bridges (e.g. Moxa MB3180), enable hardware DIP switch / jumper for **RS-485 2-Wire Read-Only Listening**.
- [ ] **Protocol Function Code Whitelisting:**
  - Allowed Modbus Function Codes: `0x03` (Read Holding Registers), `0x04` (Read Input Registers).
  - Explicitly Blocked Modbus Function Codes: `0x05` (Write Single Coil), `0x06` (Write Single Register), `0x0F` (Write Multiple Coils), `0x10` (Write Multiple Registers).
- [ ] **Circuit Breaker Verification:** Test that transient network disconnection trips the software circuit breaker to `OPEN` within 3 failed polls without hanging the web API.

---

### Stage 3: Signal Mapping & Electrical Unit Validation
- [ ] **CT & PT Ratio Verification:**
  - Verify Current Transformer (CT) primary and secondary ratings (e.g. 800:5 A).
  - Verify Potential Transformer (PT) primary and secondary ratings (e.g. 11 kV : 415 V).
  - Confirm whether the energy meter reports raw secondary values or scaled primary values to prevent 100x or 1000x magnitude discrepancies.
- [ ] **Register Alignment:**
  - Confirm endianness (Big-Endian vs Little-Endian / Word-Swapped IEEE 754 float).
  - Validate registers for:
    - Active Power ($P$, in kW)
    - Reactive Power ($Q$, in kVAr)
    - Power Factor ($\cos \phi$)
    - Grid Voltage ($V_{L-L}$ and $V_{L-N}$)
    - Total Harmonic Distortion ($\text{THD}_V$ and $\text{THD}_I$, in %)
    - Grid Frequency ($f$, in Hz)
- [ ] **Physical Electrical Bounds Sanity Check:**
  - Voltage: 100.0 V to 11,000.0 V
  - Power Factor: 0.10 to 1.00
  - Active Load: 0.0 to 50,000.0 kW
  - Frequency: 45.0 Hz to 65.0 Hz

---

### Stage 4: Time Synchronization & Data Quality
- [ ] **Time Synchronization:** Synchronize industrial energy meters, RTUs, and PRAGATI host servers to a local stratum-1 or stratum-2 NTP server or IEEE 1588 Precision Time Protocol (PTP) master clock. Max acceptable drift: $\le 1.0 \text{ s}$.
- [ ] **Sample Rate Verification:** Configure telemetry polling at exactly 15-minute intervals (or 1-minute sub-metering) aligned with DISCOM tariff integration blocks.
- [ ] **Data Quality Filter:** Verify automatic tagging of missing packets, duplicate timestamp suppression, and bad telemetry flags in `/api/v1/monitoring/metrics`.

---

### Stage 5: Baseline Measurement Period
- [ ] **30-Day Uninterrupted Logging:** Run continuous background telemetry ingestion in passive logging mode for a minimum of 30 days.
- [ ] **Operating Cycle Coverage:** Capture both regular weekday production runs, weekend low-load shifts, maintenance overhauls, and statutory holidays.
- [ ] **Persistence Verification:** Verify telemetry samples, carbon accounting logs (Scope 1, 2, and 3), and transformer temperatures persist across server and container restarts.

---

### Stage 6: Shadow-Mode Evaluation
- [ ] **Passive Advisory Operation:** PRAGATI AI runs in **Shadow Mode** where all AI load forecasts, anomaly alerts, and MILP schedule shift recommendations are displayed in the Decision Center without executing physical load shifts.
- [ ] **Human Dispatcher Log Comparison:** Compare PRAGATI AI shift recommendations against real shift changes implemented by plant operators.
- [ ] **Cost Avoidance Estimation:** Calculate theoretical financial savings ($ per batch, monthly recurring savings, peak demand charge penalties avoided) under shadow evaluation.

---

### Stage 7: Forecast and Alert Review
- [ ] **Model Accuracy Audit:**
  - Verify Random Forest / persistence load forecast accuracy against measured physical load.
  - Threshold: Mean Absolute Percentage Error (MAPE) $< 6.0\%$, RMSE improvement $> 50\%$ over naive persistence baseline.
- [ ] **Alert False-Positive Rate:**
  - Audit thermal overload, power factor drop, and phase imbalance alerts.
  - Verify that deduplication windows suppress nuisance chime cascades while maintaining 100% detection of genuine threshold breaches.

---

### Stage 8: Production Schedule Feasibility Review
- [ ] **Constraint Audit Log Review:** Inspect `/api/v1/decision/overview` to ensure every scheduled production sequence satisfies all 7 industrial physical constraints:
  - `C-DEMAND-01`: Peak draw $\le$ Contract Demand Ceiling (e.g. 450 kW).
  - `C-MAINT-01`: Prohibited Overhaul Windows avoided (e.g. 02:00-05:00).
  - `C-PF-01`: Displacement Power Factor $\ge 0.90$.
  - `C-PRECEDENCE-01`: Multi-Stage machine sequencing is acyclic and strictly causal.
  - `C-THROUGHPUT-01`: 100% of production batch quotas fulfilled before dispatch deadline.
  - `C-BESS-SOC-01`: Battery storage operated safely between 20% and 90% SoC.
  - `C-THERMAL-01`: Transformer temperatures stay below $85^\circ\text{C}$ nominal rating.

---

### Stage 9: Operator Sign-off & Rollback Procedures
- [ ] **Managerial Decision Workflow:** Verify human-in-the-loop approval and rejection modal operation (`POST /api/v1/decision/approve` and `POST /api/v1/decision/reject`).
- [ ] **Operator Training:** Train shift supervisors, energy managers, and electrical technicians on reviewing Decision Center evidence and audit trails.
- [ ] **Immediate Rollback Protocol:**
  - If a recommended schedule adjustment causes unexpected operational friction on the shop floor, the shift supervisor can reject the decision with one click, providing an audit explanation.
  - Reverting automatically restores standard fixed-shift schedules.
- [ ] **Emergency Disconnect:** Document clear physical disconnect procedure (unplugging OT Ethernet cable or stopping PRAGATI Docker container) with zero disruption to factory production lines.

---

## 3. Pilot Sign-Off Certificate Template

```
================================================================================
                    PRAGATI AI INDUSTRIAL PILOT AUTHORIZATION
================================================================================
Facility Name:        __________________________________________________________
Plant Location:       __________________________________________________________
Lead Electrical Eng:  ______________________________  Emp ID: __________________
Plant Operations Mgr: ______________________________  Date:   __________________

[ ] Stage 1: Site Access & OT Network Whitelist Verified
[ ] Stage 2: Read-Only Modbus-TCP / MQTT Communication Confirmed
[ ] Stage 3: CT/PT Ratios & Electrical Bounds Audited
[ ] Stage 4: NTP Clock Synchronization (<= 1.0s) Confirmed
[ ] Stage 5: 30-Day Baseline Telemetry Logged
[ ] Stage 6: Shadow Mode Completed with Zero Safety Incidents
[ ] Stage 7: Forecast MAPE < 6.0% and Deduplication Validated
[ ] Stage 8: MILP Constraint Audits Fully Satisfied
[ ] Stage 9: Operator Training & Rollback Procedures Established

Authorization:
The undersigned hereby authorizes PRAGATI AI to operate in Decision-Support
Advisory Mode for the specified industrial facility.

Signature (Plant Operations Manager): ___________________________ Date: _________
Signature (Chief Electrical Engineer): ___________________________ Date: _________
================================================================================
```
