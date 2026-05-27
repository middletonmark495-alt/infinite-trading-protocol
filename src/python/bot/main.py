"""
Infinite Trading Protocol — Multi-Source Trading Bot
=====================================================
Scans Coinbase (crypto), DexScreener (meme coins / DeFi), and Alpaca (stocks/futures).
Pulls social sentiment from Twitter/X and Telegram when API keys are configured.
Runs in paper-trading mode by default — set PAPER_TRADING=false in .env to go live.

Usage:
    python main.py

Required: pip install requests python-dotenv
Optional: pip install tabulate  (prettier tables)
"""
import logging
import sys
import time
import os
from datetime import datetime, timezone

# ── Bootstrap path so sibling imports work ───────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

import config as cfg
import data_feeds as feeds
import strategies as strat
import alerts
from paper_trader import PaperTrader

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("trading_bot.log"),
    ],
)
log = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
STATS_EVERY_N_SCANS = 10   # print summary every N full scans
_scan_count = 0


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


# ── Coinbase crypto scan ──────────────────────────────────────────────────────

def scan_coinbase(trader: PaperTrader):
    log.info("── Coinbase scan (%d pairs) ──", len(cfg.COINBASE_PAIRS))
    for pair in cfg.COINBASE_PAIRS:
        candles = feeds.get_coinbase_candles(pair, cfg.TIMEFRAME, cfg.NUM_CANDLES)
        if not candles:
            log.debug("No candles for %s", pair)
            continue

        price = candles[0]["close"]

        # Check exits first
        closed = trader.check_exits(pair, price)
        for c in closed:
            alerts.trade_closed(c.symbol, c.exit_price, c.pnl, c.pnl_pct, "stop_loss/take_profit")

        # Generate signal
        sig = strat.momentum_signal(candles, cfg.RSI_PERIOD, cfg.EMA_FAST, cfg.EMA_SLOW)
        log.info(
            "%s  $%-12.4f  RSI=%-5.1f  signal=%-4s  conf=%.2f  %s",
            pair.ljust(12),
            price,
            sig["indicators"].get("rsi", 0),
            sig["signal"],
            sig["confidence"],
            sig["reason"],
        )

        if sig["signal"] == "BUY" and sig["confidence"] >= 0.4:
            pos = trader.open_long(pair, price, source="coinbase")
            if pos:
                alerts.trade_opened(pair, "long", price, pos.quantity, pos.stop_loss, pos.take_profit, sig["reason"])

        time.sleep(0.3)


# ── DexScreener meme-coin scan ────────────────────────────────────────────────

def scan_meme_coins(trader: PaperTrader):
    log.info("── DexScreener meme scan ──")
    tokens = feeds.scan_trending_tokens()
    if not tokens:
        log.info("  No trending tokens found (may be rate-limited)")
        return

    log.info("  Found %d trending tokens with sufficient liquidity", len(tokens))
    for token in tokens[:20]:   # top 20 by 1h momentum
        symbol = token["symbol"]

        # Social sentiment boost (Twitter)
        tweets = feeds.get_twitter_mentions(f"${symbol} OR #{symbol}", max_results=20)
        sentiment = feeds.score_sentiment(tweets)

        sig = strat.meme_coin_signal(token, social_sentiment=sentiment)

        log.info(
            "%-10s  %-10s  $%-14.8f  1h=%+6.1f%%  liq=$%8.0f  social=%+.2f  signal=%-5s  conf=%.2f  %s",
            symbol[:10],
            token["chain"][:10],
            token["price_usd"],
            token["price_chg_1h"],
            token["liquidity_usd"],
            sentiment,
            sig["signal"],
            sig["confidence"],
            sig["reason"],
        )

        if sig["signal"] == "BUY" and sig["confidence"] >= 0.45:
            alerts.meme_alert(
                symbol,
                token["chain"],
                token["price_usd"],
                token["price_chg_1h"],
                token["liquidity_usd"],
                token["url"],
                sig["reason"],
            )
            # Note: meme tokens need DEX integration for execution (web3.py + wallet)
            # Paper trade against DexScreener price
            label = f"{symbol}[{token['chain'][:4]}]"
            pos = trader.open_long(label, token["price_usd"], source="dexscreener")
            if pos:
                alerts.trade_opened(label, "long", token["price_usd"], pos.quantity, pos.stop_loss, pos.take_profit, sig["reason"])


# ── Alpaca stocks/futures scan ────────────────────────────────────────────────

