"""
Data feed aggregator — Coinbase, DexScreener, Twitter/X, Telegram, Alpaca.
Each feed gracefully degrades if the API key is missing.
"""
import time
import logging
import requests
from datetime import datetime, timezone
from typing import Optional

import config as cfg

log = logging.getLogger(__name__)

# ── Coinbase ─────────────────────────────────────────────────────────────────

_TF_TO_SECONDS = {
    "1m": 60, "5m": 300, "15m": 900,
    "1h": 3600, "6h": 21600, "1d": 86400,
}

def get_coinbase_candles(pair: str, timeframe: str = "1h", num_candles: int = 200) -> list:
    """Returns list of [time, low, high, open, close, volume] dicts (newest first)."""
    granularity = _TF_TO_SECONDS.get(timeframe)
    if not granularity:
        log.error("Unknown timeframe: %s", timeframe)
        return []
    url = f"https://api.exchange.coinbase.com/products/{pair}/candles"
    for attempt in range(3):
        try:
            r = requests.get(url, params={"granularity": granularity}, timeout=10)
            r.raise_for_status()
            raw = r.json()
            candles = [
                {"time": c[0], "low": c[1], "high": c[2],
                 "open": c[3], "close": c[4], "volume": c[5]}
                for c in raw[:num_candles]
            ]
            return candles
        except Exception as e:
            log.warning("Coinbase candle fetch attempt %d failed for %s: %s", attempt + 1, pair, e)
            time.sleep(2 ** attempt)
    return []


def get_coinbase_price(pair: str) -> Optional[float]:
    """Spot price from Coinbase."""
    try:
        r = requests.get(f"https://api.exchange.coinbase.com/products/{pair}/ticker", timeout=5)
        r.raise_for_status()
        return float(r.json()["price"])
    except Exception as e:
        log.warning("Coinbase ticker failed for %s: %s", pair, e)
        return None


# ── DexScreener ──────────────────────────────────────────────────────────────

