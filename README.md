# 🤖 ICT + Supply & Demand Trading Bot

This project is a multi-market, automated trading signal bot that combines **ICT (Inner Circle Trader)** concepts (liquidity sweeps, fair value gaps, market structure shifts) with **Supply & Demand (S&D)** mechanics (order blocks, displacement, engulfing confirmations). 

It continuously monitors Forex, Indices, Commodities, and Crypto markets, scoring setups based on confluence layers, and sending rich HTML alerts via Telegram when high-quality setups form.

---

## 📂 Project Architecture & File Directory

Here is a breakdown of every folder and file in the codebase, detailing exactly what they do:

### 1. Root Files
* **[main.py](file:///c:/Users/Administrator/Documents/tradebot/app/main.py)**: FastAPI entrypoint. Manages the lifecycle (lifespan) of the application, starts the background scheduler on startup, stops it on shutdown, and exposes monitoring HTTP endpoints.
* **[test_integration.py](file:///c:/Users/Administrator/Documents/tradebot/test_integration.py)**: End-to-end testing script that bypasses the scheduler to fetch live market data for all asset types and runs the rule engine. Used to verify pipeline integrity.
* **`pyproject.toml` / `uv.lock`**: Configuration files for dependency management using `uv`.
* **`.env`**: Contains configuration environment variables (Telegram credentials, bot tokens, etc.).

### 2. `app/core` (System Core)
* **[config.py](file:///c:/Users/Administrator/Documents/tradebot/app/config.py)**: Configuration loader. Initializes environment variables and defines the asset catalog (`SYMBOLS`), timeframes, and session constraints.
* **[logger.py](file:///c:/Users/Administrator/Documents/tradebot/app/core/logger.py)**: Implements rotating file logging and console output to track scanner events and debug pipeline operations.
* **[utils.py](file:///c:/Users/Administrator/Documents/tradebot/app/core/utils.py)**: Common helper functions. Computes ATR (Average True Range), risk-reward ratio, recent highs/lows, candle bodies, and displacement status.

### 3. `app/data` (Market Data Feeds)
* **[feed_router.py](file:///c:/Users/Administrator/Documents/tradebot/app/data/feed_router.py)**: The central data routing layer. Maps symbols to their respective asset classes and feeds.
* **[crypto_feed.py](file:///c:/Users/Administrator/Documents/tradebot/app/data/crypto_feed.py)**: Fetches cryptocurrency candles. Uses Binance API natively, with an automatic fallback to `yfinance` (`BTC-USD`, `ETH-USD`) if credentials are not found.
* **[forex_feed.py](file:///c:/Users/Administrator/Documents/tradebot/app/data/forex_feed.py)**: Downloads Forex data from `yfinance`. Automatically normalizes MultiIndex headers and handles unnamed datetime indices.
* **[commodities_feed.py](file:///c:/Users/Administrator/Documents/tradebot/app/data/commodities_feed.py)**: Downloads Commodity Futures data (e.g., Gold `GC=F`, Silver `SI=F`) from `yfinance` using the normalization engine.
* **[indices_feed.py](file:///c:/Users/Administrator/Documents/tradebot/app/data/indices_feed.py)**: Downloads Index Futures data (e.g., NASDAQ `^NDX`, S&P 500 `^GSPC`) from `yfinance`.

### 4. `app/engine` (The Decision Engine)
* **[rule_engine.py](file:///c:/Users/Administrator/Documents/tradebot/app/engine/rule_engine.py)**: The brain of the bot. It evaluates candidates against the 8-layer checklist: validates structure, calculates SL/TP targets, runs scoring checks, and determines trade entry.
* **[scoring_engine.py](file:///c:/Users/Administrator/Documents/tradebot/app/engine/scoring_engine.py)**: Aggregates points for confluences (Engulfing=20, Displacement=25, FVG=20, Order Block=20, Volatility=15). The setup must achieve `MIN_SCORE = 40` to get executed.
* **[liquidity_engine.py](file:///c:/Users/Administrator/Documents/tradebot/app/engine/liquidity_engine.py)**: Identifies liquidity sweeps. Checks if the current candle's low/high pierced outside the lookback boundaries and closed back inside.
* **[market_structure.py](file:///c:/Users/Administrator/Documents/tradebot/app/engine/market_structure.py)**: Identifies Market Structure Shifts (MSS) by validating if the close breaks key swing structures.
* **[fvg_engine.py](file:///c:/Users/Administrator/Documents/tradebot/app/engine/fvg_engine.py)**: Identifies and monitors Fair Value Gaps (imbalances between candle $i-2$ and candle $i$).
* **[order_block_engine.py](file:///c:/Users/Administrator/Documents/tradebot/app/engine/order_block_engine.py)**: Identifies Order Blocks by mapping the candle immediately preceding a displacement drive.
* **[displacement_engine.py](file:///c:/Users/Administrator/Documents/tradebot/app/engine/displacement_engine.py)**: Confirms momentum expansion by checking if the candle body exceeds the average ATR-based body size.
* **[engulfing_engine.py](file:///c:/Users/Administrator/Documents/tradebot/app/engine/engulfing_engine.py)**: Analyzes open/close price relations of the last two candles to flag engulfing patterns.
* **[session_guard.py](file:///c:/Users/Administrator/Documents/tradebot/app/engine/session_guard.py)**: Restricts trading to specific hours (London, New York, or Crypto morning) to ensure trades occur only during high-volume periods.
* **[spread_guard.py](file:///c:/Users/Administrator/Documents/tradebot/app/engine/spread_guard.py)**: Checks spread limits to prevent entering trades during low-liquidity rollover hours.
* **[volatility_guard.py](file:///c:/Users/Administrator/Documents/tradebot/app/engine/volatility_guard.py)**: Validates that market activity meets minimum ATR limits.
* **[trade_gate.py](file:///c:/Users/Administrator/Documents/tradebot/app/engine/trade_gate.py)**: Checks account state to enforce risk bounds.

### 5. `app/risk` & `app/state` (Risk & Memory)
* **[risk_manager.py](file:///c:/Users/Administrator/Documents/tradebot/app/risk/risk_manager.py)**: Formulates dynamic position sizes matching a maximum 1% risk per trade.
* **[state_manager.py](file:///c:/Users/Administrator/Documents/tradebot/app/state/state_manager.py)**: In-memory tracker managing daily trade count limits (max 3/day) and preventing overlapping positions on the same pair.

### 6. `app/telegram` (Alert Routing)
* **[formatter.py](file:///c:/Users/Administrator/Documents/tradebot/app/telegram/formatter.py)**: Formats signals, startup statuses, and error messages into rich, beautiful HTML strings with emoji signals.
* **[notifier.py](file:///c:/Users/Administrator/Documents/tradebot/app/telegram/notifier.py)**: Handles connection timeouts and sends payloads to the Telegram bot API.

---

## ⚙️ How to Configure and Run

### 1. Configure Credentials
Create a `.env` file in the root folder:
```env
TELEGRAM_TOKEN=your_bot_token_here
CHAT_ID=your_chat_id_here
```

### 2. Run Integration Tests
Verify that all data feeds are normalizing correctly and the rules engine is executing:
```bash
uv run python test_integration.py
```

### 3. Spin up the Bot Web Server
Start the background scanner and monitoring dashboard:
```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- Query health details at: `http://127.0.0.1:8000/health`
- Check active risk limits at: `http://127.0.0.1:8000/status`

---

## 🧠 Profitability Critique: Will this logic make you profitable?

Here is an honest, personal, and professional assessment of the bot's current strategy rules and logic:

### 🌟 Strengths (What the bot does right)
1. **Mathematical Risk Edge**: The bot enforces a **1:3 Risk-to-Reward ratio** by default. With a 1:3 RR, you only need a **26% win rate** to break even. This is the foundation of professional trading.
2. **Confluence Filter**: Instead of entering raw indicator breakouts, the bot requires multiple independent factors (e.g., a sweep, structure shift, plus engulfing or displacement). Higher scores (`>= 60` or `>= 80`) yield high-quality setups.
3. **Session Filtering**: Limiting trades to London and New York sessions is critical. Entering trades during low-volume Asian sessions or spreads-widening rollovers is a major source of retail losses; the session and spread guards eliminate this.
4. **Hard Risk Gates**: The maximum 3 trades/day cap and the 1% risk-per-trade model act as circuit breakers, preventing revenge trading.

### ⚠️ Critical Limitations (Why it might lose money out-of-the-box)

1. **Coincident Indicators Check (The Single Candle Trap)**:
   In [rule_engine.py](file:///c:/Users/Administrator/Documents/tradebot/app/engine/rule_engine.py), the bot checks `bullish_sweep(df) and bullish_mss(df)` on the **exact same candle** (`df.iloc[-1]`). 
   - A liquidity sweep means price sweeps *below* a low and closes *above* it. 
   - A structure shift (MSS) means the close breaks *above* the recent high.
   - For both to happen on the same candle, the current candle must swing from below the 10-candle low all the way to above the 5-candle high. This only happens during high-impact news releases (e.g., NFP, FOMC), where slippage is severe and spreads widen, making entry highly risky.
   - *Fix needed*: The bot should check for a sweep on candle $i-N$ and look for a market structure shift to occur on a *subsequent* candle.

2. **Lack of Higher Timeframe (HTF) Trend Filter**:
   The bot scans a single timeframe (e.g. 5m). Trading a 5m bullish sweep against a 1-hour or 4-hour bearish trend is extremely low-probability. "Trading with the trend" is missing from this equation.
   - *Fix needed*: Implement a multi-timeframe check. The bot should only buy on the 5m chart if the 1-hour EMA-50 or market structure is bullish.

3. **In-Memory Mitigation State**:
   The `active_fvgs` list is stored in memory. If the server restarts, all pending FVGs are lost. Additionally, the FVG mitigation logic checks if the current close touches the FVG zone, but doesn't persist this state to database logs.

### 📈 Verdict
**Not profitable out-of-the-box, but a top-tier framework.** 

If run immediately on live markets, the bot will take very few trades (due to the strict coincident sweep + MSS constraint) and the ones it does take will likely be during high-slippage news events.

However, if you modify the code to check for **sequential states** (e.g., *Sweep occurs -> wait 1-10 candles -> MSS occurs -> entry at FVG retest*) and add a **Higher Timeframe Trend Filter** (e.g. only trade in the direction of the 1H trend), this bot will become a formidable, systematic execution system capable of generating consistent profits.
