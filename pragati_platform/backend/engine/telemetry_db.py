import os
import sys
import sqlite3
import logging
import contextlib
import pandas as pd

# Ensure backend folder is in path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dataset_loader import load_dataset

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

    def init_db(self):
        """
        Creates the table schema, adds indices, and bootstraps historical CSV data if empty.
        """
        logger.info(f"Initializing telemetry database at: {self.db_path}")
        with self.get_connection() as conn:
            # Create Table
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
                    ambient_temperature_c REAL
                );
            """)
            
            # Create Index on date
            conn.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_date ON telemetry (date);")
            conn.commit()
            
            # Check if empty
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM telemetry;")
            count = cursor.fetchone()[0]
            
            if count == 0:
                logger.info("Telemetry database is empty. Bootstrapping historical CSV data...")
                try:
                    df = load_dataset()
                    # Convert pandas datetime dates to ISO TEXT strings for SQLite
                    df_to_save = df.copy()
                    df_to_save['date'] = df_to_save['date'].dt.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Bulk insert using pandas to_sql in chunks
                    df_to_save.to_sql("telemetry", conn, if_exists="append", index=False, chunksize=5000)
                    logger.info("Telemetry database successfully bootstrapped with historical logs!")
                except Exception as e:
                    logger.error(f"Failed to bootstrap telemetry database: {e}")
                    raise
            else:
                logger.info(f"Telemetry database contains {count} active records. Skipping bootstrap.")

    def insert_telemetry_records(self, records: list):
        """
        Inserts a list of dictionaries (telemetry readings) into the database.
        Uses INSERT OR IGNORE to prevent duplicate timestamp conflicts.
        """
        query = """
            INSERT OR IGNORE INTO telemetry (
                date, usage_kwh, reactive_lagging_kvarh, reactive_leading_kvarh,
                co2_tco2, power_factor_lagging, power_factor_leading,
                nsm, week_status, day_of_week, load_type, ambient_temperature_c
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            );
        """
        
        # Prepare parameters tuple list
        param_list = []
        for r in records:
            param_list.append((
                r.get("date"),
                r.get("usage_kwh"),
                r.get("reactive_lagging_kvarh"),
                r.get("reactive_leading_kvarh"),
                r.get("co2_tco2"),
                r.get("power_factor_lagging"),
                r.get("power_factor_leading"),
                r.get("nsm"),
                r.get("week_status"),
                r.get("day_of_week"),
                r.get("load_type"),
                r.get("ambient_temperature_c")
            ))
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, param_list)
            conn.commit()
            return cursor.rowcount

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

if __name__ == "__main__":
    # Test DB
    logging.basicConfig(level=logging.INFO)
    db = TelemetryDB()
    db.init_db()
    
    # Test query
    df = db.query_recent_telemetry(3)
    print("Recent Telemetry Query Head:")
    print(df.head())
    print("Rows returned:", len(df))