def get_dexscreener_pair(pair_address: str) -> Optional[dict]:
    """Full pair data by contract address."""
    try:
        r = requests.get(
            f"https://api.dexscreener.com/latest/dex/pairs/ethereum/{pair_address}",
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        pairs = data.get("pairs") or []
        return pairs[0] if pairs else None
    except Exception as e:
        log.warning("DexScreener pair fetch failed: %s", e)
        return None


def scan_trending_tokens(min_liquidity: float = None, min_volume: float = None) -> list:
    """
    Returns trending tokens from DexScreener boosted/trending endpoint.
    Filters by liquidity and 24h volume to surface legit opportunities.
    """
    min_liquidity = min_liquidity or cfg.MEME_MIN_LIQUIDITY_USD
    min_volume = min_volume or cfg.MEME_MIN_VOLUME_24H

    results = []
    # DexScreener public endpoints — no API key needed
    endpoints = [
        "https://api.dexscreener.com/token-boosts/latest/v1",
        "https://api.dexscreener.com/token-boosts/top/v1",
    ]
    seen = set()
    for url in endpoints:
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            tokens = r.json() if isinstance(r.json(), list) else r.json().get("tokens", [])
            for t in tokens:
                addr = t.get("tokenAddress", "")
                chain = t.get("chainId", "")
                key = f"{chain}:{addr}"
                if key in seen or not addr:
                    continue
                seen.add(key)
                # Fetch full pair data for this token
                try:
                    pr = requests.get(
                        f"https://api.dexscreener.com/latest/dex/tokens/{addr}",
                        timeout=8,
                    )
                    pr.raise_for_status()
                    pairs = pr.json().get("pairs") or []
                    if not pairs:
                        continue
                    p = max(pairs, key=lambda x: x.get("volume", {}).get("h24", 0) or 0)
                    liq = (p.get("liquidity") or {}).get("usd", 0) or 0
                    vol = (p.get("volume") or {}).get("h24", 0) or 0
                    price_chg_1h = float((p.get("priceChange") or {}).get("h1", 0) or 0)
                    if liq >= min_liquidity and vol >= min_volume:
                        results.append({
                            "symbol": p.get("baseToken", {}).get("symbol", "?"),
                            "name": p.get("baseToken", {}).get("name", "?"),
                            "address": addr,
                            "chain": chain,
                            "price_usd": float(p.get("priceUsd") or 0),
                            "price_chg_1h": price_chg_1h,
                            "price_chg_24h": float((p.get("priceChange") or {}).get("h24", 0) or 0),
                            "liquidity_usd": liq,
                            "volume_24h": vol,
                            "pair_address": p.get("pairAddress", ""),
                            "dex": p.get("dexId", ""),
                            "url": p.get("url", ""),
                        })
                except Exception:
                    pass
                time.sleep(0.2)
        except Exception as e:
            log.warning("DexScreener trending fetch failed: %s", e)

    # Sort by 1h price change descending (momentum)
    results.sort(key=lambda x: x["price_chg_1h"], reverse=True)
    return results


def search_dexscreener(query: str) -> list:
    """Search DexScreener by token name or symbol."""
    try:
        r = requests.get(
            f"https://api.dexscreener.com/latest/dex/search?q={query}",
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("pairs") or []
    except Exception as e:
        log.warning("DexScreener search failed: %s", e)
        return []


# ── Twitter/X ────────────────────────────────────────────────────────────────

def get_twitter_mentions(query: str, max_results: int = 20) -> list:
    """
    Fetches recent tweets matching a query (requires TWITTER_BEARER_TOKEN in .env).
    Returns list of {text, author_id, created_at, public_metrics}.
    """
    if not cfg.TWITTER_BEARER_TOKEN:
        log.debug("Twitter bearer token not configured — skipping social feed")
        return []
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {cfg.TWITTER_BEARER_TOKEN}"}
    params = {
        "query": f"{query} lang:en -is:retweet",
        "max_results": max(10, min(max_results, 100)),
        "tweet.fields": "created_at,public_metrics,author_id",
    }
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        return r.json().get("data") or []
    except Exception as e:
        log.warning("Twitter search failed for '%s': %s", query, e)
        return []


def score_sentiment(tweets: list) -> float:
    """
    Naive bullish/bearish sentiment score from tweet keywords.
    Returns value in [-1.0, 1.0]. Positive = bullish, negative = bearish.
    """
    if not tweets:
        return 0.0
    bullish_words = {"moon", "buy", "bullish", "pump", "🚀", "breakout", "long", "degen", "gem", "send", "wen", "mooning"}
    bearish_words = {"dump", "sell", "bearish", "rug", "scam", "rekt", "crash", "short", "dead", "exit"}
    score = 0
    for t in tweets:
        text = t.get("text", "").lower()
        likes = (t.get("public_metrics") or {}).get("like_count", 0)
        weight = 1 + (likes ** 0.5) / 10  # weight by engagement
        bull = sum(1 for w in bullish_words if w in text)
        bear = sum(1 for w in bearish_words if w in text)
        score += weight * (bull - bear)
    return max(-1.0, min(1.0, score / (len(tweets) * 3)))


# ── Telegram ─────────────────────────────────────────────────────────────────

def get_telegram_channel_messages(channel: str, limit: int = 20) -> list:
    """
    Reads recent messages from a Telegram channel (requires TELEGRAM_BOT_TOKEN).
    Returns list of message text strings.
    Note: bot must be a member of private channels; public channels work via getUpdates.
    """
    if not cfg.TELEGRAM_BOT_TOKEN or not channel:
        return []
    base = f"https://api.telegram.org/bot{cfg.TELEGRAM_BOT_TOKEN}"
    try:
        r = requests.get(
            f"{base}/getUpdates",
            params={"limit": limit, "allowed_updates": ["channel_post"]},
            timeout=10,
        )
        r.raise_for_status()
        updates = r.json().get("result") or []
        msgs = []
        for u in updates:
            post = u.get("channel_post") or {}
            chat = (post.get("chat") or {})
            if chat.get("username") == channel.lstrip("@") or str(chat.get("id")) == channel:
                if post.get("text"):
                    msgs.append(post["text"])
        return msgs
    except Exception as e:
        log.warning("Telegram fetch failed for %s: %s", channel, e)
        return []


# ── Alpaca (stocks + futures) ─────────────────────────────────────────────────

def get_alpaca_bars(symbol: str, timeframe: str = "1Hour", limit: int = 100) -> list:
    """
    Fetches OHLCV bars from Alpaca for stocks and ETFs.
    Requires ALPACA_API_KEY + ALPACA_SECRET_KEY in .env.
    Returns list of {time, open, high, low, close, volume} dicts.
    """
    if not cfg.ALPACA_API_KEY or not cfg.ALPACA_SECRET_KEY:
        log.debug("Alpaca keys not configured — skipping stock feed for %s", symbol)
        return []
    base = cfg.ALPACA_BASE_URL.replace("api.", "data.").rstrip("/")
    url = f"{base}/v2/stocks/{symbol}/bars"
    headers = {
        "APCA-API-KEY-ID": cfg.ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": cfg.ALPACA_SECRET_KEY,
    }
    params = {"timeframe": timeframe, "limit": limit, "feed": "iex"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        bars = r.json().get("bars") or []
        return [
            {"time": b["t"], "open": b["o"], "high": b["h"],
             "low": b["l"], "close": b["c"], "volume": b["v"]}
            for b in bars
        ]
    except Exception as e:
        log.warning("Alpaca bars failed for %s: %s", symbol, e)
        return []


def get_alpaca_latest_price(symbol: str) -> Optional[float]:
    """Latest trade price from Alpaca."""
    if not cfg.ALPACA_API_KEY or not cfg.ALPACA_SECRET_KEY:
        return None
    base = cfg.ALPACA_BASE_URL.replace("api.", "data.").rstrip("/")
    url = f"{base}/v2/stocks/{symbol}/trades/latest"
    headers = {
        "APCA-API-KEY-ID": cfg.ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": cfg.ALPACA_SECRET_KEY,
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        return float(r.json()["trade"]["p"])
    except Exception as e:
        log.warning("Alpaca price failed for %s: %s", symbol, e)
        return None
