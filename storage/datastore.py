import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import threading
import logging

class DataStore:
    def __init__(self, db_path="market_data.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ticks (
                    symbol TEXT,
                    ts TEXT,
                    price REAL,
                    size REAL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbol_ts ON ticks(symbol, ts)")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    symbol TEXT,
                    alert_type TEXT,
                    message TEXT,
                    value REAL
                )
            """)
            
            conn.commit()
            conn.close()

    def store_tick(self, tick_data: dict):
        """
        Store a single tick.
        tick_data: {symbol, ts, price, size}
        """
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT INTO ticks (symbol, ts, price, size) VALUES (?, ?, ?, ?)",
                    (tick_data['symbol'], tick_data['ts'], tick_data['price'], tick_data['size'])
                )
                conn.commit()
            except Exception as e:
                logging.error(f"Error storing tick: {e}")
            finally:
                conn.close()

    def get_ticks(self, symbol: str, lookback_minutes: int = 60) -> pd.DataFrame:
        """
        Retrieve ticks for a symbol from the last N minutes.
        """
        start_time = (datetime.utcnow() - timedelta(minutes=lookback_minutes)).isoformat()
        
        query = "SELECT ts, price, size FROM ticks WHERE symbol = ? AND ts >= ? ORDER BY ts ASC"
        
        with self._lock:
            conn = self._get_conn()
            try:
                df = pd.read_sql_query(query, conn, params=(symbol, start_time))
                if not df.empty:
                    df['ts'] = pd.to_datetime(df['ts'], format='mixed')
                    df.set_index('ts', inplace=True)
                return df
            finally:
                conn.close()

    def log_alert(self, alert_data: dict):
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT INTO alerts (timestamp, symbol, alert_type, message, value) VALUES (?, ?, ?, ?, ?)",
                    (alert_data['timestamp'], alert_data['symbol'], 
                     alert_data['type'], alert_data['message'], alert_data['value'])
                )
                conn.commit()
            finally:
                conn.close()

    def get_latest_alerts(self, limit=50) -> pd.DataFrame:
        query = "SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?"
        with self._lock:
            conn = self._get_conn()
            try:
                df = pd.read_sql_query(query, conn, params=(limit,))
                return df
            finally:
                conn.close()

    def clear_db(self):
        """
        Clear all data from the database.
        """
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("DELETE FROM ticks")
                conn.execute("DELETE FROM alerts")
                conn.commit()
            except Exception as e:
                logging.error(f"Error clearing DB: {e}")
            finally:
                conn.close()
