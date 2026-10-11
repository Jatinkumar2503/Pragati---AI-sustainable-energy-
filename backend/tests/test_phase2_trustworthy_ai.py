"""
PRAGATI AI — Phase 2 Trustworthy AI Outputs Test Suite
Validates:
1. Safe MAPE & WAPE calculations (zero-valued actuals, near-zero actuals, standard series).
2. Forecaster metrics, evaluation sample counts, chronological holdouts, and provenance metadata.
3. Deterministic alert deduplication with configurable suppression window.
4. Alert lifecycle transitions (TRIGGERED -> ACKNOWLEDGED -> RESOLVED) and audit trails.
5. Severity sorting (CRITICAL > HIGH > MEDIUM > LOW > INFO) and recency tie-breaking.
6. Explicit data provenance distinction (historical UCI, synthetic stream, no false physical claims).
7. Repeated API calls on alerts, forecast metrics, and telemetry endpoints.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime
from fastapi.testclient import TestClient

from engine.forecaster import calculate_safe_mape, calculate_wape, generate_forecast
from engine.telemetry_streamer import TelemetryStreamer
from engine.dataset_loader import get_dataset_provenance
from api import app

client = TestClient(app)


class TestTrustworthyForecastingMetrics:
    """Tests for safe metric calculation without data leakage or zero-division explosions."""

    def test_safe_mape_all_zeros(self):
        y_true = np.zeros(20)
        y_pred = np.ones(20) * 10.0
        mape = calculate_safe_mape(y_true, y_pred)
        # When all actuals are zero, MAPE is mathematically undefined; safe MAPE returns None
        assert mape is None

    def test_safe_mape_with_some_zero_actuals(self):
        y_true = np.array([0.0, 100.0, 0.0, 200.0, 50.0])
        y_pred = np.array([10.0, 110.0, 5.0, 190.0, 55.0])
        mape = calculate_safe_mape(y_true, y_pred)
        # Should exclude zeros and compute MAPE on non-zero entries (10%, 5%, 10% -> ~8.33%)
        assert mape is not None
        assert 5.0 < mape < 15.0

    def test_safe_mape_standard_series(self):
        y_true = np.array([100.0, 100.0, 100.0])
        y_pred = np.array([110.0, 90.0, 105.0])
        mape = calculate_safe_mape(y_true, y_pred)
        assert mape is not None
        assert abs(mape - 8.333) < 0.1

    def test_wape_all_zeros(self):
        y_true = np.zeros(10)
        y_pred = np.zeros(10)
        wape = calculate_wape(y_true, y_pred)
        assert wape == 0.0

    def test_wape_standard_series(self):
        y_true = np.array([100.0, 200.0, 300.0])
        y_pred = np.array([110.0, 190.0, 330.0])
        # Sum of absolute errors = 10 + 10 + 30 = 50. Sum of actuals = 600. WAPE % = (50 / 600) * 100 = 8.333%
        wape = calculate_wape(y_true, y_pred)
        assert wape is not None
        assert abs(wape - (50.0 / 600.0) * 100.0) < 0.01

    def test_forecast_provenance_and_metadata(self):
        # Create a small chronological dataset
        dates = pd.date_range("2026-06-01", periods=120, freq="15min")
        df_dummy = pd.DataFrame({
            "date": dates,
            "usage_kwh": 100.0 + 20.0 * np.sin(np.linspace(0, 4 * np.pi, 120))
        })
        res = generate_forecast(df_dummy, forecast_hours=12, backtest_folds=2)
        assert "evaluation_sample_count" in res
        assert res["evaluation_sample_count"] > 0
        assert res["evaluation_sample_count"] == len(res["actuals"])
        assert "evaluation_period" in res
        assert "start" in res["evaluation_period"]
        assert "end" in res["evaluation_period"]
        assert "provenance" in res
        assert res["provenance"]["is_live_data"] is False
        assert "units" in res
        assert "kWh" in res["units"]
        assert "generation_timestamp" in res
        assert "models" in res
        for model in res["models"]:
            assert "name" in model
            assert "model_version" in model
            assert "mae" in model
            assert "rmse" in model
            assert "wape" in model


class TestAlertManagementLifecycle:
    """Tests for deterministic alert deduplication, lifecycle states, and severity sorting."""

    def test_deterministic_alert_deduplication(self):
        streamer = TelemetryStreamer()
        # Clean state for isolated test
        streamer.active_alerts = []
        streamer.alert_history = []
        streamer._next_alert_id = 100

        # First alert trigger
        res1 = streamer.trigger_alert(
            alert_type="Transformer Overheating",
            severity="CRITICAL",
            equipment="Substation Transformer TR-1",
            value=88.5,
            threshold=80.0,
            suppression_window_seconds=1800
        )
        assert res1["is_new"] is True
        assert res1["status"] == "triggered"
        assert res1["duplicate_count"] == 1
        initial_id = res1["alert_id"]

        # Duplicate trigger within suppression window (e.g., 10 seconds later)
        res2 = streamer.trigger_alert(
            alert_type="Transformer Overheating",
            severity="CRITICAL",
            equipment="Substation Transformer TR-1",
            value=89.2,
            threshold=80.0,
            suppression_window_seconds=1800
        )
        assert res2["is_new"] is False
        assert res2["status"] == "deduplicated"
        assert res2["alert_id"] == initial_id
        assert res2["duplicate_count"] == 2
        assert len(streamer.active_alerts) == 1

    def test_alert_lifecycle_audit_trail(self):
        streamer = TelemetryStreamer()
        streamer.active_alerts = []
        streamer.alert_history = []
        streamer._next_alert_id = 200

        res = streamer.trigger_alert(
            alert_type="Low Power Factor",
            severity="HIGH",
            equipment="Induction Arc Furnace AF-01",
            value=0.74,
            threshold=0.85
        )
        alert_id = res["alert_id"]
        assert res["alert"]["status"] == "TRIGGERED"
        assert len(res["alert"]["status_transitions"]) == 1
        assert res["alert"]["status_transitions"][0]["to_status"] == "TRIGGERED"

        # Acknowledge alert
        ack_res = streamer.acknowledge_alert(alert_id, operator_name="Shift Supervisor S. Patel")
        assert ack_res["status"] == "success"
        assert ack_res["alert"]["status"] == "ACKNOWLEDGED"
        assert ack_res["alert"]["acknowledged_by"] == "Shift Supervisor S. Patel"
        assert len(ack_res["alert"]["status_transitions"]) == 2
        assert ack_res["alert"]["status_transitions"][1]["to_status"] == "ACKNOWLEDGED"

        # Resolve alert
        res_res = streamer.resolve_alert(
            alert_id,
            operator_name="Chief Electrical Engineer K. Rao",
            resolution_notes="Engaged APFC capacitor bank Stage 3; PF restored to 0.96 lagging."
        )
        assert res_res["status"] == "success"
        assert res_res["alert"]["status"] == "RESOLVED"
        assert res_res["alert"]["resolved_by"] == "Chief Electrical Engineer K. Rao"
        assert len(res_res["alert"]["status_transitions"]) == 3
        assert res_res["alert"]["status_transitions"][2]["to_status"] == "RESOLVED"

        # Check active alerts does not include RESOLVED
        active = streamer.get_active_alerts()
        active_ids = [a["alert_id"] for a in active]
        assert alert_id not in active_ids

        # Check history retains resolved alert
        history = streamer.get_alert_history()
        hist_ids = [h["alert_id"] for h in history]
        assert alert_id in hist_ids

    def test_alert_severity_sorting(self):
        streamer = TelemetryStreamer()
        streamer.active_alerts = []
        streamer.alert_history = []
        streamer._next_alert_id = 300

        # Trigger LOW, then CRITICAL, then MEDIUM
        streamer.trigger_alert("Minor Deviation", "LOW", "Pump P-1", 10, 8)
        streamer.trigger_alert("Arc Flash Hazard", "CRITICAL", "Switchgear SG-2", 450, 400)
        streamer.trigger_alert("Current Imbalance", "MEDIUM", "Motor M-4", 25, 20)

        active = streamer.get_active_alerts(sort_by_severity=True)
        severities = [a["severity"] for a in active]
        assert severities[0] == "CRITICAL"
        assert severities[1] == "MEDIUM"
        assert severities[2] == "LOW"


class TestDataProvenanceDistinction:
    """Tests verifying provenance metadata and preventing false claims of live industrial hardware."""

    def test_dataset_provenance_explicit_labeling(self):
        prov = get_dataset_provenance()
        assert "source_type" in prov
        assert prov["is_live_physical_hardware"] is False
        assert "units" in prov
        assert prov["units"]["usage_kwh"] == "kWh"
        assert "description" in prov

    def test_telemetry_streamer_synthetic_provenance(self):
        streamer = TelemetryStreamer()
        reading = streamer.get_live_telemetry()
        assert reading["data_source_type"] == "SYNTHETIC_STREAM"
        assert reading["provenance"]["is_live_physical_hardware"] is False
        assert reading["provenance"]["units"]["active_load_kw"] == "kW"
        assert reading["provenance"]["units"]["grid_voltage_v"] == "V"


class TestPhase2APIEndpoints:
    """Tests verifying API contracts, deduplication, and repeated calls."""

    def test_api_alert_trigger_and_deduplication(self):
        payload = {
            "alert_type": "Busbar Harmonic Distortion",
            "severity": "HIGH",
            "equipment": "Main Feed Busbar B-1",
            "value": 11.4,
            "threshold": 8.0,
            "mitigation": "Switch on passive harmonic tuned filter",
            "suppression_window_seconds": 1200
        }

        # First trigger
        r1 = client.post("/api/v1/alerts/trigger", json=payload)
        assert r1.status_code == 200
        data1 = r1.json()
        assert data1["status"] == "triggered"
        assert data1["is_new"] is True
        alert_id = data1["alert_id"]

        # Repeated trigger
        r2 = client.post("/api/v1/alerts/trigger", json=payload)
        assert r2.status_code == 200
        data2 = r2.json()
        assert data2["status"] == "deduplicated"
        assert data2["is_new"] is False
        assert data2["alert_id"] == alert_id
        assert data2["duplicate_count"] >= 2

    def test_api_alert_history_endpoint(self):
        r = client.get("/api/v1/alerts/history?limit=10")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert "alerts" in data
        assert isinstance(data["alerts"], list)

    def test_api_forecast_metrics_provenance(self):
        r = client.get("/api/v1/forecast/metrics")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert data["data_source"] == "HISTORICAL_BENCHMARK_EVALUATION"
        assert data["provenance"]["is_live_data"] is False
        assert "evaluation_sample_count" in data
        assert "generation_timestamp" in data
        assert len(data["models"]) >= 3
        for m in data["models"]:
            assert "rmse" in m
            assert "mae" in m
            assert "wape" in m

    def test_api_telemetry_provenance(self):
        r = client.get("/api/telemetry?days=3")
        assert r.status_code == 200
        data = r.json()
        assert "provenance" in data
        assert data["is_live_telemetry"] is False
        assert data["provenance"]["is_live_physical_hardware"] is False
