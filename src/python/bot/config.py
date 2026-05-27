"""
Configuration loader — reads .env file and environment variables.
Copy .env.example to .env and fill in your keys before running.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Paper vs live ────────────────────────────────────────────────────────────
PAPER_TRADING = os.getenv("PAPER_TRADING", "true").lower() == "true"
STARTING_CAPITAL = float(os.getenv("STARTING_CAPITAL", "10000"))

# ── Pairs to trade (Coinbase format: BASE-QUOTE) ─────────────────────────────
COINBASE_PAIRS = os.getenv(
    "COINBASE_PAIRS",
    "BTC-USD,ETH-USD,SOL-USD,LINK-USD,ARB-USD,MATIC-USD,AAVE-USD,UNI-USD,DOGE-USD,PEPE-USD,SHIB-USD"
).split(",")

# ── DexScreener meme-coin scanning ──────────────────────────────────────────
DEXSCREENER_CHAINS = os.getenv("DEXSCREENER_CHAINS", "ethereum,solana,bsc,base,polygon,arbitrum").split(",")
MEME_MIN_LIQUIDITY_USD = float(os.getenv("MEME_MIN_LIQUIDITY_USD", "50000"))
MEME_MIN_VOLUME_24H = float(os.getenv("MEME_MIN_VOLUME_24H", "100000"))
MEME_MIN_PRICE_CHANGE_1H = float(os.getenv("MEME_MIN_PRICE_CHANGE_1H", "5.0"))   # %
MEME_MAX_AGE_HOURS = float(os.getenv("MEME_MAX_AGE_HOURS", "72"))

# ── Strategy ─────────────────────────────────────────────────────────────────
TIMEFRAME = os.getenv("TIMEFRAME", "1h")
NUM_CANDLES = int(os.getenv("NUM_CANDLES", "200"))
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
EMA_FAST = int(os.getenv("EMA_FAST", "9"))
EMA_SLOW = int(os.getenv("EMA_SLOW", "21"))
RISK_PER_TRADE_PCT = float(os.getenv("RISK_PER_TRADE_PCT", "2.0"))   # % of capital per trade
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "3.0"))             # % below entry
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "6.0"))         # % above entry
MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", "5"))
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "60"))

# ── Social feeds (all optional) ──────────────────────────────────────────────
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_IDS = os.getenv("TELEGRAM_CHANNEL_IDS", "").split(",")   # e.g. @channel

# ── Alerts (outbound) ────────────────────────────────────────────────────────
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
TELEGRAM_ALERT_CHAT_ID = os.getenv("TELEGRAM_ALERT_CHAT_ID", "")

# ── Alpaca (stocks + futures, paper or live) ─────────────────────────────────
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")  # switch to live-api for real trading
STOCK_SYMBOLS = os.getenv("STOCK_SYMBOLS", "NVDA,TSLA,AAPL,AMZN,META,SPY").split(",")
FUTURES_SYMBOLS = os.getenv("FUTURES_SYMBOLS", "ES,NQ,CL,GC").split(",")
