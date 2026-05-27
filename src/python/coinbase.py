"""
Author: etherpilled
Infinite Trading Protocol

Licensed under the MIT License.

Coinbase API client supporting:
- Coinbase Exchange API (public, no auth) for OHLCV candle data
- Coinbase Advanced Trade API (API key + secret) for authenticated endpoints

Environment variables (required only for authenticated endpoints):
    COINBASE_API_KEY    – your Coinbase API key
    COINBASE_API_SECRET – your Coinbase API secret

Dependencies: pip install requests
"""

import hashlib
import hmac
import os
import time
from typing import Optional

import requests

# ── Constants ─────────────────────────────────────────────────────────────────

EXCHANGE_BASE_URL      = "https://api.exchange.coinbase.com"
ADVANCED_TRADE_BASE_URL = "https://api.coinbase.com"

TIMEFRAME_TO_GRANULARITY: dict[str, int] = {
    "1m":  60,
    "5m":  300,
    "15m": 900,
    "1h":  3600,
    "6h":  21600,
    "1d":  86400,
    "1w":  604800,
}

# Kept for backward compatibility
timeframe_to_seconds = TIMEFRAME_TO_GRANULARITY


# ── Public Exchange API ────────────────────────────────────────────────────────

def get_candles(
    pair: str,
    numcandles: int,
    timeframe: str,
    exchange: str = "coinbase",
) -> Optional[list]:
    """
    Fetch historical OHLCV candles from the Coinbase Exchange API.

    Args:
        pair:       Trading pair, e.g. "BTC-USD" or "BTC_USD".
        numcandles: Maximum number of candles to return (most-recent first).
        timeframe:  One of '1m','5m','15m','1h','6h','1d','1w'.
        exchange:   Ignored; retained for API compatibility.

    Returns:
        List of candle arrays [timestamp, low, high, open, close, volume],
        or None on any error.
    """
    product_id  = pair.replace("_", "-")
    granularity = TIMEFRAME_TO_GRANULARITY.get(timeframe)

    if granularity is None:
        print(f"Error: unknown timeframe '{timeframe}'. Valid options: {list(TIMEFRAME_TO_GRANULARITY)}")
        return None

    url    = f"{EXCHANGE_BASE_URL}/products/{product_id}/candles"
    params = {"granularity": granularity}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        candles = response.json()
        return candles[:numcandles] if len(candles) > numcandles else candles

    except requests.exceptions.HTTPError as err:
        print(f"HTTP error: {err} – {response.text}")
    except requests.exceptions.RequestException as err:
        print(f"Request error: {err}")
    except (ValueError, KeyError) as err:
        print(f"Parse error: {err}")
    except Exception as err:
        print(f"Unexpected error fetching candles: {err}")

    return None


def get_candles_with_retry(
    pair: str,
    numcandles: int,
    timeframe: str,
    exchange: str = "coinbase",
    retries: int = 3,
    delay: float = 1.0,
) -> Optional[list]:
    """
    Retry wrapper around get_candles.
    Stops immediately on rate-limit / IP-ban errors.
    """
    for attempt in range(retries):
        try:
            candles = get_candles(pair, numcandles, timeframe, exchange)
            if candles is not None:
                return candles
        except Exception as err:
            msg = str(err).lower()
            print(f"Error fetching candles (attempt {attempt + 1}/{retries}): {err}")
            if any(k in msg for k in ("ban", "403", "rate limit")):
                print("Rate-limited or IP-banned – stopping retries.")
                return None

        if attempt < retries - 1:
            print(f"Retrying in {delay}s… ({attempt + 1}/{retries})")
            time.sleep(delay)

    return None


# ── Authenticated Advanced Trade API ──────────────────────────────────────────

class CoinbaseAdvancedClient:
    """
    Client for the Coinbase Advanced Trade REST API.

    Authentication uses HMAC-SHA256 signed headers (legacy API keys from
    coinbase.com/settings/api). CDP (cloud.coinbase.com) keys use JWT —
    see Coinbase docs for that variant.

    Usage:
        client = CoinbaseAdvancedClient()        # reads env vars
        client = CoinbaseAdvancedClient(api_key="...", api_secret="...")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ) -> None:
        self.api_key    = api_key    or os.environ.get("COINBASE_API_KEY",    "")
        self.api_secret = api_secret or os.environ.get("COINBASE_API_SECRET", "")
        self.base_url   = ADVANCED_TRADE_BASE_URL

    # ── Request helpers ────────────────────────────────────────────────────────

    def _headers(self, method: str, path: str, body: str = "") -> dict:
        """Build CB-ACCESS-* HMAC-SHA256 authentication headers."""
        timestamp = str(int(time.time()))
        message   = f"{timestamp}{method.upper()}{path}{body}"
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return {
            "CB-ACCESS-KEY":       self.api_key,
            "CB-ACCESS-SIGN":      signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "Content-Type":        "application/json",
        }

    def _get(self, path: str, params: Optional[dict] = None) -> Optional[dict]:
        url     = f"{self.base_url}{path}"
        headers = self._headers("GET", path)
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error {resp.status_code}: {err}")
        except requests.exceptions.RequestException as err:
            print(f"Request error: {err}")
        except (ValueError, KeyError) as err:
            print(f"Parse error: {err}")
        return None

    # ── Market data (public, but included here for convenience) ───────────────

    def get_product_candles(
        self,
        product_id: str,
        start: int,
        end: int,
        granularity: str = "ONE_HOUR",
    ) -> Optional[list]:
        """
        Fetch candles from the Advanced Trade API.

        Args:
            product_id:  e.g. "BTC-USD"
            start:       Unix timestamp (seconds) – range start.
            end:         Unix timestamp (seconds) – range end.
            granularity: ONE_MINUTE | FIVE_MINUTE | FIFTEEN_MINUTE |
                         THIRTY_MINUTE | ONE_HOUR | TWO_HOUR | SIX_HOUR | ONE_DAY
        """
        path   = f"/api/v3/brokerage/products/{product_id}/candles"
        params = {"start": start, "end": end, "granularity": granularity}
        data   = self._get(path, params)
        if data and "candles" in data:
            return data["candles"]
        return None

    # ── Authenticated endpoints ────────────────────────────────────────────────

    def list_accounts(self) -> Optional[list]:
        """Return all portfolios / accounts for the authenticated user."""
        data = self._get("/api/v3/brokerage/accounts")
        if data and "accounts" in data:
            return data["accounts"]
        return None

    def get_best_bid_ask(self, product_ids: list) -> Optional[dict]:
        """Return the best bid/ask for the given product IDs."""
        params = {"product_ids": ",".join(product_ids)}
        return self._get("/api/v3/brokerage/best_bid_ask", params)


# ── CLI entry point ────────────────────────────────────────────────────────────

def main() -> None:
    pairs      = ["BTC-USD", "ETH-USD", "POL-USD", "ARB-USD", "VELO-USD",
                  "AERO-USD", "LINK-USD", "SOL-USD"]
    timeframe  = "1h"
    numcandles = 300

    for pair in pairs:
        candles = get_candles_with_retry(pair, numcandles, timeframe)
        if candles:
            print(f"Fetched {len(candles)} candles for {pair}.")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
