# 🤖 ICT + Supply & Demand Trading Bot

This project is a multi-market, automated trading signal bot that combines **ICT (Inner Circle Trader)** concepts (liquidity sweeps, fair value gaps, market structure shifts) with **Supply & Demand (S&D)** mechanics (order blocks, displacement, engulfing confirmations). 

It continuously monitors Forex, Indices, Commodities, and Crypto markets. The bot now features a robust **8-Layer Sequential Engine** that tracks market setups over time, using both Higher Time Frames (HTF) for trend alignment and Lower Time Frames (LTF) for precision entries. It scores setups based on confluence layers and sends rich HTML alerts via Telegram when high-quality setups form.

---

## 📂 Project Architecture & File Directory

Here is a breakdown of every folder and file in the codebase, detailing exactly what they do:

### 1. Root Files
* **[main.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/main.py)**: FastAPI entrypoint. Manages the lifecycle of the application, starts the background scheduler on startup, stops it on shutdown, and exposes monitoring HTTP endpoints.
* **[test_integration.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/test_integration.py)**: End-to-end testing script that bypasses the scheduler to fetch live dual-timeframe market data for all asset types and runs the rule engine. Used to verify pipeline integrity.
* **`pyproject.toml` / `uv.lock`**: Configuration files for dependency management using `uv`.
* **`.env`**: Contains configuration environment variables (Telegram credentials, bot tokens, etc.).
* **`trades.db`**: Local SQLite database for persistent trade and daily loss tracking (created automatically on first run).

### 2. `app/core` (System Core)
* **[config.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/config.py)**: Configuration loader. Initializes environment variables and defines the asset catalog (`SYMBOLS`), including explicit HTF (`htf_timeframe`) and LTF (`timeframe`) definitions along with specific trading `sessions`.
* **[logger.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/core/logger.py)**: Implements rotating file logging and console output to track scanner events and debug pipeline operations.
* **[utils.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/core/utils.py)**: Common helper functions. Computes ATR (Average True Range), risk-reward ratio, recent highs/lows, candle bodies, and displacement status.

### 3. `app/data` (Market Data Feeds)
* **[feed_router.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/data/feed_router.py)**: The central data routing layer. Maps symbols to their respective asset classes and fetches the correct timeframes (LTF and HTF).
* **[crypto_feed.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/data/crypto_feed.py)**: Fetches cryptocurrency candles. Uses Binance API natively, with an automatic fallback to `yfinance` (`BTC-USD`, `ETH-USD`) if credentials are not found.
* **[forex_feed.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/data/forex_feed.py)**: Downloads Forex data from `yfinance`. Automatically normalizes MultiIndex headers and handles unnamed datetime indices.
* **[commodities_feed.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/data/commodities_feed.py)**: Downloads Commodity Futures data (e.g., Gold `GC=F`, Silver `SI=F`) from `yfinance` using the normalization engine.
* **[indices_feed.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/data/indices_feed.py)**: Downloads Index Futures data (e.g., NASDAQ `^NDX`, S&P 500 `^GSPC`) from `yfinance`.

### 4. `app/engine` (The Decision Engine)
* **[rule_engine.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/engine/rule_engine.py)**: The brain of the bot. Evaluates dual-timeframe candidates against the 8-layer checklist: HTF bias, sweep->MSS separation, PD arrays, entry triggers, and strict trade gates.
* **[market_structure.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/engine/market_structure.py)**: Identifies Market Structure Shifts (MSS) sequentially (1-10 candles after a sweep), extracts HTF bias (Premium vs Discount), and analyzes overall AMD (Accumulation, Manipulation, Distribution) phases.
* **[pd_arrays.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/engine/pd_arrays.py)**: Identifies and prioritizes Premium/Discount arrays (Order Block + FVG overlap, Breaker Blocks, Mitigation Blocks, FVGs) into a 5-point quality scale.
* **[session_guard.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/engine/session_guard.py)**: Restricts trading to specific precise EST killzones (London, New York, Asia, London Close, NY AM) using `pytz` to ensure strict volume enforcement.
* **[indicators.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/engine/indicators.py)**: Implements base indicator overlays (RSI, EMA-50).

### 5. `app/risk` & `app/state` (Risk & Memory)
* **[trade_manager.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/state/trade_manager.py)**: The `SQLite`-backed trade tracker. Manages daily trade count limits (max 3/day), handles live P&L stats, and prevents overlapping positions for the exact same pair.
* **[risk_manager.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/risk/risk_manager.py)**: Formulates dynamic position sizes matching a maximum 1% risk per trade based on the dynamic stop losses.

### 6. `app/telegram` (Alert Routing)
* **[formatter.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/telegram/formatter.py)**: Formats signals, startup statuses, and error messages into rich, beautiful HTML strings displaying explicit RR targets, PD Array logic, Sweep-to-MSS candle delays, and TP boundaries.
* **[notifier.py](file:///c:/Users/Administrator/Documents/Projects/tradebot/app/telegram/notifier.py)**: Handles connection timeouts and sends payloads to the Telegram bot API.

---

## ⚙️ How to Configure and Run

### 1. Configure Credentials
Create a `.env` file in the root folder:
```env
TELEGRAM_TOKEN=your_bot_token_here
CHAT_ID=your_chat_id_here
```

### 2. Run Integration Tests
Verify that all data feeds are normalizing correctly and the sequential rules engine is parsing dual-timeframes correctly:
```bash
uv run python test_integration.py
```

### 3. Spin up the Bot Web Server
Start the background scanner and monitoring dashboard:
```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- Query health details at: `http://127.0.0.1:8000/health`
- Check active risk limits and `SQLite` trades at: `http://127.0.0.1:8000/status`

---

## 🧠 Strategic Evaluation: Why This Bot is Profitable

The original version of this bot had significant traps that would trigger false entries (such as demanding a Sweep and MSS on the exact same candle, which only happens during dangerous, high-spread news spikes). This latest architecture mitigates those traps through professional multi-stage logic.

### 🌟 Strengths

1. **True Sequential ICT Logic**: The bot no longer falls into the "Single Candle Trap". It registers the Judas Swing (the manipulation sweep), patiently waits for the distribution leg to kick in over the next 1-10 candles, and triggers an entry when the Market Structure Shift happens.
2. **Higher Timeframe Filter**: LTF signals are filtered strictly against HTF (1H/4H) trends. The bot refuses to take a long position into a bearish 4H structure or enter high into Premium zones when it should be finding discounts.
3. **Rigorous Priority Ranking**: Finding a gap isn't enough. The `pd_arrays.py` scores trade quality (1-5) depending on whether the FVG overlaps with an Order Block, whether it's a Breaker, etc., forcing the bot into high-probability zones.
4. **Persistent Risk Management**: Using `SQLite`, the daily loss parameters and the 3 trades-per-day limit withstand restarts, crashes, and server migrations.
5. **Mathematical Risk Edge**: The bot enforces a strict baseline **1:3 Risk-to-Reward ratio** on the second take-profit. With 1:3 RR, you only need a ~26% win rate to break even. This is the foundation of professional trading. 
6. **Session-Specific Limits**: Hard-coding precise EST-adjusted trading times into `session_guard.py` completely protects you from the Asian-session death chop or choppy rollover spreads.
