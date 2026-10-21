"""
PRAGATI AI — Production Readiness and Operational Validation Test Suite
Validates:
1. Continuous background telemetry ingestion worker lifecycle (start/stop/graceful shutdown).
2. Protection against duplicate telemetry ingestion.
3. Electrical bounds validation and out-of-range flagging.
4. Circuit breaker protection and failure recovery under network partition.
5. SQLite persistence across simulated restarts (decisions & alerts survive).
6. Non-blocking API performance during background polling.
7. System health monitoring endpoint (/api/v1/monitoring/health) distinguishing healthy vs degraded dependencies.
8. Operational metrics monitoring endpoint (/api/v1/monitoring/metrics).
9. Strict read-only hardware safety interlock enforcement (403 Forbidden).
10. Explicit data provenance tagging (preventing simulated readings from being claimed as live physical hardware).
"""

import time
import pytest
import sqlite3
import tempfile
import os
from fastapi.testclient import TestClient

from api import app, DB_INSTANCE
from engine.industrial_telemetry_adapter import (
    IndustrialTelemetryAdapter,
    TelemetryIngestionWorker,
    CircuitBreaker,
    CircuitBreakerOpenError,
    SafetyControlViolationError,
    TELEMETRY_WORKER_INSTANCE,
    TELEMETRY_ADAPTER_INSTANCE
)
from engine.telemetry_db import TelemetryDB
from engine.decision_engine import DecisionEngine
from engine.telemetry_streamer import TelemetryStreamer

client = TestClient(app)

# -----------------------------------------------------------------------------
# 1. Background Telemetry Worker Lifecycle & Duplicate Suppression
# -----------------------------------------------------------------------------
def test_worker_start_stop_lifecycle():
    adapter = IndustrialTelemetryAdapter(enable_simulated_fallback=True)
    worker = TelemetryIngestionWorker(adapter=adapter, poll_interval_s=0.2)
    
    assert not worker.is_running
    start_res = worker.start(poll_interval_s=0.1)
    assert start_res["status"] == "started"
    assert worker.is_running
    
    # Let it poll at least once
    time.sleep(0.3)
    status = worker.get_status()
    assert status["is_running"]
    assert status["total_polls"] >= 1
    assert status["successful_ingestions"] >= 1
    
    stop_res = worker.stop()
    assert stop_res["status"] == "stopped"
    assert not worker.is_running


def test_worker_duplicate_suppression():
    adapter = IndustrialTelemetryAdapter(enable_simulated_fallback=True)
    worker = TelemetryIngestionWorker(adapter=adapter, poll_interval_s=10.0)
    
    # Execute single poll and ingest
    res1 = worker.poll_and_ingest()
    assert res1["status"] == "ingested"
    assert worker.successful_ingestions == 1
    assert worker.duplicate_skips == 0
    
    # Mock adapter to return identical packet
    same_packet = dict(worker.recent_packets[-1])
    adapter.poll = lambda: same_packet
    
    res2 = worker.poll_and_ingest()
    assert res2["status"] == "skipped_duplicate"
    assert worker.successful_ingestions == 1
    assert worker.duplicate_skips == 1


def test_worker_bounds_validation_flagging():
    adapter = IndustrialTelemetryAdapter(enable_simulated_fallback=True)
    worker = TelemetryIngestionWorker(adapter=adapter, poll_interval_s=10.0)
    
    # Mock adapter returning physically invalid voltage (e.g. 50,000 V on low-voltage bus)
    invalid_packet = {
        "timestamp": "2026-10-21 12:00:00",
        "protocol": "MODBUS_TCP",
        "active_load_kw": 250.0,
        "voltage_v": 99999.0, # Outside physical bounds
        "power_factor": 0.95,
        "thd_pct": 2.0,
        "grid_frequency_hz": 50.0
    }
    adapter.poll = lambda: invalid_packet
    
    res = worker.poll_and_ingest()
    assert res["status"] == "ingested"
    assert res["is_physically_plausible"] is False
    assert worker.invalid_readings_flagged >= 1


def test_worker_circuit_breaker_resilience():
    adapter = IndustrialTelemetryAdapter(enable_simulated_fallback=False)
    # Force trip circuit breaker
    adapter.circuit_breaker.state = "OPEN"
    adapter.circuit_breaker.last_failure_time = time.time()
    
    worker = TelemetryIngestionWorker(adapter=adapter, poll_interval_s=10.0)
    res = worker.poll_and_ingest()
    
    assert res["status"] == "circuit_breaker_open"
    assert worker.circuit_breaker_trips >= 1
    assert worker.consecutive_errors >= 1
    assert worker.get_status()["health"] == "DEGRADED"


