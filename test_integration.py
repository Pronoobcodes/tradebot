"""Integration test: fetch live data and run signal engine."""

from app.data.feed_router import get_market_data, get_htf_data
from app.engine.rule_engine import RuleEngine
from app.state.trade_manager import TradeManager
from app.config import SYMBOLS


def test_symbol(sym):
    print(f"--- Testing {sym} ---")
    df_ltf = get_market_data(sym)
    df_htf = get_htf_data(sym)

    if df_ltf is None or df_ltf.empty or df_htf is None or df_htf.empty:
        print(f"  No data (market may be closed)")
        return

    print(f"  LTF Rows: {len(df_ltf)}, HTF Rows: {len(df_htf)}")
    last_close = df_ltf["close"].iloc[-1]
    print(f"  Last LTF close: {last_close}")

    tm = TradeManager()
    engine = RuleEngine(pair=sym, trade_manager=tm)
    sessions = SYMBOLS[sym].get("sessions", [])

    signal, layers = engine.evaluate(df_ltf, df_htf, sessions, signal_mode="intraday")
    
    if signal:
        print(f"  SIGNAL: {signal.direction} Grade={signal.quality_score}/5 RR=1:{signal.risk_reward}")
    else:
        print(f"  No signal (normal — setup not present)")
        failed = layers.failed_layers()
        if failed:
            print(f"  Reason: {failed[0]}")


if __name__ == "__main__":
    for symbol in ["EURGBP", "XAUUSD", "SP500", "BTCUSDT"]:
        test_symbol(symbol)

    print("--- All integration tests done ---")
