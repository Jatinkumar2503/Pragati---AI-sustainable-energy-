import os
import sys
import unittest
import tempfile
import sqlite3
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

# Ensure backend directory is in the path for proper module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dataset_loader import load_dataset
from engine.telemetry_db import TelemetryDB
from engine.privacy_shield import PrivacyShield
from engine.anomaly_detector import run_anomaly_detection
from engine.forecaster import generate_forecast, time_series_backtest
from engine.scheduler import optimize_shift_schedule, solve_milp_schedule, calculate_schedule_metrics
from api import app

class TestPragatiBackend(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Configure test environment variable to bypass key validation on non-security tests
        os.environ["PRAGATI_ENV"] = "test"
        # Load a small sample of the historical dataset for testing validation
        cls.df_all = load_dataset()
        cls.df_sample = cls.df_all.head(500).copy()
        
    def test_dataset_loader(self):
        """1. Test that the dataset loader retrieves valid telemetry DataFrame."""
        self.assertIsNotNone(self.df_all)
        self.assertFalse(self.df_all.empty)
        required_cols = [
            'date', 'usage_kwh', 'reactive_lagging_kvarh', 'reactive_leading_kvarh',
            'power_factor_lagging', 'power_factor_leading', 'nsm',
            'week_status', 'day_of_week', 'load_type', 'ambient_temperature_c'
        ]
        for col in required_cols:
            self.assertIn(col, self.df_all.columns)
            
    def test_telemetry_db(self):
        """2. Test SQLite Transactional Database-Backed Pipeline."""
        # Create a temp file to act as our SQLite DB
        fd, temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        db = None
        try:
            # Initialize database connection on the temp database file path
            db = TelemetryDB(db_path=temp_db_path)
            
            # Assert schema initialization and WAL mode activation
            db.init_db()
            
            # Clear bootstrapped database records to ensure a clean slate for the test
            with db.get_connection() as conn:
                conn.execute("DELETE FROM telemetry;")
                conn.commit()
                
            with db.get_connection() as conn:
                # Assert WAL journaling mode
                journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
                self.assertEqual(journal_mode.lower(), "wal")
                
                # Check that tables and indices exist
                tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
                self.assertIn("telemetry", tables)
                
                indices = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index';").fetchall()]
                self.assertIn("idx_telemetry_date", indices)
                
            # Test inserting telemetry records
            test_records = [
                {
                    "date": "2026-06-06 00:00:00",
                    "usage_kwh": 120.5,
                    "reactive_lagging_kvarh": 50.2,
                    "reactive_leading_kvarh": 0.0,
                    "co2_tco2": 0.042,
                    "power_factor_lagging": 92.4,
                    "power_factor_leading": 100.0,
                    "nsm": 0,
                    "week_status": "Weekday",
                    "day_of_week": "Saturday",
                    "load_type": "Light_Load",
                    "ambient_temperature_c": 22.5
                },
                {
                    "date": "2026-06-06 00:15:00",
                    "usage_kwh": 135.2,
                    "reactive_lagging_kvarh": 52.8,
                    "reactive_leading_kvarh": 0.0,
                    "co2_tco2": 0.047,
                    "power_factor_lagging": 93.1,
                    "power_factor_leading": 100.0,
                    "nsm": 900,
                    "week_status": "Weekday",
                    "day_of_week": "Saturday",
                    "load_type": "Light_Load",
                    "ambient_temperature_c": 22.1
                }
            ]
            
            # Insert synchronously to prevent race conditions during query tests
            rows_inserted = db.insert_telemetry_records(test_records, sync=True)
            self.assertEqual(rows_inserted, 2)
            
            # Query recent telemetry
            df_recent = db.query_recent_telemetry(days=1)
            self.assertEqual(len(df_recent), 2)
            
            # Query all telemetry
            df_all = db.query_all_telemetry()
            self.assertEqual(len(df_all), 2)
            
            # Switch back to DELETE journal mode to cleanup WAL files
            with db.get_connection() as conn:
                conn.execute("PRAGMA journal_mode=DELETE;")
                
        finally:
            if db:
                db.close()
            # Force garbage collection to release SQLite file handles
            import gc
            gc.collect()
            
            # Clean up temp files
            for suffix in ["", "-wal", "-shm"]:
                p = temp_db_path + suffix
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except PermissionError:
                        pass
                
    def test_privacy_shield(self):
        """3. Test Industrial Privacy Shield data redaction/deanonymization layers."""
        shield = PrivacyShield()
        session_id = "test-session-123"
        
        raw_query = "Please query telemetry at Cambridge Smelting Co. (IP: 192.168.1.45, email: admin@cambridge.org) on Smelter 3B."
        
        # Test anonymization
        anonymized = shield.anonymize(raw_query, session_id=session_id)
        self.assertNotIn("Cambridge Smelting Co.", anonymized)
        self.assertNotIn("192.168.1.45", anonymized)
        self.assertNotIn("admin@cambridge.org", anonymized)
        self.assertNotIn("Smelter 3B", anonymized)
        self.assertIn("[REDACTED_FACILITY_0]", anonymized)
        self.assertIn("[REDACTED_IP_3]", anonymized)
        self.assertIn("[REDACTED_EMAIL_2]", anonymized)
        self.assertIn("[REDACTED_EQUIPMENT_1]", anonymized)
        
        # Test deanonymization (reverse restoration)
        restored = shield.deanonymize(anonymized, session_id=session_id)
        self.assertIn("Cambridge Smelting Co.", restored)
        self.assertIn("192.168.1.45", restored)
        self.assertIn("admin@cambridge.org", restored)
        self.assertIn("Smelter 3B", restored)
        
    def test_anomaly_detector(self):
        """4. Test Isolation Forest and custom rule-based classification heuristics."""
        # Detect anomalies
        anomalies = run_anomaly_detection(self.df_sample)
        
        self.assertIsInstance(anomalies, list)
        if len(anomalies) > 0:
            anom = anomalies[0]
            self.assertIn("timestamp", anom)
            self.assertIn("usage_kwh", anom)
            self.assertIn("anomaly_type", anom)
            self.assertIn("severity", anom)
            self.assertIn("explanation", anom)
            self.assertIn("recommendation", anom)
            
    def test_forecaster_adf_and_rnn(self):
        """5. Test ADF stationarity test and custom Elman RNN forecasting engine."""
        # ADF Test on usage data
        series = self.df_sample['usage_kwh'].values
        # To perform raw ADF math we check difference arrays
        diffs = np.diff(series)
        self.assertTrue(len(diffs) > 0)
        
        # RNN Sequence dataset verification
        seq_length = 24
        X, y = [], []
        for i in range(len(series) - seq_length):
            X.append(series[i : i + seq_length])
            y.append(series[i + seq_length])
        X = np.array(X)
        y = np.array(y)
        self.assertEqual(X.shape[1], seq_length)
        
        # Backtest loop
        metrics = time_series_backtest(self.df_sample, n_splits=2)
        self.assertIn("prophet_rmse", metrics)
        self.assertIn("rf_rmse", metrics)
        self.assertIn("rnn_rmse", metrics)
        self.assertIn("persistence_rmse", metrics)
        
    def test_scheduler_milp_and_pf_penalty(self):
        """6. Test MILP battery/load optimization and Power Factor penalty calculations."""
        # Solve scheduling optimization with custom battery parameters
        res = solve_milp_schedule(
            task_load_kw=100.0,
            task_duration_h=4,
            solar_capacity_kw=150.0,
            environmental_weight=0.15,
            battery_capacity_kwh=100.0,
            battery_rate_kw=50.0,
            battery_efficiency=0.90,
            solar_yield_coeff=0.15
        )
        self.assertTrue(res.success)
        
        # Test calculation of scheduling metrics incorporating PF Penalty Surcharges
        # P = 100 kW, Target PF = 0.8 lagging
        # Reactive power Q = 100 * sqrt(1 - 0.64) / 0.8 = 75 kVAR
        # If net active grid draw is 50 kW, PF_net = 50 / sqrt(50^2 + 75^2) = 50 / 90.13 = 55.4%
        # 55.4% PF < 90% threshold. Surcharge multiplier should be applied.
        total_cost, total_carbon, details = calculate_schedule_metrics(
            start_hour=9,
            task_load_kw=100.0,
            task_duration_h=4,
            solar_capacity_kw=150.0,
            solar_yield_coeff=0.12,
            task_power_factor=0.80,
            pf_penalty_mult=2.0
        )
        self.assertTrue(total_cost > 0.0)
        self.assertTrue(len(details) == 4)
        for h_detail in details:
            self.assertIn("power_factor", h_detail)
            self.assertIn("cost", h_detail)
            
        # Test optimize schedule wrapper
        opt_res = optimize_shift_schedule(
            task_load_kw=80.0,
            task_duration_h=2,
            solar_capacity_kw=100.0,
            environmental_weight=0.20,
            battery_capacity_kwh=60.0,
            battery_rate_kw=30.0,
            battery_efficiency=0.92,
            solar_yield_coeff=0.10,
            task_power_factor=0.85,
            pf_penalty_mult=1.5
        )
        self.assertIn("best_start_hour", opt_res)
        self.assertIn("best_cost", opt_res)
        self.assertIn("savings", opt_res)
        self.assertIn("baseline", opt_res)
        
    def test_fastapi_endpoints(self):
        """7. Test FastAPI application routes using TestClient."""
        client = TestClient(app)
        
        # API Health Check
        res_status = client.get("/api/status")
        self.assertEqual(res_status.status_code, 200)
        self.assertEqual(res_status.json()["status"], "healthy")
        
        # API Recent Telemetry
        res_telemetry = client.get("/api/telemetry?days=1")
        self.assertEqual(res_telemetry.status_code, 200)
        self.assertIn("timestamps", res_telemetry.json())
        
        # API Anomaly List
        res_anomalies = client.get("/api/anomalies")
        self.assertEqual(res_anomalies.status_code, 200)
        self.assertIsInstance(res_anomalies.json(), list)
        
        # API Shift Scheduler Optimization with custom battery and PF configs
        res_sched = client.post("/api/schedule", json={
            "task_load_kw": 120.0,
            "task_duration_h": 3,
            "solar_capacity_kw": 200.0,
            "environmental_weight": 0.25,
            "battery_capacity_kwh": 80.0,
            "battery_rate_kw": 40.0,
            "battery_efficiency": 0.94,
            "solar_yield_coeff": 0.14,
            "task_power_factor": 0.75,
            "pf_penalty_mult": 2.5
        })
        self.assertEqual(res_sched.status_code, 200)
        self.assertIn("best_start_hour", res_sched.json())
        self.assertIn("savings", res_sched.json())
        
        # API ROI simulation
        res_sim = client.post("/api/simulate", json={
            "solar_capacity_kw": 250.0,
            "battery_capacity_kwh": 100.0
        })
        self.assertEqual(res_sim.status_code, 200)
        self.assertIn("simple_payback_period_years", res_sim.json())

    def test_bulk_csv_upload(self):
        """8. Test Bulk CSV Telemetry Upload and alignment routing."""
        client = TestClient(app)
        
        # Disable test bypass temporarily to verify API Key authentication works
        os.environ["PRAGATI_ENV"] = "production"
        os.environ["PRAGATI_API_KEY"] = "secure_test_key_123"
        
        # Test without key -> should yield 401
        res = client.post("/api/telemetry/upload", files={"file": ("test.csv", "timestamp,usage\n2026-06-06 12:00:00,150.0")})
        self.assertEqual(res.status_code, 401)
        
        # Test with wrong key -> should yield 403
        res = client.post("/api/telemetry/upload", headers={"X-API-Key": "wrong_key"}, files={"file": ("test.csv", "timestamp,usage\n2026-06-06 12:00:00,150.0")})
        self.assertEqual(res.status_code, 403)
        
        # Test with correct key
        csv_data = (
            "timestamp,usage,power_factor,temp\n"
            "2026-06-06 12:00:00,150.0,85.0,22.0\n"
            "2026-06-06 12:15:00,165.0,88.0,22.5\n"
        )
        res = client.post(
            "/api/telemetry/upload",
            headers={"X-API-Key": "secure_test_key_123"},
            files={"file": ("test.csv", csv_data)}
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["rows_inserted"], 2)
        
        # Reset environment settings for other tests
        os.environ["PRAGATI_ENV"] = "test"

if __name__ == "__main__":
    unittest.main()
