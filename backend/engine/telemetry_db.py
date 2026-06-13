import os
import sys
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

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "pragati_telemetry.db")

class TelemetryDB:
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
        and ensures the connection is closed when exiting the context.
        """
        conn = sqlite3.connect(self.db_path)
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
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, param_list)
            conn.commit()

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
            
            if count == 0:
                logger.info("Telemetry database is empty. Bootstrapping historical CSV data...")
                try:
                    df = load_dataset()
                    # Convert pandas datetime dates to ISO TEXT strings for SQLite
                    df_to_save = df.copy()
                    df_to_save['date'] = df_to_save['date'].dt.strftime("%Y-%m-%d %H:%M:%S")
                    
                    records = df_to_save.to_dict(orient="records")
                    self.insert_telemetry_records(records, sync=True)
                    logger.info("Telemetry database successfully bootstrapped with historical logs!")
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
        with self.get_connection() as conn:
            conn.execute("DELETE FROM telemetry;")
            conn.commit()

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
