"""
Trading Bot — FastAPI Entrypoint

Starts the scheduler on startup and provides monitoring endpoints.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException
import os
import sqlite3

from app.scheduler import start_scheduler, scheduler, trade_manager
from app.core.logger import logger
from app.core.utils import timestamp
from app.config import SYMBOLS
from app.telegram.notifier import send_message
from app.telegram.formatter import format_startup

CRON_SECRET = os.environ.get("CRON_SECRET")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""

    # ── Startup ──
    logger.info("Trading bot starting up...")
    start_scheduler()

    # Send Telegram startup notification
    send_message(format_startup())

    logger.info("Trading bot is live")
    yield

    # ── Shutdown ──
    logger.info("Trading bot shutting down...")
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")


app = FastAPI(
    title="Trading Bot",
    description="Multi-market ICT + S&D signal engine",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def root():
    """Health check."""

    return {
        "status": "running",
        "timestamp": timestamp(),
    }


@app.get("/health")
def health():
    """Detailed health check."""

    return {
        "status": "healthy",
        "scheduler_running": scheduler.running,
        "symbols": list(SYMBOLS.keys()),
        "timestamp": timestamp(),
    }


@app.get("/status")
def status():
    """Current trading state."""
    
    # Query sqlite for current active trades and today's trade count
    active_trades = {}
    today_count = 0
    
    try:
        with sqlite3.connect(trade_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT pair, direction, entry_price FROM active_trades")
            for row in cursor.fetchall():
                active_trades[row["pair"]] = dict(row)
                
            cursor = conn.execute("SELECT trade_count FROM daily_stats WHERE trade_date = ?", (trade_manager._get_today_date(),))
            row = cursor.fetchone()
            if row:
                today_count = row["trade_count"]
    except Exception as e:
        logger.error(f"Error fetching status from db: {e}")

    return {
        "active_trades": active_trades,
        "trades_today": today_count,
        "current_day": trade_manager._get_today_date(),
        "timestamp": timestamp(),
    }


@app.get("/symbols")
def symbols():
    """List all monitored symbols and their config."""

    return {
        "count": len(SYMBOLS),
        "symbols": SYMBOLS,
    }


@app.get("/run-check")
def run_check(x_cron_secret: str = Header(None)):
    """Run a single pass of the engine (for external cron triggers)."""
    if CRON_SECRET and x_cron_secret != CRON_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    from run_once import main as run_main
    run_main()
    return {"status": "ok"}