# -----------------------------------------------------------------------------
# 2. Database Persistence Across Simulated Restarts
# -----------------------------------------------------------------------------
def test_db_persistence_decisions_across_restart(tmp_path):
    test_db_path = str(tmp_path / "test_persistence.db")
    db1 = TelemetryDB(db_path=test_db_path)
    db1.init_db()
    
    engine1 = DecisionEngine(db_instance=db1)
    dec = engine1.generate_recommendation(
        sector="Textiles",
        task_load_kw=100.0,
        task_duration_h=4
    )
    action_id = dec["action_id"]
    engine1.approve_decision(action_id, manager_name="Rupesh Gahlawat", notes="Shift approved for solar alignment")
    db1.close()
    
    # Simulate application restart with a fresh DB connection and fresh engine
    db2 = TelemetryDB(db_path=test_db_path)
    db2.init_db()
    engine2 = DecisionEngine(db_instance=db2)
    
    saved = db2.get_decision(action_id)
    assert saved is not None
    assert saved["status"] == "APPROVED"
    assert saved["approved_by"] == "Rupesh Gahlawat"
    assert saved["sector"] == "Textiles"
    assert any(d.get("action_id") == action_id for d in engine2.decision_history)
    db2.close()


def test_db_persistence_alerts_across_restart(tmp_path):
    test_db_path = str(tmp_path / "test_alerts_persistence.db")
    db1 = TelemetryDB(db_path=test_db_path)
    db1.init_db()
    
    streamer1 = TelemetryStreamer(db_instance=db1)
    trig_res = streamer1.trigger_alert(
        alert_type="Thermal Overload",
        equipment="Furnace Blower F-01",
        value="92.4 °C",
        threshold="85.0 °C",
        severity="CRITICAL"
    )
    alert_id = trig_res["alert_id"]
    streamer1.acknowledge_alert(alert_id, operator_name="Jatin Kumar")
    db1.close()
    
    # Restart simulation
    db2 = TelemetryDB(db_path=test_db_path)
    db2.init_db()
    streamer2 = TelemetryStreamer(db_instance=db2)
    
    all_saved = db2.get_all_alerts()
    saved_alert = next((a for a in all_saved if a.get("alert_id") == alert_id), None)
    assert saved_alert is not None
    assert saved_alert["status"] == "ACKNOWLEDGED"
    assert saved_alert["equipment"] == "Furnace Blower F-01"
    assert any(a.get("alert_id") == alert_id for a in streamer2.active_alerts)
    db2.close()


# -----------------------------------------------------------------------------
# 3. FastAPI Telemetry Worker Endpoints & Non-Blocking Responsiveness
# -----------------------------------------------------------------------------
def test_fastapi_worker_endpoints():
    # 1. Check status
    r = client.get("/api/v1/telemetry/worker/status")
    assert r.status_code == 200
    assert r.json()["status"] == "success"
    
    # 2. Start worker
    r = client.post("/api/v1/telemetry/worker/start", json={"poll_interval_s": 5.0})
    assert r.status_code == 200
    assert r.json()["worker"]["status"] in ("started", "already_running")
    
    # 3. Stop worker
    r = client.post("/api/v1/telemetry/worker/stop")
    assert r.status_code == 200
    assert r.json()["status"] == "success"


def test_api_responsiveness_during_background_polling():
    """Verify that starting the worker does not lock or slow down standard API requests."""
    client.post("/api/v1/telemetry/worker/start", json={"poll_interval_s": 0.5})
    
    t0 = time.time()
    r = client.get("/api/v1/telemetry/adapter/status")
    elapsed = time.time() - t0
    
    assert r.status_code == 200
    assert elapsed < 1.0, f"API took {elapsed:.2f}s during background polling, which is too slow!"
    
    client.post("/api/v1/telemetry/worker/stop")


# -----------------------------------------------------------------------------
# 4. Model and Operational Monitoring Endpoints
# -----------------------------------------------------------------------------
def test_monitoring_health_endpoint():
    r = client.get("/api/v1/monitoring/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert body["system_status"] in ("HEALTHY", "DEGRADED")
    assert "components" in body
    assert "database" in body["components"]
    assert "telemetry_adapter" in body["components"]
    assert "forecasting_engine" in body["components"]
    assert "alert_streamer" in body["components"]
    assert body["components"]["database"]["status"] == "HEALTHY"


def test_monitoring_metrics_endpoint():
    r = client.get("/api/v1/monitoring/metrics")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert "telemetry_monitoring" in body
    assert "alert_deduplication_monitoring" in body
    assert "forecast_model_monitoring" in body
    assert "decision_scheduler_monitoring" in body
    
    # Check deduplication ratio format
    assert "deduplication_efficiency_pct" in body["alert_deduplication_monitoring"]
    assert "mae_kw" in body["forecast_model_monitoring"]
    assert "constraint_satisfaction_rate_pct" in body["decision_scheduler_monitoring"]


# -----------------------------------------------------------------------------
# 5. Safety Control Interlock & Data Provenance
# -----------------------------------------------------------------------------
def test_safety_control_interlock():
    r = client.post("/api/v1/telemetry/adapter/control", json={
        "target_device": "MAIN_FEEDER_BREAKER_01",
        "command": "TRIP_RELAY"
    })
    assert r.status_code == 403
    body = r.json()
    assert body["detail"]["error"] == "SAFETY_CONTROL_VIOLATION"
    assert body["detail"]["is_read_only_enforced"] is True


def test_simulated_data_provenance_labeling():
    adapter = IndustrialTelemetryAdapter(enable_simulated_fallback=True)
    packet = adapter.poll()
    
    provenance = packet.get("provenance", {})
    assert provenance.get("is_read_only") is True
    assert provenance.get("is_live_physical_hardware") is False
    assert "disclaimer" in provenance
    assert "Not claimed as physical factory hardware" in provenance["disclaimer"]
