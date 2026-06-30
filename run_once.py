"""
Single-run entrypoint for Render Cron Job.

Unlike main.py (which starts a FastAPI app + persistent background
scheduler), this script does ONE pass: fetch data for every symbol,
run the rule engine, send a Telegram alert for any signal found,
then exit cleanly. This is the correct shape for a cron job — Render
expects the command to finish, not run forever.

Set this as the "Command" in the Render Cron Job dashboard, e.g.:
    python run_once.py
or, if using uv:
    uv run python run_once.py
"""

import sys

from app.data.feed_router import get_market_data, get_htf_data
from app.engine.rule_engine import RuleEngine
from app.state.trade_manager import TradeManager
from app.telegram.notifier import send_message
from app.config import SYMBOLS
from app.core.logger import logger


def check_symbol(sym, tm):
    """Fetch data, run the rule engine, and alert on a signal for one symbol."""
    logger.info(f"Checking {sym}...")

    df_ltf = get_market_data(sym)
    df_htf = get_htf_data(sym)

    if df_ltf is None or df_ltf.empty or df_htf is None or df_htf.empty:
        logger.info(f"{sym}: no data (market may be closed)")
        return None

    engine = RuleEngine(pair=sym, trade_manager=tm)
    sessions = SYMBOLS[sym].get("sessions", [])

    signal, layers = engine.evaluate(
        df_ltf, df_htf, sessions, signal_mode="intraday"
    )

    if signal:
        logger.info(
            f"{sym}: SIGNAL {signal.direction} "
            f"Grade={signal.quality_score}/5 RR=1:{signal.risk_reward}"
        )
        message = (
            f"<b>Signal: {sym}</b>\n"
            f"Direction: {signal.direction}\n"
            f"Grade: {signal.quality_score}/5\n"
            f"RR: 1:{signal.risk_reward}"
        )
        send_message(message)
        return signal
    else:
        failed = layers.failed_layers()
        reason = failed[0] if failed else "setup not present"
        logger.info(f"{sym}: no signal ({reason})")
        return None


def main():
    tm = TradeManager()
    signals_found = 0
    errors = 0

    for symbol in SYMBOLS.keys():
        try:
            result = check_symbol(symbol, tm)
            if result:
                signals_found += 1
        except Exception as e:
            errors += 1
            logger.error(f"{symbol}: unhandled error — {e}")

    logger.info(
        f"Run complete. {signals_found} signal(s), {errors} error(s)."
    )

    # Non-zero exit on hard errors so Render's cron history flags the run
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
