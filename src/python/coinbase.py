"""
Author: etherpilled
Infinite Trading Protocol

Licensed under the MIT License.

Coinbase API client supporting:
- Coinbase Exchange API (public, no auth) for OHLCV candle data
- Coinbase Advanced Trade API v3 (API key + secret) for all authenticated endpoints:
    Accounts, Products, Orders (market/limit/stop-limit GTC/GTD),
    Cancellations, Fills, Portfolios, Fees, Conversions, Payment Methods.

Environment variables (required only for authenticated endpoints):
    COINBASE_API_KEY    – your Coinbase Advanced Trade API key
    COINBASE_API_SECRET – your Coinbase Advanced Trade API secret

Dependencies: pip install requests
"""

import hashlib
import hmac
import json
import os
import time
import uuid
from typing import Optional

import requests

# ── Constants ─────────────────────────────────────────────────────────────────

EXCHANGE_BASE_URL       = "https://api.exchange.coinbase.com"
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
    Client for the Coinbase Advanced Trade REST API v3.

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

    def _post(self, path: str, payload: Optional[dict] = None) -> Optional[dict]:
        url     = f"{self.base_url}{path}"
        body    = json.dumps(payload or {})
        headers = self._headers("POST", path, body)
        try:
            resp = requests.post(url, headers=headers, data=body, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error {resp.status_code}: {err}")
        except requests.exceptions.RequestException as err:
            print(f"Request error: {err}")
        except (ValueError, KeyError) as err:
            print(f"Parse error: {err}")
        return None

    def _put(self, path: str, payload: Optional[dict] = None) -> Optional[dict]:
        url     = f"{self.base_url}{path}"
        body    = json.dumps(payload or {})
        headers = self._headers("PUT", path, body)
        try:
            resp = requests.put(url, headers=headers, data=body, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error {resp.status_code}: {err}")
        except requests.exceptions.RequestException as err:
            print(f"Request error: {err}")
        except (ValueError, KeyError) as err:
            print(f"Parse error: {err}")
        return None

    def _delete(self, path: str) -> Optional[dict]:
        url     = f"{self.base_url}{path}"
        headers = self._headers("DELETE", path)
        try:
            resp = requests.delete(url, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error {resp.status_code}: {err}")
        except requests.exceptions.RequestException as err:
            print(f"Request error: {err}")
        except (ValueError, KeyError) as err:
            print(f"Parse error: {err}")
        return None

    # ── Accounts ──────────────────────────────────────────────────────────────

    def list_accounts(self) -> Optional[list]:
        """Return all portfolios / accounts for the authenticated user."""
        data = self._get("/api/v3/brokerage/accounts")
        if data and "accounts" in data:
            return data["accounts"]
        return None

    def get_account(self, account_uuid: str) -> Optional[dict]:
        """Return a single account by UUID."""
        data = self._get(f"/api/v3/brokerage/accounts/{account_uuid}")
        if data and "account" in data:
            return data["account"]
        return None

    # ── Products ──────────────────────────────────────────────────────────────

    def list_products(
        self,
        product_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Optional[list]:
        """Return available trading products."""
        params: dict = {}
        if product_type:
            params["product_type"] = product_type
        if limit:
            params["limit"] = limit
        data = self._get("/api/v3/brokerage/products", params or None)
        if data and "products" in data:
            return data["products"]
        return None

    def get_product(self, product_id: str) -> Optional[dict]:
        """Return info for a single product, e.g. 'BTC-USD'."""
        return self._get(f"/api/v3/brokerage/products/{product_id}")

    def get_product_book(
        self,
        product_id: str,
        limit: Optional[int] = None,
    ) -> Optional[dict]:
        """Return the best bids/asks (order book) for a product."""
        params: dict = {"product_id": product_id}
        if limit:
            params["limit"] = limit
        return self._get("/api/v3/brokerage/product_book", params)

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

    def get_best_bid_ask(self, product_ids: list) -> Optional[dict]:
        """Return the best bid/ask for the given product IDs."""
        params = {"product_ids": ",".join(product_ids)}
        return self._get("/api/v3/brokerage/best_bid_ask", params)

    # ── Orders ────────────────────────────────────────────────────────────────

    def create_order(
        self,
        product_id: str,
        side: str,
        order_configuration: dict,
        client_order_id: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Place an order. Low-level method; prefer the typed helpers below.

        Args:
            product_id:          e.g. "BTC-USD"
            side:                "BUY" | "SELL"
            order_configuration: Coinbase order_configuration dict.
            client_order_id:     Unique client ID; auto-generated if omitted.
        """
        payload = {
            "client_order_id": client_order_id or str(uuid.uuid4()),
            "product_id":      product_id,
            "side":            side,
            "order_configuration": order_configuration,
        }
        return self._post("/api/v3/brokerage/orders", payload)

    def create_market_order(
        self,
        product_id: str,
        side: str,
        base_size: Optional[str] = None,
        quote_size: Optional[str] = None,
        client_order_id: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Place a market IOC order.
        Supply either base_size (crypto amount) or quote_size (fiat/quote amount).
        """
        ioc: dict = {}
        if base_size:
            ioc["base_size"] = str(base_size)
        if quote_size:
            ioc["quote_size"] = str(quote_size)
        return self.create_order(
            product_id, side,
            {"market_market_ioc": ioc},
            client_order_id,
        )

    def create_limit_order_gtc(
        self,
        product_id: str,
        side: str,
        base_size: str,
        limit_price: str,
        post_only: bool = False,
        client_order_id: Optional[str] = None,
    ) -> Optional[dict]:
        """Place a Good-Till-Cancelled limit order."""
        config = {
            "limit_limit_gtc": {
                "base_size":   str(base_size),
                "limit_price": str(limit_price),
                "post_only":   post_only,
            }
        }
        return self.create_order(product_id, side, config, client_order_id)

    def create_limit_order_gtd(
        self,
        product_id: str,
        side: str,
        base_size: str,
        limit_price: str,
        end_time: str,
        post_only: bool = False,
        client_order_id: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Place a Good-Till-Date limit order.

        Args:
            end_time: ISO 8601 timestamp, e.g. "2025-01-01T00:00:00Z"
        """
        config = {
            "limit_limit_gtd": {
                "base_size":   str(base_size),
                "limit_price": str(limit_price),
                "end_time":    end_time,
                "post_only":   post_only,
            }
        }
        return self.create_order(product_id, side, config, client_order_id)

    def create_stop_limit_order_gtc(
        self,
        product_id: str,
        side: str,
        base_size: str,
        limit_price: str,
        stop_price: str,
        stop_direction: str,
        client_order_id: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Place a Good-Till-Cancelled stop-limit order.

        Args:
            stop_direction: "STOP_DIRECTION_STOP_UP" | "STOP_DIRECTION_STOP_DOWN"
        """
        config = {
            "stop_limit_stop_limit_gtc": {
                "base_size":      str(base_size),
                "limit_price":    str(limit_price),
                "stop_price":     str(stop_price),
                "stop_direction": stop_direction,
            }
        }
        return self.create_order(product_id, side, config, client_order_id)

    def create_stop_limit_order_gtd(
        self,
        product_id: str,
        side: str,
        base_size: str,
        limit_price: str,
        stop_price: str,
        stop_direction: str,
        end_time: str,
        client_order_id: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Place a Good-Till-Date stop-limit order.

        Args:
            stop_direction: "STOP_DIRECTION_STOP_UP" | "STOP_DIRECTION_STOP_DOWN"
            end_time:       ISO 8601 timestamp.
        """
        config = {
            "stop_limit_stop_limit_gtd": {
                "base_size":      str(base_size),
                "limit_price":    str(limit_price),
                "stop_price":     str(stop_price),
                "stop_direction": stop_direction,
                "end_time":       end_time,
            }
        }
        return self.create_order(product_id, side, config, client_order_id)

    def cancel_orders(self, order_ids: list) -> Optional[dict]:
        """Cancel one or more orders by ID."""
        return self._post(
            "/api/v3/brokerage/orders/batch_cancel",
            {"order_ids": order_ids},
        )

    def list_orders(
        self,
        product_id: Optional[str] = None,
        order_status: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Optional[list]:
        """Return historical orders with optional filters."""
        params: dict = {}
        if product_id:
            params["product_id"] = product_id
        if order_status:
            params["order_status"] = order_status
        if limit:
            params["limit"] = limit
        if cursor:
            params["cursor"] = cursor
        data = self._get("/api/v3/brokerage/orders/historical/batch", params or None)
        if data and "orders" in data:
            return data["orders"]
        return None

    def get_order(self, order_id: str) -> Optional[dict]:
        """Return a single historical order by ID."""
        data = self._get(f"/api/v3/brokerage/orders/historical/{order_id}")
        if data and "order" in data:
            return data["order"]
        return None

    def list_fills(
        self,
        order_id: Optional[str] = None,
        product_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Optional[list]:
        """Return fills (trade executions) with optional filters."""
        params: dict = {}
        if order_id:
            params["order_id"] = order_id
        if product_id:
            params["product_id"] = product_id
        if limit:
            params["limit"] = limit
        data = self._get("/api/v3/brokerage/orders/historical/fills", params or None)
        if data and "fills" in data:
            return data["fills"]
        return None

    # ── Portfolios ────────────────────────────────────────────────────────────

    def list_portfolios(self, portfolio_type: Optional[str] = None) -> Optional[list]:
        """Return all portfolios."""
        params = {"portfolio_type": portfolio_type} if portfolio_type else None
        data = self._get("/api/v3/brokerage/portfolios", params)
        if data and "portfolios" in data:
            return data["portfolios"]
        return None

    def create_portfolio(self, name: str) -> Optional[dict]:
        """Create a new portfolio."""
        data = self._post("/api/v3/brokerage/portfolios", {"name": name})
        if data and "portfolio" in data:
            return data["portfolio"]
        return None

    def get_portfolio(self, portfolio_uuid: str) -> Optional[dict]:
        """Return details for a single portfolio."""
        data = self._get(f"/api/v3/brokerage/portfolios/{portfolio_uuid}")
        if data and "breakdown" in data:
            return data["breakdown"]
        return None

    def edit_portfolio(self, portfolio_uuid: str, name: str) -> Optional[dict]:
        """Rename a portfolio."""
        data = self._put(
            f"/api/v3/brokerage/portfolios/{portfolio_uuid}",
            {"name": name},
        )
        if data and "portfolio" in data:
            return data["portfolio"]
        return None

    def delete_portfolio(self, portfolio_uuid: str) -> Optional[dict]:
        """Delete a portfolio (must be empty)."""
        return self._delete(f"/api/v3/brokerage/portfolios/{portfolio_uuid}")

    def move_portfolio_funds(
        self,
        funds: str,
        currency: str,
        source_portfolio_uuid: str,
        target_portfolio_uuid: str,
    ) -> Optional[dict]:
        """Move funds between portfolios."""
        payload = {
            "funds": {"value": str(funds), "currency": currency},
            "source_portfolio_uuid": source_portfolio_uuid,
            "target_portfolio_uuid": target_portfolio_uuid,
        }
        return self._post("/api/v3/brokerage/portfolios/move_funds", payload)

    # ── Fees ──────────────────────────────────────────────────────────────────

    def get_transaction_summary(
        self,
        product_type: Optional[str] = None,
        contract_expiry_type: Optional[str] = None,
    ) -> Optional[dict]:
        """Return fee tier and 30-day trading volume summary."""
        params: dict = {}
        if product_type:
            params["product_type"] = product_type
        if contract_expiry_type:
            params["contract_expiry_type"] = contract_expiry_type
        return self._get("/api/v3/brokerage/transaction_summary", params or None)

    # ── Conversions ───────────────────────────────────────────────────────────

    def create_convert_quote(
        self,
        from_account: str,
        to_account: str,
        amount: str,
    ) -> Optional[dict]:
        """Create a conversion quote (preview, does not execute)."""
        payload = {
            "from_account": from_account,
            "to_account":   to_account,
            "amount":       str(amount),
        }
        return self._post("/api/v3/brokerage/convert/quote", payload)

    def get_convert_trade(self, trade_id: str, from_account: str, to_account: str) -> Optional[dict]:
        """Return the status of an existing conversion."""
        params = {"from_account": from_account, "to_account": to_account}
        return self._get(f"/api/v3/brokerage/convert/trade/{trade_id}", params)

    def commit_convert_trade(
        self,
        trade_id: str,
        from_account: str,
        to_account: str,
    ) -> Optional[dict]:
        """Execute (commit) a previously created conversion quote."""
        payload = {"from_account": from_account, "to_account": to_account}
        return self._post(f"/api/v3/brokerage/convert/trade/{trade_id}", payload)

    # ── Payment Methods ───────────────────────────────────────────────────────

    def list_payment_methods(self) -> Optional[list]:
        """Return all payment methods linked to the account."""
        data = self._get("/api/v3/brokerage/payment_methods")
        if data and "payment_methods" in data:
            return data["payment_methods"]
        return None

    def get_payment_method(self, payment_method_id: str) -> Optional[dict]:
        """Return a single payment method by ID."""
        data = self._get(f"/api/v3/brokerage/payment_methods/{payment_method_id}")
        if data and "payment_method" in data:
            return data["payment_method"]
        return None


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
