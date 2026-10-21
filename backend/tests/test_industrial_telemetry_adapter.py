"""
backend/tests/test_industrial_telemetry_adapter.py

Unit and integration tests for IndustrialTelemetryAdapter:
- Modbus-TCP and MQTT simulation/polling
- Physical electrical bounds validation (voltage, PF, load, THD, freq)
- Strict safety interlock: verify execute_control_command raises SafetyControlViolationError (PermissionError)
- CircuitBreaker fault-isolation state machine (CLOSED -> OPEN -> HALF_OPEN)
- Provenance tagging (is_read_only=True, is_live_physical_hardware=False)
- FastAPI endpoints for adapter status, configure, poll, and control command rejection
"""

import time
import pytest
from fastapi.testclient import TestClient

from backend.api import app
from backend.engine.industrial_telemetry_adapter import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    IndustrialTelemetryAdapter,
    SafetyControlViolationError,
    PHYSICAL_VALIDATION_BOUNDS,
    TELEMETRY_ADAPTER_INSTANCE,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def adapter():
    return IndustrialTelemetryAdapter(enable_simulated_fallback=True)


def test_circuit_breaker_transitions():
    """Verify circuit breaker trips to OPEN after consecutive failures and recovers to HALF_OPEN after cooldown."""
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.15)
    assert cb.state == "CLOSED"
    assert cb.can_attempt() is True

    # Record first failure
    cb.record_failure()
    assert cb.consecutive_failures == 1
    assert cb.state == "CLOSED"
    assert cb.can_attempt() is True

    # Record second failure -> should trip to OPEN
    cb.record_failure()
    assert cb.consecutive_failures == 2
    assert cb.state == "OPEN"
    assert cb.can_attempt() is False

    # Wait for cooldown to expire
    time.sleep(0.2)
    assert cb.can_attempt() is True
    assert cb.state == "HALF_OPEN"

    # Success should reset to CLOSED
    cb.record_success()
    assert cb.state == "CLOSED"
    assert cb.consecutive_failures == 0


def test_safety_interlock_rejects_control_commands(adapter):
    """
    CRITICAL SAFETY REQUIREMENT:
    Any attempt to execute a write or control command on industrial equipment
    MUST raise a SafetyControlViolationError (PermissionError) and never reach hardware.
    """
    with pytest.raises(SafetyControlViolationError) as exc_info:
        adapter.execute_control_command(
            target_register=40001,
            command_value=1,
        )
    assert "SAFETY VIOLATION" in str(exc_info.value)
    assert "READ-ONLY" in str(exc_info.value)


def test_modbus_poll_and_provenance(adapter):
    """Verify reading Modbus registers produces validated data with sandbox provenance metadata."""
    adapter.protocol = "MODBUS_TCP"
    packet = adapter.poll()

    assert packet["protocol"] == "MODBUS_TCP"
    assert "active_load_kw" in packet
    assert "voltage_v" in packet
    assert "power_factor" in packet
    assert "thd_pct" in packet
    assert "grid_frequency_hz" in packet

    # Check bounds
    assert 100.0 <= packet["voltage_v"] <= 11000.0
    assert 0.10 <= packet["power_factor"] <= 1.00
    assert 45.0 <= packet["grid_frequency_hz"] <= 65.0
    assert packet["is_physically_plausible"] is True

    # Check provenance
    prov = packet["provenance"]
    assert prov["is_read_only"] is True
    assert prov["is_live_physical_hardware"] is False
    assert "SANDBOX" in prov["data_nature"]


def test_mqtt_poll_and_physical_bounds_validation(adapter):
    """Verify reading MQTT topics validates physical bounds and flags invalid metrics."""
    adapter.protocol = "MQTT"
    packet = adapter.poll()

    assert packet["protocol"] == "MQTT"
    assert packet["provenance"]["is_read_only"] is True
    assert packet["provenance"]["is_live_physical_hardware"] is False

    # Test physical validation on out-of-bounds readings
    invalid_raw = {
        "voltage_v": 50.0,            # Out of bounds (< 100 V)
        "active_load_kw": -20.0,      # Negative load (< 0)
        "power_factor": 1.45,         # Impossible PF (> 1.0)
        "thd_pct": 120.0,             # Out of bounds (> 100%)
        "grid_frequency_hz": 78.5,    # Abnormal grid freq (> 65 Hz)
    }
    is_valid, errors = adapter.validate_reading_bounds(invalid_raw)
    assert is_valid is False
    assert len(errors) == 5


def test_telemetry_fastapi_endpoints(client):
    """Test API integration for adapter status, configuration, polling, and safety rejection."""
    # 1. Get status
    status_res = client.get("/api/v1/telemetry/adapter/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "success"
    adapter_info = status_data["adapter"]
    assert adapter_info["read_only_enforced"] is True
    assert "circuit_breaker" in adapter_info
    assert "configured_protocol" in adapter_info

    # 2. Configure adapter via POST
    config_payload = {
        "protocol": "MODBUS_TCP",
        "host": "192.168.1.100",
        "port": 502,
        "slave_id": 2,
    }
    cfg_res = client.post("/api/v1/telemetry/adapter/configure", json=config_payload)
    assert cfg_res.status_code == 200
    cfg_data = cfg_res.json()
    assert cfg_data["status"] == "success"
    assert "MODBUS_TCP" in cfg_data["message"]

    # 3. Poll adapter via POST
    poll_res = client.post("/api/v1/telemetry/adapter/poll")
    assert poll_res.status_code == 200
    poll_data = poll_res.json()
    assert poll_data["status"] == "success"
    packet = poll_data["telemetry_packet"]
    assert packet["protocol"] == "MODBUS_TCP"
    assert packet["provenance"]["is_read_only"] is True
    assert packet["provenance"]["is_live_physical_hardware"] is False
    assert "active_load_kw" in packet

    # 4. Attempt control command -> MUST return 403 Forbidden
    control_res = client.post(
        "/api/v1/telemetry/adapter/control",
        json={"target_device": "CB-01", "command": "TRIP"}
    )
    assert control_res.status_code == 403
    control_data = control_res.json()["detail"]
    assert control_data["error"] == "SAFETY_CONTROL_VIOLATION"
    assert control_data["is_read_only_enforced"] is True
