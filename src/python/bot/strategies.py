"""
Technical analysis indicators and signal generation.
All functions operate on plain Python lists of floats (close prices etc.)
so there are no heavy dependencies beyond basic math.
"""
import math
from typing import Optional


# ── Indicators ────────────────────────────────────────────────────────────────

def ema(prices: list, period: int) -> list:
    """Exponential moving average. Returns same-length list (NaN-padded at front)."""
    if len(prices) < period:
        return [float("nan")] * len(prices)
    result = [float("nan")] * len(prices)
    k = 2 / (period + 1)
    # seed with SMA
    sma = sum(prices[:period]) / period
    result[period - 1] = sma
    for i in range(period, len(prices)):
        result[i] = prices[i] * k + result[i - 1] * (1 - k)
    return result


def sma(prices: list, period: int) -> list:
    result = [float("nan")] * len(prices)
    for i in range(period - 1, len(prices)):
        result[i] = sum(prices[i - period + 1 : i + 1]) / period
    return result


def rsi(prices: list, period: int = 14) -> list:
    result = [float("nan")] * len(prices)
    if len(prices) < period + 1:
        return result
    gains, losses = [], []
    for i in range(1, len(prices)):
        delta = prices[i] - prices[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(prices)):
        idx = i - period
        avg_gain = (avg_gain * (period - 1) + gains[idx]) / period
        avg_loss = (avg_loss * (period - 1) + losses[idx]) / period
        if avg_loss == 0:
            result[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i] = 100.0 - (100.0 / (1 + rs))
    return result


def bollinger_bands(prices: list, period: int = 20, std_dev: float = 2.0):
    """Returns (upper, middle, lower) lists."""
    mid = sma(prices, period)
    upper = [float("nan")] * len(prices)
    lower = [float("nan")] * len(prices)
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1 : i + 1]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        sd = math.sqrt(variance)
        upper[i] = mid[i] + std_dev * sd
        lower[i] = mid[i] - std_dev * sd
    return upper, mid, lower


def atr(highs: list, lows: list, closes: list, period: int = 14) -> list:
    """Average True Range."""
    trs = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    result = [float("nan")] * len(closes)
    result[period - 1] = sum(trs[:period]) / period
    for i in range(period, len(closes)):
        result[i] = (result[i - 1] * (period - 1) + trs[i]) / period
    return result


def volume_spike(volumes: list, lookback: int = 20) -> list:
    """Returns ratio of current volume to rolling average (> 2.0 = spike)."""
    result = [float("nan")] * len(volumes)
    for i in range(lookback, len(volumes)):
        avg = sum(volumes[i - lookback : i]) / lookback
        result[i] = volumes[i] / avg if avg > 0 else 1.0
    return result


# ── Signal generation ─────────────────────────────────────────────────────────

def _nan_safe(val) -> float:
    return val if val is not None and not (isinstance(val, float) and math.isnan(val)) else float("nan")