def scan_stocks(trader: PaperTrader):
    if not cfg.ALPACA_API_KEY:
        log.debug("Alpaca not configured — skipping stocks/futures")
        return
    log.info("── Alpaca stocks scan (%d symbols) ──", len(cfg.STOCK_SYMBOLS))
    for symbol in cfg.STOCK_SYMBOLS:
        bars = feeds.get_alpaca_bars(symbol, timeframe="1Hour", limit=100)
        if not bars:
            continue
        candles = [{"close": b["close"], "high": b["high"], "low": b["low"],
                    "open": b["open"], "volume": b["volume"]} for b in bars]
        price = candles[-1]["close"]

        closed = trader.check_exits(f"${symbol}", price)
        for c in closed:
            alerts.trade_closed(c.symbol, c.exit_price, c.pnl, c.pnl_pct, "stop_loss/take_profit")

        sig = strat.momentum_signal(candles[::-1], cfg.RSI_PERIOD, cfg.EMA_FAST, cfg.EMA_SLOW)
        log.info(
            "$%-8s  $%-10.2f  RSI=%-5.1f  signal=%-4s  conf=%.2f  %s",
            symbol,
            price,
            sig["indicators"].get("rsi", 0),
            sig["signal"],
            sig["confidence"],
            sig["reason"],
        )

        if sig["signal"] == "BUY" and sig["confidence"] >= 0.4:
            pos = trader.open_long(f"${symbol}", price, source="alpaca")
            if pos:
                alerts.trade_opened(f"${symbol}", "long", price, pos.quantity, pos.stop_loss, pos.take_profit, sig["reason"])

        time.sleep(0.2)


# ── Twitter scanning for market catalysts ────────────────────────────────────

def scan_twitter_catalysts():
    if not cfg.TWITTER_BEARER_TOKEN:
        return
    log.info("── Twitter catalyst scan ──")
    queries = ["crypto moon", "new listing coinbase", "pump coin", "100x gem"]
    for q in queries:
        tweets = feeds.get_twitter_mentions(q, max_results=15)
        sentiment = feeds.score_sentiment(tweets)
        if sentiment > 0.4:
            log.info("  HIGH BULLISH sentiment for '%s': %.2f (%d tweets)", q, sentiment, len(tweets))


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    global _scan_count

    log.info("=" * 60)
    log.info("  Infinite Trading Protocol Bot — starting %s", _ts())
    log.info("  Mode: %s", "PAPER TRADING" if cfg.PAPER_TRADING else "⚠️  LIVE TRADING")
    log.info("  Capital: $%.2f", cfg.STARTING_CAPITAL)
    log.info("  Scan interval: %ds", cfg.SCAN_INTERVAL_SECONDS)
    log.info("  Coinbase pairs: %d", len(cfg.COINBASE_PAIRS))
    log.info("  Twitter:  %s", "✓ configured" if cfg.TWITTER_BEARER_TOKEN else "✗ not configured")
    log.info("  Telegram: %s", "✓ configured" if cfg.TELEGRAM_BOT_TOKEN else "✗ not configured")
    log.info("  Discord:  %s", "✓ configured" if cfg.DISCORD_WEBHOOK_URL else "✗ not configured")
    log.info("  Alpaca:   %s", "✓ configured" if cfg.ALPACA_API_KEY else "✗ not configured")
    log.info("=" * 60)

    trader = PaperTrader(cfg.STARTING_CAPITAL)
    alerts.send(f"🤖 ITP Trading Bot started — paper={cfg.PAPER_TRADING} — capital=${cfg.STARTING_CAPITAL:,.0f}")

    while True:
        try:
            log.info("\n╔══ SCAN #%d  %s ══", _scan_count + 1, _ts())

            scan_coinbase(trader)
            scan_meme_coins(trader)
            scan_stocks(trader)
            scan_twitter_catalysts()

            _scan_count += 1
            if _scan_count % STATS_EVERY_N_SCANS == 0:
                trader.print_stats()
                alerts.stats_report(trader.stats())

            log.info("╚══ scan complete — next in %ds\n", cfg.SCAN_INTERVAL_SECONDS)
            time.sleep(cfg.SCAN_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            log.info("\nShutting down — final stats:")
            trader.print_stats()
            alerts.stats_report(trader.stats())
            alerts.send("🛑 ITP Trading Bot stopped.")
            sys.exit(0)
        except Exception as e:
            log.exception("Unhandled error in main loop: %s", e)
            time.sleep(10)


if __name__ == "__main__":
    main()
