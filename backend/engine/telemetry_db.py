import os
import sys
import json
import sqlite3
import logging
import contextlib
import queue
import threading
import time
import pandas as pd

# Ensure backend folder is in path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dataset_loader import load_dataset
from engine.scheduler import get_carbon_intensity
from engine.base_db import BaseDatabase

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "pragati_telemetry.db")

class TelemetryDB(BaseDatabase):
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = db_path
        # Ensure data folder exists
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"Created DB directory: {db_dir}")
            
        # Thread-safe batch buffer queue for high-throughput IoT writes
        self.ingest_queue = queue.Queue()
        self.stop_worker = threading.Event()
        self.worker_thread = None
        self._start_worker_thread()
            
    @contextlib.contextmanager
    def get_connection(self):
        """
        Creates a connection to the SQLite database, configures high-concurrency WAL mode,
        uses IMMEDIATE transactions for write-safety, and ensures connection closure.
        """
        conn = sqlite3.connect(self.db_path, isolation_level="IMMEDIATE")
        conn.row_factory = sqlite3.Row
        
        # Enable Write-Ahead Logging (WAL) for high concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        # Set busy timeout to 5000ms (avoids SQLite database locked exceptions)
        conn.execute("PRAGMA busy_timeout=5000;")
        
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def execute_with_retry(self, action, max_retries=5, initial_backoff=0.05):
        """
        Executes a database write action with exponential backoff retries if database is locked.
        """
        retries = 0
        while True:
            try:
                return action()
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and retries < max_retries:
                    retries += 1
                    sleep_time = initial_backoff * (2 ** retries)
                    logger.warning(f"Database is locked, retrying {retries}/{max_retries} after {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                else:
                    raise

    def _start_worker_thread(self):
        self.worker_thread = threading.Thread(target=self._batch_write_worker, daemon=True)
        self.worker_thread.start()
        logger.info("Started asynchronous telemetry DB batch write worker thread.")

    def _batch_write_worker(self):
        """
        Background worker that polls the ingest queue and flushes records in bulk transactions.
        """
        while not self.stop_worker.is_set():
            batch = []
            start_time = time.time()
            # Gather up to 200 records or flush after 100ms
            while len(batch) < 200 and (time.time() - start_time) < 0.1:
                try:
                    record = self.ingest_queue.get(timeout=0.01)
                    batch.append(record)
                    self.ingest_queue.task_done()
                except queue.Empty:
                    continue
            
            if batch:
                try:
                    self._flush_batch_to_db(batch)
                except Exception as e:
                    logger.error(f"Async batch DB write worker failed to flush: {e}")
            else:
                time.sleep(0.01)
        
        # Flush any remaining items in the queue before exiting
        remaining_records = []
        while not self.ingest_queue.empty():
            try:
                record = self.ingest_queue.get_nowait()
                remaining_records.append(record)
                self.ingest_queue.task_done()
            except queue.Empty:
                break
        if remaining_records:
            try:
                self._flush_batch_to_db(remaining_records)
                logger.info(f"Async worker flushed {len(remaining_records)} remaining records on shutdown.")
            except Exception as e:
                logger.error(f"Async worker failed to flush remaining records on shutdown: {e}")

    def _flush_batch_to_db(self, records):
        """
        Performs direct transactional bulk SQL inserts.
        """
        query = """
            INSERT OR IGNORE INTO telemetry (
                date, usage_kwh, reactive_lagging_kvarh, reactive_leading_kvarh,
                co2_tco2, power_factor_lagging, power_factor_leading,
                nsm, week_status, day_of_week, load_type, ambient_temperature_c,
                scope1_co2_kg, scope2_co2_kg, scope3_co2_kg
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            );
        """
        param_list = []
        for r in records:
            usage = float(r.get("usage_kwh", 0.0))
            
            # Resolve hour for dynamic Scope 2 grid intensity calculation
            try:
                dt_val = pd.to_datetime(r.get("date"))
                hour_val = dt_val.hour
            except Exception:
                hour_val = 12
                
            # Scope 2: Dynamic Grid Intensity
            scope2_intensity = get_carbon_intensity(hour_val)
            scope2 = float(r.get("scope2_co2_kg", round(usage * (scope2_intensity / 1000.0), 3)))
            
            # Scope 1: Furnace thermodynamic lag and natural gas combustion
            if getattr(self, "_last_usage_smooth", None) is None:
                try:
                    with self.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT scope1_co2_kg FROM telemetry ORDER BY date DESC LIMIT 1;")
                        row = cursor.fetchone()
                        if row and row[0] is not None:
                            self._last_usage_smooth = row[0] / (0.062176 * 1.93)
                except Exception:
                    pass

            if getattr(self, "_last_usage_smooth", None) is None:
                self._last_usage_smooth = usage
            else:
                self._last_usage_smooth = 0.8 * self._last_usage_smooth + 0.2 * usage
                
            calc_scope1 = round(self._last_usage_smooth * 0.062176 * 1.93, 3)
            scope1 = float(r.get("scope1_co2_kg", calc_scope1))
            
            # Scope 3: Supply chain logistics
            nsm_val = int(r.get("nsm", hour_val * 3600))
            scope3 = float(r.get("scope3_co2_kg", round(usage * 0.220 + 5.0 * (nsm_val / 86400.0), 3)))
            
            # Total CO2 in metric tons (tCO2)
            calc_co2_tco2 = round((scope1 + scope2 + scope3) / 1000.0, 4)
            co2_tco2 = float(r.get("co2_tco2", calc_co2_tco2))
            
            param_list.append((
                r.get("date"),
                usage,
                float(r.get("reactive_lagging_kvarh", 0.0)),
                float(r.get("reactive_leading_kvarh", 0.0)),
                co2_tco2,
                float(r.get("power_factor_lagging", 100.0)),
                float(r.get("power_factor_leading", 100.0)),
                nsm_val,
                r.get("week_status", "Weekday"),
                r.get("day_of_week", "Monday"),
                r.get("load_type", "Light_Load"),
                float(r.get("ambient_temperature_c", 20.0)),
                scope1,
                scope2,
                scope3
            ))
            
        def write_action():
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, param_list)
                conn.commit()
                
        self.execute_with_retry(write_action)

    def init_db(self):
        """
        Creates the table schema, adds indices, applies dynamic column migrations, 
        and bootstraps historical CSV data if empty.
        """
        logger.info(f"Initializing telemetry database at: {self.db_path}")
        with self.get_connection() as conn:
            # Create Table with Scope 1, 2, and 3 columns
            conn.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE,
                    usage_kwh REAL,
                    reactive_lagging_kvarh REAL,
                    reactive_leading_kvarh REAL,
                    co2_tco2 REAL,
                    power_factor_lagging REAL,
                    power_factor_leading REAL,
                    nsm INTEGER,
                    week_status TEXT,
                    day_of_week TEXT,
                    load_type TEXT,
                    ambient_temperature_c REAL,
                    scope1_co2_kg REAL,
                    scope2_co2_kg REAL,
                    scope3_co2_kg REAL
                );
            """)
            
            # Create Index on date
            conn.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_date ON telemetry (date);")
            
            # Create Table for Alert persistence and lifecycle transitions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    first_seen_timestamp TEXT,
                    last_seen_timestamp TEXT,
                    type TEXT,
                    severity TEXT,
                    equipment TEXT,
                    value TEXT,
                    threshold TEXT,
                    status TEXT,
                    duplicate_count INTEGER DEFAULT 1,
                    mitigation TEXT,
                    resolution_notes TEXT,
                    resolved_by TEXT,
                    resolved_at TEXT,
                    raw_json TEXT
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts (status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts (timestamp);")

            # Create Table for Decision Center Audit History
            conn.execute("""
                CREATE TABLE IF NOT EXISTS decision_history (
                    action_id TEXT PRIMARY KEY,
                    title TEXT,
                    status TEXT,
                    created_at TEXT,
                    approved_at TEXT,
                    approved_by TEXT,
                    rejected_at TEXT,
                    rejected_by TEXT,
                    notes TEXT,
                    rejection_reason TEXT,
                    sector TEXT,
                    issue_summary TEXT,
                    raw_json TEXT
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_decision_status ON decision_history (status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_decision_created ON decision_history (created_at);")

            # Create Table for Model and Operational Monitoring Metrics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS operational_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    metric_type TEXT,
                    metric_name TEXT,
                    metric_value REAL,
                    metadata_json TEXT
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_type_ts ON operational_metrics (metric_type, timestamp);")
            conn.commit()
            
            # Schema migration for existing databases: add Scope 1/2/3 columns if missing
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(telemetry)")
            columns = [row['name'] for row in cursor.fetchall()]
            for scope_col in ["scope1_co2_kg", "scope2_co2_kg", "scope3_co2_kg"]:
                if scope_col not in columns:
                    logger.info(f"Migrating database: Adding column {scope_col} to telemetry table.")
                    conn.execute(f"ALTER TABLE telemetry ADD COLUMN {scope_col} REAL DEFAULT 0.0;")
            conn.commit()
            
            # Check if empty
            cursor.execute("SELECT COUNT(*) FROM telemetry;")
            count = cursor.fetchone()[0]
            
            if count < 500:
                logger.info(f"Telemetry database contains only {count} records. Bootstrapping full historical dataset...")
                try:
                    conn.execute("DELETE FROM telemetry;")
                    conn.commit()
                    df = load_dataset()
                    # Convert pandas datetime dates to ISO TEXT strings for SQLite
                    df_to_save = df.copy()
                    df_to_save['date'] = df_to_save['date'].dt.strftime("%Y-%m-%d %H:%M:%S")
                    
                    records = df_to_save.to_dict(orient="records")
                    self.insert_telemetry_records(records, sync=True)
                    logger.info(f"Telemetry database successfully bootstrapped with {len(records)} historical logs!")
                except Exception as e:
                    logger.error(f"Failed to bootstrap telemetry database: {e}")
                    raise
            else:
                logger.info(f"Telemetry database contains {count} active records. Skipping bootstrap.")

    def insert_telemetry_records(self, records: list, sync=False):
        """
        Inserts a list of telemetry readings.
        Pushes to queue for async ingestion under normal operation.
        If sync=True, flushes directly in a single transaction (used for initialization/bootstrapping).
        """
        if sync:
            self._flush_batch_to_db(records)
            return len(records)
        else:
            for r in records:
                self.ingest_queue.put(r)
            return len(records)

    def query_all_telemetry(self) -> pd.DataFrame:
        """
        Returns a DataFrame representing the entire telemetry logs.
        """
        with self.get_connection() as conn:
            df = pd.read_sql_query("SELECT * FROM telemetry ORDER BY date ASC", conn)
            df['date'] = pd.to_datetime(df['date'])
            return df

    def query_recent_telemetry(self, days: int) -> pd.DataFrame:
        """
        Returns a DataFrame representing the last N days of telemetry logs.
        """
        limit = days * 96
        with self.get_connection() as conn:
            query = f"""
                SELECT * FROM (
                    SELECT * FROM telemetry ORDER BY date DESC LIMIT {limit}
                ) ORDER BY date ASC
            """
            df = pd.read_sql_query(query, conn)
            df['date'] = pd.to_datetime(df['date'])
            return df

    def clear_all_telemetry(self):
        """
        Clears all telemetry records from the database table.
        """
        logger.info("Purging all records from the telemetry database.")
        def clear_action():
            with self.get_connection() as conn:
                conn.execute("DELETE FROM telemetry;")
                conn.commit()
                
        self.execute_with_retry(clear_action)

    # -------------------------------------------------------------
    # Decision Center Persistence & Recovery Methods
    # -------------------------------------------------------------
    def upsert_decision(self, decision: dict):
        """
        Idempotently inserts or updates a Decision Center action item.
        """
        def action():
            with self.get_connection() as conn:
                raw_json = json.dumps(decision)
                conn.execute("""
                    INSERT INTO decision_history (
                        action_id, title, status, created_at, approved_at, approved_by,
                        rejected_at, rejected_by, notes, rejection_reason, sector, issue_summary, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(action_id) DO UPDATE SET
                        title=excluded.title,
                        status=excluded.status,
                        approved_at=excluded.approved_at,
                        approved_by=excluded.approved_by,
                        rejected_at=excluded.rejected_at,
                        rejected_by=excluded.rejected_by,
                        notes=excluded.notes,
                        rejection_reason=excluded.rejection_reason,
                        sector=excluded.sector,
                        issue_summary=excluded.issue_summary,
                        raw_json=excluded.raw_json;
                """, (
                    decision.get("action_id"),
                    decision.get("title"),
                    decision.get("status"),
                    decision.get("created_at"),
                    decision.get("approved_at"),
                    decision.get("approved_by"),
                    decision.get("rejected_at"),
                    decision.get("rejected_by"),
                    decision.get("notes"),
                    decision.get("rejection_reason"),
                    decision.get("sector"),
                    decision.get("issue_summary"),
                    raw_json
                ))
                conn.commit()
        return self.execute_with_retry(action)

    def get_all_decisions(self) -> list:
        """
        Retrieves all historical decision items ordered chronologically.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decision_history ORDER BY created_at ASC;")
            rows = cursor.fetchall()
            decisions = []
            for r in rows:
                if r["raw_json"]:
                    try:
                        d = json.loads(r["raw_json"])
                        decisions.append(d)
                        continue
                    except Exception:
                        pass
                decisions.append(dict(r))
            return decisions

    def get_decision(self, action_id: str) -> dict:
        """
        Retrieves a single decision item by action_id.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decision_history WHERE action_id = ? LIMIT 1;", (action_id,))
            row = cursor.fetchone()
            if not row:
                return None
            if row["raw_json"]:
                try:
                    return json.loads(row["raw_json"])
                except Exception:
                    pass
            return dict(row)

    # -------------------------------------------------------------
    # Alerts Persistence & Lifecycle Methods
    # -------------------------------------------------------------
    def upsert_alert(self, alert: dict):
        """
        Idempotently inserts or updates an alert with full lifecycle status and transitions.
        """
        def action():
            with self.get_connection() as conn:
                raw_json = json.dumps(alert)
                conn.execute("""
                    INSERT INTO alerts (
                        alert_id, timestamp, first_seen_timestamp, last_seen_timestamp,
                        type, severity, equipment, value, threshold, status,
                        duplicate_count, mitigation, resolution_notes, resolved_by, resolved_at, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(alert_id) DO UPDATE SET
                        timestamp=excluded.timestamp,
                        last_seen_timestamp=excluded.last_seen_timestamp,
                        status=excluded.status,
                        duplicate_count=excluded.duplicate_count,
                        mitigation=excluded.mitigation,
                        resolution_notes=excluded.resolution_notes,
                        resolved_by=excluded.resolved_by,
                        resolved_at=excluded.resolved_at,
                        raw_json=excluded.raw_json;
                """, (
                    alert.get("alert_id"),
                    alert.get("timestamp"),
                    alert.get("first_seen_timestamp", alert.get("timestamp")),
                    alert.get("last_seen_timestamp", alert.get("timestamp")),
                    alert.get("type"),
                    alert.get("severity"),
                    alert.get("equipment"),
                    str(alert.get("value")),
                    str(alert.get("threshold")),
                    alert.get("status"),
                    int(alert.get("duplicate_count", 1)),
                    alert.get("mitigation"),
                    alert.get("resolution_notes"),
                    alert.get("resolved_by"),
                    alert.get("resolved_at"),
                    raw_json
                ))
                conn.commit()
        return self.execute_with_retry(action)

    def get_all_alerts(self, status: str = None) -> list:
        """
        Retrieves alerts ordered by timestamp descending, optionally filtered by status.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM alerts WHERE status = ? ORDER BY timestamp DESC;", (status,))
            else:
                cursor.execute("SELECT * FROM alerts ORDER BY timestamp DESC;")
            rows = cursor.fetchall()
            alerts = []
            for r in rows:
                if r["raw_json"]:
                    try:
                        a = json.loads(r["raw_json"])
                        alerts.append(a)
                        continue
                    except Exception:
                        pass
                alerts.append(dict(r))
            return alerts

    # -------------------------------------------------------------
    # Operational & Model Monitoring Metrics Persistence
    # -------------------------------------------------------------
    def record_operational_metric(self, metric_type: str, metric_name: str, metric_value: float, metadata: dict = None):
        """
        Records an operational monitoring point (e.g. forecast error, solver duration, telemetry drift).
        """
        def action():
            with self.get_connection() as conn:
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                meta_json = json.dumps(metadata) if metadata else "{}"
                conn.execute("""
                    INSERT INTO operational_metrics (timestamp, metric_type, metric_name, metric_value, metadata_json)
                    VALUES (?, ?, ?, ?, ?);
                """, (ts, metric_type, metric_name, float(metric_value), meta_json))
                conn.commit()
        return self.execute_with_retry(action)

    def get_operational_metrics(self, metric_type: str = None, limit: int = 50) -> list:
        """
        Retrieves recent operational monitoring metrics.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if metric_type:
                cursor.execute("""
                    SELECT * FROM operational_metrics WHERE metric_type = ? ORDER BY timestamp DESC LIMIT ?;
                """, (metric_type, limit))
            else:
                cursor.execute("""
                    SELECT * FROM operational_metrics ORDER BY timestamp DESC LIMIT ?;
                """, (limit,))
            rows = cursor.fetchall()
            metrics = []
            for r in rows:
                m = dict(r)
                if m.get("metadata_json"):
                    try:
                        m["metadata"] = json.loads(m["metadata_json"])
                    except Exception:
                        pass
                metrics.append(m)
            return metrics

    def close(self):
        """
        Safely stops the background batch writer thread.
        """
        self.stop_worker.set()
        if self.worker_thread:
            self.worker_thread.join(timeout=2.0)
            logger.info("Telemetry DB batch write worker thread stopped.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = TelemetryDB()
    db.init_db()
    
    # Test query
    df = db.query_recent_telemetry(3)
    print("Recent Telemetry Query Head:")
    print(df.head())
    db.close()
