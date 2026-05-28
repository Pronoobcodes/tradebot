from enum import Enum


class MarketType(str, Enum):
    CRYPTO = "crypto"
    FOREX = "forex"
    INDICES = "indices"
    STOCKS = "stocks"
    COMMODITIES = "commodities"
    

class TradeDirection(str, Enum):
    BUY = "buy"
    SELL = "sell"


class TradeStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    PENDING = "pending"
    CANCELLED = "cancelled"
    STOPPED = "stopped"


class TradingSession(str, Enum):
    LONDON = "london"
    NEW_YORK = "new_york"
    ASIAN = "asian"
    CRYPTO_MORNING = "crypto_morning"


class SignalStrength(str, Enum):
    WEAK = "weak"
    NEUTRAL = "neutral"
    STRONG = "strong"
    VERY_STRONG = "very_strong" 


class LiquidityType(str, Enum):
    SSL = "sell_side_liquidity"
    BSL = "buy_side_liquidity"


class MarketStructure(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"


class OrderBlockType(str, Enum):
    BEARISH_OB = "bearish_order_block"
    BULLISH_OB = "bullish_order_block"


class FVGType(str, Enum):
    BULLISH_FVG = "bullish_fvg"
    BEARISH_FVG = "bearish_fvg"


class TradeOutcome(str, Enum):
    WIN = "win"
    LOSS = "loss"
    BREAKEVEN = "breakeven"
    PARTIAL = "partial"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class EngineState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"