def momentum_signal(candles: list, rsi_period: int = 14, fast: int = 9, slow: int = 21) -> dict:
    """
    Combines RSI + EMA crossover + volume to produce a signal.

    Returns:
        signal: "BUY" | "SELL" | "HOLD"
        confidence: 0.0 – 1.0
        reason: human-readable string
        indicators: dict of current indicator values
    """
    if len(candles) < slow + 5:
        return {"signal": "HOLD", "confidence": 0.0, "reason": "not enough data", "indicators": {}}

    closes = [c["close"] for c in candles][::-1]   # oldest→newest
    highs  = [c["high"]  for c in candles][::-1]
    lows   = [c["low"]   for c in candles][::-1]
    vols   = [c["volume"] for c in candles][::-1]

    rsi_vals   = rsi(closes, rsi_period)
    ema_f      = ema(closes, fast)
    ema_s      = ema(closes, slow)
    vol_ratio  = volume_spike(vols)
    atr_vals   = atr(highs, lows, closes, 14)

    cur_rsi   = _nan_safe(rsi_vals[-1])
    cur_ema_f = _nan_safe(ema_f[-1])
    cur_ema_s = _nan_safe(ema_s[-1])
    prev_ema_f = _nan_safe(ema_f[-2])
    prev_ema_s = _nan_safe(ema_s[-2])
    cur_vol_r  = _nan_safe(vol_ratio[-1])
    cur_atr    = _nan_safe(atr_vals[-1])
    cur_price  = closes[-1]

    if any(math.isnan(v) for v in [cur_rsi, cur_ema_f, cur_ema_s, prev_ema_f, prev_ema_s]):
        return {"signal": "HOLD", "confidence": 0.0, "reason": "indicator not ready", "indicators": {}}

    # EMA crossover
    cross_up   = prev_ema_f <= prev_ema_s and cur_ema_f > cur_ema_s
    cross_down = prev_ema_f >= prev_ema_s and cur_ema_f < cur_ema_s
    trend_up   = cur_ema_f > cur_ema_s
    trend_down = cur_ema_f < cur_ema_s

    # RSI zones
    oversold     = cur_rsi < 35
    overbought   = cur_rsi > 65
    rsi_rising   = cur_rsi > rsi_vals[-3] if len(rsi_vals) >= 3 and not math.isnan(rsi_vals[-3]) else False
    rsi_falling  = cur_rsi < rsi_vals[-3] if len(rsi_vals) >= 3 and not math.isnan(rsi_vals[-3]) else False

    # Volume confirmation
    vol_confirm = (not math.isnan(cur_vol_r)) and cur_vol_r > 1.5

    reasons = []
    score = 0.0

    if trend_up:    score += 0.25
    if trend_down:  score -= 0.25
    if cross_up:    score += 0.35; reasons.append("EMA crossover up")
    if cross_down:  score -= 0.35; reasons.append("EMA crossover down")
    if oversold and rsi_rising:   score += 0.25; reasons.append(f"RSI oversold ({cur_rsi:.1f})")
    if overbought and rsi_falling: score -= 0.25; reasons.append(f"RSI overbought ({cur_rsi:.1f})")
    if vol_confirm and score > 0: score += 0.15; reasons.append(f"volume spike {cur_vol_r:.1f}x")
    if vol_confirm and score < 0: score -= 0.15

    signal = "HOLD"
    confidence = abs(score)
    if score >= 0.4:
        signal = "BUY"
    elif score <= -0.4:
        signal = "SELL"

    return {
        "signal": signal,
        "confidence": round(min(confidence, 1.0), 3),
        "reason": ", ".join(reasons) if reasons else "no strong signal",
        "indicators": {
            "rsi": round(cur_rsi, 2),
            "ema_fast": round(cur_ema_f, 6),
            "ema_slow": round(cur_ema_s, 6),
            "atr": round(cur_atr, 6) if not math.isnan(cur_atr) else None,
            "vol_ratio": round(cur_vol_r, 2) if not math.isnan(cur_vol_r) else None,
            "price": cur_price,
        },
    }


def meme_coin_signal(token: dict, social_sentiment: float = 0.0) -> dict:
    """
    Signal for DexScreener meme tokens based on price momentum + social sentiment.
    token: dict from scan_trending_tokens()
    social_sentiment: float in [-1, 1] from score_sentiment()
    """
    chg_1h  = token.get("price_chg_1h", 0)
    chg_24h = token.get("price_chg_24h", 0)
    liq     = token.get("liquidity_usd", 0)
    vol     = token.get("volume_24h", 0)

    score = 0.0
    reasons = []

    # Momentum score
    if chg_1h > 10:   score += 0.4; reasons.append(f"+{chg_1h:.1f}% 1h")
    elif chg_1h > 5:  score += 0.2; reasons.append(f"+{chg_1h:.1f}% 1h")
    elif chg_1h < -10: score -= 0.3; reasons.append(f"{chg_1h:.1f}% 1h drop")

    # 24h context
    if chg_24h > 50:  score += 0.2; reasons.append(f"+{chg_24h:.1f}% 24h")
    elif chg_24h < -30: score -= 0.2

    # Liquidity quality
    if liq > 500_000:   score += 0.15
    elif liq < 100_000: score -= 0.1  # thin — risky

    # Social boost
    score += social_sentiment * 0.25
    if social_sentiment > 0.3: reasons.append(f"social bullish ({social_sentiment:.2f})")

    signal = "HOLD"
    confidence = round(min(abs(score), 1.0), 3)
    if score >= 0.45:
        signal = "BUY"
    elif score <= -0.35:
        signal = "AVOID"

    return {
        "signal": signal,
        "confidence": confidence,
        "reason": ", ".join(reasons) if reasons else "low conviction",
        "score": round(score, 3),
    }
