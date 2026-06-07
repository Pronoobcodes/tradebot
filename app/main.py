"""
Trading Bot — FastAPI Entrypoint

Starts the scheduler on startup and provides monitoring endpoints.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.scheduler import start_scheduler, scheduler
from app.core.logger import logger
from app.core.utils import timestamp
from app.config import SYMBOLS
from app.engine.trade_gate import state
from app.telegram.notifier import send_message
from app.telegram.formatter import format_startup


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

    return {
        "active_trade": state.active_trade,
        "trades_today": state.trade_count,
        "can_trade": state.can_trade(),
        "current_day": str(state.current_day),
        "timestamp": timestamp(),
    }


@app.get("/symbols")
def symbols():
    """List all monitored symbols and their config."""

    return {
        "count": len(SYMBOLS),
        "symbols": SYMBOLS,
    }