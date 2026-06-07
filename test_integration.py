"""Integration test: fetch live data and run signal engine."""

from app.data.feed_router import get_market_data
from app.engine.rule_engine import generate_signal


def test_symbol(sym):
    print(f"--- Testing {sym} ---")
    df = get_market_data(sym)

    if df is None or df.empty:
        print(f"  No data (market may be closed)")
        return

    print(f"  Columns: {df.columns.tolist()}")
    print(f"  Rows: {len(df)}")
    last_close = df["close"].iloc[-1]
    print(f"  Last close: {last_close}")

    signal = generate_signal(df, symbol=sym)
    if signal:
        print(f"  SIGNAL: {signal['direction']} Grade={signal['grade']} RR=1:{signal['rr']}")
    else:
        print(f"  No signal (normal — setup not present)")


if __name__ == "__main__":
    for symbol in ["EURGBP", "XAUUSD", "SP500", "BTCUSDT"]:
        test_symbol(symbol)

    print("--- All integration tests done ---")
