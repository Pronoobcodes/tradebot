import sqlite3
import json
from datetime import date, datetime
from typing import Optional, Dict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "trades.db"

class TradeManager:
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self.max_trades_per_day = 3
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS active_trades (
                    pair TEXT PRIMARY KEY,
                    direction TEXT,
                    entry_price REAL,
                    signal_mode TEXT,
                    timestamp TEXT,
                    data TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    trade_date TEXT PRIMARY KEY,
                    trade_count INTEGER DEFAULT 0,
                    pnl REAL DEFAULT 0.0
                )
            ''')
            conn.commit()

    def _get_today_date(self) -> str:
        return date.today().isoformat()

    def can_open_trade(self, pair: str, signal_mode: str = "intraday") -> bool:
        if self.get_active_trade(pair):
            return False

        today = self._get_today_date()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT trade_count FROM daily_stats WHERE trade_date = ?", (today,)
            )
            row = cursor.fetchone()
            count = row[0] if row else 0

        return count < self.max_trades_per_day

    def register_trade(self, pair: str, direction: str, entry: float, signal_mode: str = "intraday", data: dict = None):
        if data is None:
            data = {}
        today = self._get_today_date()
        timestamp = datetime.utcnow().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO active_trades 
                (pair, direction, entry_price, signal_mode, timestamp, data)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (pair, direction, entry, signal_mode, timestamp, json.dumps(data)))
            
            conn.execute('''
                INSERT INTO daily_stats (trade_date, trade_count) 
                VALUES (?, 1)
                ON CONFLICT(trade_date) DO UPDATE SET trade_count = trade_count + 1
            ''', (today,))
            conn.commit()

    def get_active_trade(self, pair: str) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM active_trades WHERE pair = ?", (pair,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d["data"] = json.loads(d["data"])
                return d
            return None

    def close_trade(self, pair: str, pnl: float = 0.0):
        today = self._get_today_date()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM active_trades WHERE pair = ?", (pair,))
            conn.execute('''
                UPDATE daily_stats SET pnl = pnl + ? WHERE trade_date = ?
            ''', (pnl, today))
            conn.commit()
