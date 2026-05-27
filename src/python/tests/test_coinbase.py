"""
Tests for coinbase.py
All HTTP calls are mocked – no real network requests are made.

Run with:  pytest src/python/tests/
"""

import json
import os
import sys
from unittest.mock import MagicMock, call, patch

import pytest

# Allow importing coinbase.py from the parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests as _requests  # imported solely for exception types in tests

from coinbase import (
    TIMEFRAME_TO_GRANULARITY,
    CoinbaseAdvancedClient,
    get_candles,
    get_candles_with_retry,
)

# ── Shared fixtures ────────────────────────────────────────────────────────────

SAMPLE_CANDLES = [
    [1700000000, 37000.0, 38000.0, 37500.0, 37800.0, 100.5],
    [1699996400, 36500.0, 37200.0, 36800.0, 37000.0,  95.2],
    [1699992800, 36000.0, 36800.0, 36200.0, 36500.0,  88.7],
]


def _ok_response(data, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = data
    mock.raise_for_status.return_value = None
    return mock


def _error_response(status_code: int, text: str = "Error") -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = text
    mock.raise_for_status.side_effect = _requests.exceptions.HTTPError(
        f"{status_code} Error"
    )
    return mock


# ── get_candles ───────────────────────────────────────────────────────────────

class TestGetCandles:
    def test_returns_candles_on_success(self):
        with patch("coinbase.requests.get", return_value=_ok_response(SAMPLE_CANDLES)):
            result = get_candles("BTC-USD", 10, "1h")
        assert result == SAMPLE_CANDLES

    def test_limits_to_numcandles(self):
        large = SAMPLE_CANDLES * 10  # 30 candles
        with patch("coinbase.requests.get", return_value=_ok_response(large)):
            result = get_candles("BTC-USD", 5, "1h")
        assert len(result) == 5

    def test_returns_all_when_fewer_than_numcandles(self):
        with patch("coinbase.requests.get", return_value=_ok_response(SAMPLE_CANDLES)):
            result = get_candles("BTC-USD", 100, "1h")
        assert len(result) == len(SAMPLE_CANDLES)

    def test_normalises_underscore_pair(self):
        with patch("coinbase.requests.get", return_value=_ok_response(SAMPLE_CANDLES)) as mock_get:
            get_candles("BTC_USD", 10, "1h")
        url = mock_get.call_args[0][0]
        assert "BTC-USD" in url

    def test_uses_correct_granularity_1h(self):
        with patch("coinbase.requests.get", return_value=_ok_response(SAMPLE_CANDLES)) as mock_get:
            get_candles("BTC-USD", 10, "1h")
        assert mock_get.call_args[1]["params"]["granularity"] == 3600

    def test_uses_correct_granularity_1d(self):
        with patch("coinbase.requests.get", return_value=_ok_response(SAMPLE_CANDLES)) as mock_get:
            get_candles("BTC-USD", 10, "1d")
        assert mock_get.call_args[1]["params"]["granularity"] == 86400

    def test_uses_correct_granularity_1w(self):
        with patch("coinbase.requests.get", return_value=_ok_response(SAMPLE_CANDLES)) as mock_get:
            get_candles("BTC-USD", 10, "1w")
        assert mock_get.call_args[1]["params"]["granularity"] == 604800

    def test_returns_none_for_unknown_timeframe(self):
        result = get_candles("BTC-USD", 10, "3h")
        assert result is None

    def test_returns_none_on_http_error(self):
        with patch("coinbase.requests.get", return_value=_error_response(404)):
            result = get_candles("BTC-USD", 10, "1h")
        assert result is None

    def test_returns_none_on_connection_error(self):
        with patch("coinbase.requests.get", side_effect=_requests.exceptions.ConnectionError("refused")):
            result = get_candles("BTC-USD", 10, "1h")
        assert result is None

    def test_returns_none_on_json_parse_error(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.side_effect = ValueError("Invalid JSON")
        with patch("coinbase.requests.get", return_value=mock_resp):
            result = get_candles("BTC-USD", 10, "1h")
        assert result is None

    @pytest.mark.parametrize("timeframe", list(TIMEFRAME_TO_GRANULARITY.keys()))
    def test_all_supported_timeframes_succeed(self, timeframe):
        with patch("coinbase.requests.get", return_value=_ok_response(SAMPLE_CANDLES)):
            result = get_candles("BTC-USD", 10, timeframe)
        assert result is not None, f"Timeframe '{timeframe}' should be supported"

    def test_exchange_param_is_ignored(self):
        with patch("coinbase.requests.get", return_value=_ok_response(SAMPLE_CANDLES)) as mock_get:
            get_candles("BTC-USD", 10, "1h", exchange="some_exchange")
        url = mock_get.call_args[0][0]
        assert "coinbase.com" in url


# ── get_candles_with_retry ────────────────────────────────────────────────────

class TestGetCandlesWithRetry:
    def test_returns_candles_on_first_success(self):
        with patch("coinbase.get_candles", return_value=SAMPLE_CANDLES):
            result = get_candles_with_retry("BTC-USD", 10, "1h")
        assert result == SAMPLE_CANDLES

    def test_retries_on_none_result_then_succeeds(self):
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return SAMPLE_CANDLES if call_count >= 3 else None

        with patch("coinbase.get_candles", side_effect=side_effect), \
             patch("coinbase.time.sleep"):
            result = get_candles_with_retry("BTC-USD", 10, "1h", retries=3, delay=0)

        assert result == SAMPLE_CANDLES
        assert call_count == 3

    def test_returns_none_after_all_retries_exhausted(self):
        with patch("coinbase.get_candles", return_value=None), \
             patch("coinbase.time.sleep"):
            result = get_candles_with_retry("BTC-USD", 10, "1h", retries=3, delay=0)
        assert result is None

    def test_default_retries_is_3(self):
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return None

        with patch("coinbase.get_candles", side_effect=side_effect), \
             patch("coinbase.time.sleep"):
            get_candles_with_retry("BTC-USD", 10, "1h")

        assert call_count == 3

    def test_stops_on_rate_limit_error(self):
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise Exception("403 rate limit exceeded")

        with patch("coinbase.get_candles", side_effect=side_effect), \
             patch("coinbase.time.sleep"):
            result = get_candles_with_retry("BTC-USD", 10, "1h", retries=5, delay=0)

        assert result is None
        assert call_count == 1, "Should stop immediately on rate-limit error"

    def test_stops_on_ip_ban_error(self):
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise Exception("IP ban detected by server")

        with patch("coinbase.get_candles", side_effect=side_effect), \
             patch("coinbase.time.sleep"):
            result = get_candles_with_retry("BTC-USD", 10, "1h", retries=5, delay=0)

        assert result is None
        assert call_count == 1

    def test_retries_transient_errors(self):
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("temporary network timeout")
            return SAMPLE_CANDLES

        with patch("coinbase.get_candles", side_effect=side_effect), \
             patch("coinbase.time.sleep"):
            result = get_candles_with_retry("BTC-USD", 10, "1h", retries=5, delay=0)

        assert result == SAMPLE_CANDLES
        assert call_count == 3

    def test_sleeps_between_retries(self):
        sleep_calls = []

        with patch("coinbase.get_candles", return_value=None), \
             patch("coinbase.time.sleep", side_effect=sleep_calls.append):
            get_candles_with_retry("BTC-USD", 10, "1h", retries=3, delay=1.5)

        assert len(sleep_calls) == 2
        assert all(v == 1.5 for v in sleep_calls)


# ── CoinbaseAdvancedClient — shared setup ─────────────────────────────────────

class _ClientBase:
    def setup_method(self):
        self.client = CoinbaseAdvancedClient(api_key="test-key", api_secret="test-secret")


# ── Init & headers ────────────────────────────────────────────────────────────

class TestCoinbaseAdvancedClientInit(_ClientBase):
    def test_init_explicit_credentials(self):
        c = CoinbaseAdvancedClient(api_key="k", api_secret="s")
        assert c.api_key == "k"
        assert c.api_secret == "s"

    def test_init_reads_env_vars(self, monkeypatch):
        monkeypatch.setenv("COINBASE_API_KEY", "env-key")
        monkeypatch.setenv("COINBASE_API_SECRET", "env-secret")
        c = CoinbaseAdvancedClient()
        assert c.api_key == "env-key"
        assert c.api_secret == "env-secret"

    def test_headers_contain_required_fields(self):
        headers = self.client._headers("GET", "/api/v3/brokerage/accounts")
        assert "CB-ACCESS-KEY"       in headers
        assert "CB-ACCESS-SIGN"      in headers
        assert "CB-ACCESS-TIMESTAMP" in headers

    def test_headers_key_matches_api_key(self):
        headers = self.client._headers("GET", "/some/path")
        assert headers["CB-ACCESS-KEY"] == "test-key"

    def test_headers_signature_is_hex_string(self):
        headers = self.client._headers("GET", "/some/path")
        sig = headers["CB-ACCESS-SIGN"]
        assert isinstance(sig, str)
        int(sig, 16)  # must be valid hex


# ── HTTP helpers ──────────────────────────────────────────────────────────────

class TestHttpHelpers(_ClientBase):
    def test_post_returns_json_on_success(self):
        mock_data = {"order_id": "abc123"}
        with patch("coinbase.requests.post", return_value=_ok_response(mock_data)):
            result = self.client._post("/api/v3/brokerage/orders", {"key": "val"})
        assert result == mock_data

    def test_post_returns_none_on_http_error(self):
        with patch("coinbase.requests.post", return_value=_error_response(400)):
            result = self.client._post("/api/v3/brokerage/orders", {})
        assert result is None

    def test_post_sends_json_body(self):
        payload = {"product_id": "BTC-USD", "side": "BUY"}
        with patch("coinbase.requests.post", return_value=_ok_response({})) as mock_post:
            self.client._post("/api/v3/brokerage/orders", payload)
        sent_body = mock_post.call_args[1]["data"]
        assert json.loads(sent_body) == payload

    def test_put_returns_json_on_success(self):
        mock_data = {"portfolio": {"name": "renamed"}}
        with patch("coinbase.requests.put", return_value=_ok_response(mock_data)):
            result = self.client._put("/api/v3/brokerage/portfolios/uuid-1", {"name": "renamed"})
        assert result == mock_data

    def test_put_returns_none_on_http_error(self):
        with patch("coinbase.requests.put", return_value=_error_response(403)):
            result = self.client._put("/api/v3/brokerage/portfolios/uuid-1", {})
        assert result is None

    def test_delete_returns_json_on_success(self):
        with patch("coinbase.requests.delete", return_value=_ok_response({})):
            result = self.client._delete("/api/v3/brokerage/portfolios/uuid-1")
        assert result == {}

    def test_delete_returns_none_on_http_error(self):
        with patch("coinbase.requests.delete", return_value=_error_response(404)):
            result = self.client._delete("/api/v3/brokerage/portfolios/bad-uuid")
        assert result is None


# ── Accounts ──────────────────────────────────────────────────────────────────

class TestAccounts(_ClientBase):
    def test_list_accounts_returns_account_list(self):
        mock_data = {"accounts": [{"uuid": "abc123", "name": "BTC Wallet"}]}
        with patch("coinbase.requests.get", return_value=_ok_response(mock_data)):
            result = self.client.list_accounts()
        assert result == mock_data["accounts"]

    def test_list_accounts_returns_none_on_missing_key(self):
        with patch("coinbase.requests.get", return_value=_ok_response({"error": "UNAUTHORIZED"})):
            result = self.client.list_accounts()
        assert result is None

    def test_list_accounts_returns_none_on_http_error(self):
        with patch("coinbase.requests.get", return_value=_error_response(403)):
            result = self.client.list_accounts()
        assert result is None

    def test_get_account_returns_account(self):
        mock_data = {"account": {"uuid": "uuid-1", "currency": "BTC"}}
        with patch("coinbase.requests.get", return_value=_ok_response(mock_data)):
            result = self.client.get_account("uuid-1")
        assert result == mock_data["account"]

    def test_get_account_returns_none_on_error(self):
        with patch("coinbase.requests.get", return_value=_error_response(404)):
            result = self.client.get_account("bad-uuid")
        assert result is None

    def test_get_account_uses_uuid_in_path(self):
        with patch("coinbase.requests.get", return_value=_ok_response({"account": {}})) as mock_get:
            self.client.get_account("my-uuid-123")
        url = mock_get.call_args[0][0]
        assert "my-uuid-123" in url


# ── Products ──────────────────────────────────────────────────────────────────

class TestProducts(_ClientBase):
    def test_list_products_returns_list(self):
        mock_data = {"products": [{"product_id": "BTC-USD"}]}
        with patch("coinbase.requests.get", return_value=_ok_response(mock_data)):
            result = self.client.list_products()
        assert result == mock_data["products"]

    def test_list_products_returns_none_on_error(self):
        with patch("coinbase.requests.get", return_value=_error_response(500)):
            result = self.client.list_products()
        assert result is None

    def test_list_products_passes_product_type(self):
        with patch("coinbase.requests.get", return_value=_ok_response({"products": []})) as mock_get:
            self.client.list_products(product_type="SPOT")
        params = mock_get.call_args[1]["params"]
        assert params["product_type"] == "SPOT"

    def test_get_product_returns_dict(self):
        mock_data = {"product_id": "BTC-USD", "base_currency": "BTC"}
        with patch("coinbase.requests.get", return_value=_ok_response(mock_data)):
            result = self.client.get_product("BTC-USD")
        assert result == mock_data

    def test_get_product_returns_none_on_error(self):
        with patch("coinbase.requests.get", return_value=_error_response(404)):
            result = self.client.get_product("FAKE-USD")
        assert result is None

    def test_get_product_book_returns_dict(self):
        mock_data = {"pricebook": {"product_id": "BTC-USD", "bids": [], "asks": []}}
        with patch("coinbase.requests.get", return_value=_ok_response(mock_data)):
            result = self.client.get_product_book("BTC-USD")
        assert result == mock_data

    def test_get_product_book_passes_product_id(self):
        with patch("coinbase.requests.get", return_value=_ok_response({})) as mock_get:
            self.client.get_product_book("ETH-USD")
        params = mock_get.call_args[1]["params"]
        assert params["product_id"] == "ETH-USD"

    def test_get_product_candles_returns_list(self):
        mock_data = {
            "candles": [
                {"start": "1700000000", "low": "37000", "high": "38000",
                 "open": "37500", "close": "37800", "volume": "100.5"}
            ]
        }
        with patch("coinbase.requests.get", return_value=_ok_response(mock_data)):
            result = self.client.get_product_candles("BTC-USD", 1699990000, 1700000000)
        assert result == mock_data["candles"]

    def test_get_product_candles_returns_none_on_http_error(self):
        with patch("coinbase.requests.get", return_value=_error_response(401)):
            result = self.client.get_product_candles("BTC-USD", 1699990000, 1700000000)
        assert result is None

    def test_get_product_candles_returns_none_on_missing_key(self):
        with patch("coinbase.requests.get", return_value=_ok_response({"error": "UNAUTHORIZED"})):
            result = self.client.get_product_candles("BTC-USD", 1699990000, 1700000000)
        assert result is None

    def test_get_best_bid_ask_passes_product_ids(self):
        with patch("coinbase.requests.get", return_value=_ok_response({"pricebooks": []})) as mock_get:
            self.client.get_best_bid_ask(["BTC-USD", "ETH-USD"])
        params = mock_get.call_args[1]["params"]
        assert "BTC-USD" in params["product_ids"]
        assert "ETH-USD" in params["product_ids"]

    def test_get_best_bid_ask_returns_none_on_error(self):
        with patch("coinbase.requests.get", return_value=_error_response(500)):
            result = self.client.get_best_bid_ask(["BTC-USD"])
        assert result is None


# ── Orders ────────────────────────────────────────────────────────────────────

class TestOrders(_ClientBase):
    _ORDER_RESP = {"success": True, "order_id": "order-abc"}

    def test_create_order_returns_dict(self):
        with patch("coinbase.requests.post", return_value=_ok_response(self._ORDER_RESP)):
            result = self.client.create_order(
                "BTC-USD", "BUY",
                {"market_market_ioc": {"base_size": "0.01"}},
            )
        assert result == self._ORDER_RESP

    def test_create_order_auto_generates_client_order_id(self):
        with patch("coinbase.requests.post", return_value=_ok_response({})) as mock_post:
            self.client.create_order("BTC-USD", "BUY", {"market_market_ioc": {}})
        body = json.loads(mock_post.call_args[1]["data"])
        assert "client_order_id" in body
        assert len(body["client_order_id"]) == 36  # UUID format

    def test_create_order_uses_provided_client_order_id(self):
        with patch("coinbase.requests.post", return_value=_ok_response({})) as mock_post:
            self.client.create_order(
                "BTC-USD", "BUY", {"market_market_ioc": {}},
                client_order_id="my-id-123",
            )
        body = json.loads(mock_post.call_args[1]["data"])
        assert body["client_order_id"] == "my-id-123"

    def test_create_order_returns_none_on_error(self):
        with patch("coinbase.requests.post", return_value=_error_response(400)):
            result = self.client.create_order("BTC-USD", "BUY", {})
        assert result is None

    def test_create_market_order_sets_base_size(self):
        with patch("coinbase.requests.post", return_value=_ok_response({})) as mock_post:
            self.client.create_market_order("BTC-USD", "BUY", base_size="0.01")
        body = json.loads(mock_post.call_args[1]["data"])
        cfg = body["order_configuration"]["market_market_ioc"]
        assert cfg["base_size"] == "0.01"

    def test_create_market_order_sets_quote_size(self):
        with patch("coinbase.requests.post", return_value=_ok_response({})) as mock_post:
            self.client.create_market_order("ETH-USD", "SELL", quote_size="100")
        body = json.loads(mock_post.call_args[1]["data"])
        cfg = body["order_configuration"]["market_market_ioc"]
        assert cfg["quote_size"] == "100"

    def test_create_limit_order_gtc_payload(self):
        with patch("coinbase.requests.post", return_value=_ok_response({})) as mock_post:
            self.client.create_limit_order_gtc("BTC-USD", "BUY", "0.01", "50000")
        body = json.loads(mock_post.call_args[1]["data"])
        cfg = body["order_configuration"]["limit_limit_gtc"]
        assert cfg["base_size"]   == "0.01"
        assert cfg["limit_price"] == "50000"
        assert cfg["post_only"]   is False

    def test_create_limit_order_gtc_post_only(self):
        with patch("coinbase.requests.post", return_value=_ok_response({})) as mock_post:
            self.client.create_limit_order_gtc("BTC-USD", "BUY", "0.01", "50000", post_only=True)
        body = json.loads(mock_post.call_args[1]["data"])
        assert body["order_configuration"]["limit_limit_gtc"]["post_only"] is True

    def test_create_limit_order_gtd_includes_end_time(self):
        end = "2025-12-31T00:00:00Z"
        with patch("coinbase.requests.post", return_value=_ok_response({})) as mock_post:
            self.client.create_limit_order_gtd("BTC-USD", "BUY", "0.01", "50000", end)
        body = json.loads(mock_post.call_args[1]["data"])
        cfg = body["order_configuration"]["limit_limit_gtd"]
        assert cfg["end_time"] == end

    def test_create_stop_limit_gtc_payload(self):
        with patch("coinbase.requests.post", return_value=_ok_response({})) as mock_post:
            self.client.create_stop_limit_order_gtc(
                "BTC-USD", "SELL", "0.1", "45000", "46000",
                "STOP_DIRECTION_STOP_UP",
            )
        body = json.loads(mock_post.call_args[1]["data"])
        cfg = body["order_configuration"]["stop_limit_stop_limit_gtc"]
        assert cfg["stop_price"]     == "46000"
        assert cfg["limit_price"]    == "45000"
        assert cfg["stop_direction"] == "STOP_DIRECTION_STOP_UP"

    def test_create_stop_limit_gtd_includes_end_time(self):
        end = "2025-06-01T00:00:00Z"
        with patch("coinbase.requests.post", return_value=_ok_response({})) as mock_post:
            self.client.create_stop_limit_order_gtd(
                "BTC-USD", "SELL", "0.1", "45000", "46000",
                "STOP_DIRECTION_STOP_DOWN", end,
            )
        body = json.loads(mock_post.call_args[1]["data"])
        cfg = body["order_configuration"]["stop_limit_stop_limit_gtd"]
        assert cfg["end_time"] == end

    def test_cancel_orders_sends_order_ids(self):
        ids = ["id-1", "id-2"]
        with patch("coinbase.requests.post", return_value=_ok_response({"results": []})) as mock_post:
            self.client.cancel_orders(ids)
        body = json.loads(mock_post.call_args[1]["data"])
        assert body["order_ids"] == ids

    def test_cancel_orders_returns_none_on_error(self):
        with patch("coinbase.requests.post", return_value=_error_response(400)):
            result = self.client.cancel_orders(["id-1"])
        assert result is None

    def test_list_orders_returns_list(self):
        mock_data = {"orders": [{"order_id": "o1"}, {"order_id": "o2"}]}
        with patch("coinbase.requests.get", return_value=_ok_response(mock_data)):
            result = self.client.list_orders()
        assert result == mock_data["orders"]

    def test_list_orders_passes_filters(self):
        with patch("coinbase.requests.get", return_value=_ok_response({"orders": []})) as mock_get:
            self.client.list_orders(product_id="BTC-USD", order_status="OPEN", limit=10)
        params = mock_get.call_args[1]["params"]
        assert params["product_id"]   == "BTC-USD"
        assert params["order_status"] == "OPEN"
        assert params["limit"]        == 10

    def test_list_orders_returns_none_on_error(self):
        with patch("coinbase.requests.get", return_value=_error_response(500)):
            result = self.client.list_orders()
        assert result is None

    def test_get_order_returns_order(self):
        mock_data = {"order": {"order_id": "o1", "status": "FILLED"}}
        with patch("coinbase.requests.get", return_value=_ok_response(mock_data)):
            result = self.client.get_order("o1")
        assert result == mock_data["order"]

    def test_get_order_uses_id_in_path(self):
        with patch("coinbase.requests.get", return_value=_ok_response({"order": {}})) as mock_get:
            self.client.get_order("order-xyz")
        url = mock_get.call_args[0][0]
        assert "order-xyz" in url

    def test_get_order_returns_none_on_missing_key(self):
        with patch("coinbase.requests.get", return_value=_ok_response({"error": "NOT_FOUND"})):
            result = self.client.get_order("bad-id")
        assert result is None

    def test_list_fills_returns_list(self):
        mock_data = {"fills": [{"fill_id": "f1"}]}
        with patch("coinbase.requests.get", return_value=_ok_response(mock_data)):
            result = self.client.list_fills(order_id="o1")
        assert result == mock_data["fills"]

    def test_list_fills_returns_none_on_error(self):
        with patch("coinbase.requests.get", return_value=_error_response(500)):
            result = self.client.list_fills()
        assert result is None

    def test_list_fills_passes_filters(self):
        with patch("coinbase.requests.get", return_value=_ok_response({"fills": []})) as mock_get:
            self.client.list_fills(order_id="o1", product_id="BTC-USD", limit=5)
        params = mock_get.call_args[1]["params"]
        assert params["order_id"]   == "o1"
        assert params["product_id"] == "BTC-USD"
        assert params["limit"]      == 5


# ── Portfolios ────────────────────────────────────────────────────────────────

class TestPortfolios(_ClientBase):
    def test_list_portfolios_returns_list(self):
        mock_data = {"portfolios": [{"uuid": "p1", "name": "default"}]}
        with patch("coinbase.requests.get", return_value=_ok_response(mock_data)):
            result = self.client.list_portfolios()
        assert result == mock_data["portfolios"]

    def test_list_portfolios_returns_none_on_error(self):
        with patch("coinbase.requests.get", return_value=_error_response(500)):
            result = self.client.list_portfolios()
        assert result is None

    def test_list_portfolios_passes_type(self):
        with patch("coinbase.requests.get", return_value=_ok_response({"portfolios": []})) as mock_get:
            self.client.list_portfolios(portfolio_type="DEFAULT")
        params = mock_get.call_args[1]["params"]
        assert params["portfolio_type"] == "DEFAULT"

    def test_create_portfolio_returns_portfolio(self):
        mock_data = {"portfolio": {"uuid": "p2", "name": "my-port"}}
        with patch("coinbase.requests.post", return_value=_ok_response(mock_data)):
            result = self.client.create_portfolio("my-port")
        assert result == mock_data["portfolio"]

    def test_create_portfolio_sends_name(self):
        with patch("coinbase.requests.post", return_value=_ok_response({"portfolio": {}})) as mock_post:
            self.client.create_portfolio("alpha")
        body = json.loads(mock_post.call_args[1]["data"])
        assert body["name"] == "alpha"

    def test_create_portfolio_returns_none_on_error(self):
        with patch("coinbase.requests.post", return_value=_error_response(400)):
            result = self.client.create_portfolio("dup")
        assert result is None

    def test_get_portfolio_returns_breakdown(self):
        mock_data = {"breakdown": {"portfolio": {"uuid": "p1"}, "spot_positions": []}}
        with patch("coinbase.requests.get", return_value=_ok_response(mock_data)):
            result = self.client.get_portfolio("p1")
        assert result == mock_data["breakdown"]

    def test_get_portfolio_uses_uuid_in_path(self):
        with patch("coinbase.requests.get", return_value=_ok_response({"breakdown": {}})) as mock_get:
            self.client.get_portfolio("uuid-p1")
        url = mock_get.call_args[0][0]
        assert "uuid-p1" in url

    def test_edit_portfolio_returns_portfolio(self):
        mock_data = {"portfolio": {"uuid": "p1", "name": "renamed"}}
        with patch("coinbase.requests.put", return_value=_ok_response(mock_data)):
            result = self.client.edit_portfolio("p1", "renamed")
        assert result == mock_data["portfolio"]

    def test_edit_portfolio_sends_name(self):
        with patch("coinbase.requests.put", return_value=_ok_response({"portfolio": {}})) as mock_put:
            self.client.edit_portfolio("p1", "new-name")
        body = json.loads(mock_put.call_args[1]["data"])
        assert body["name"] == "new-name"

    def test_edit_portfolio_returns_none_on_error(self):
        with patch("coinbase.requests.put", return_value=_error_response(404)):
            result = self.client.edit_portfolio("bad-uuid", "name")
        assert result is None

    def test_delete_portfolio_returns_dict(self):
        with patch("coinbase.requests.delete", return_value=_ok_response({})):
            result = self.client.delete_portfolio("p1")
        assert result == {}

    def test_delete_portfolio_uses_uuid_in_path(self):
        with patch("coinbase.requests.delete", return_value=_ok_response({})) as mock_del:
            self.client.delete_portfolio("del-uuid")
        url = mock_del.call_args[0][0]
        assert "del-uuid" in url

    def test_delete_portfolio_returns_none_on_error(self):
        with patch("coinbase.requests.delete", return_value=_error_response(400)):
            result = self.client.delete_portfolio("p1")
        assert result is None

    def test_move_portfolio_funds_payload(self):
        with patch("coinbase.requests.post", return_value=_ok_response({})) as mock_post:
            self.client.move_portfolio_funds("100", "USD", "src-uuid", "dst-uuid")
        body = json.loads(mock_post.call_args[1]["data"])
        assert body["funds"]["value"]          == "100"
        assert body["funds"]["currency"]       == "USD"
        assert body["source_portfolio_uuid"]   == "src-uuid"
        assert body["target_portfolio_uuid"]   == "dst-uuid"

    def test_move_portfolio_funds_returns_none_on_error(self):
        with patch("coinbase.requests.post", return_value=_error_response(400)):
            result = self.client.move_portfolio_funds("100", "USD", "a", "b")
        assert result is None


# ── Fees ──────────────────────────────────────────────────────────────────────

class TestFees(_ClientBase):
    def test_get_transaction_summary_returns_dict(self):
        mock_data = {"total_volume": "1000000", "fee_tier": {"maker_fee_rate": "0.001"}}
        with patch("coinbase.requests.get", return_value=_ok_response(mock_data)):
            result = self.client.get_transaction_summary()
        assert result == mock_data

    def test_get_transaction_summary_returns_none_on_error(self):
        with patch("coinbase.requests.get", return_value=_error_response(401)):
            result = self.client.get_transaction_summary()
        assert result is None

    def test_get_transaction_summary_passes_product_type(self):
        with patch("coinbase.requests.get", return_value=_ok_response({})) as mock_get:
            self.client.get_transaction_summary(product_type="SPOT")
        params = mock_get.call_args[1]["params"]
        assert params["product_type"] == "SPOT"


# ── Conversions ───────────────────────────────────────────────────────────────

class TestConversions(_ClientBase):
    def test_create_convert_quote_payload(self):
        with patch("coinbase.requests.post", return_value=_ok_response({"trade": {}})) as mock_post:
            self.client.create_convert_quote("acc-usd", "acc-btc", "500")
        body = json.loads(mock_post.call_args[1]["data"])
        assert body["from_account"] == "acc-usd"
        assert body["to_account"]   == "acc-btc"
        assert body["amount"]       == "500"

    def test_create_convert_quote_returns_dict(self):
        mock_data = {"trade": {"id": "t1", "status": "CREATED"}}
        with patch("coinbase.requests.post", return_value=_ok_response(mock_data)):
            result = self.client.create_convert_quote("a", "b", "10")
        assert result == mock_data

    def test_create_convert_quote_returns_none_on_error(self):
        with patch("coinbase.requests.post", return_value=_error_response(400)):
            result = self.client.create_convert_quote("a", "b", "0")
        assert result is None

    def test_get_convert_trade_returns_dict(self):
        mock_data = {"trade": {"id": "t1", "status": "FILLED"}}
        with patch("coinbase.requests.get", return_value=_ok_response(mock_data)):
            result = self.client.get_convert_trade("t1", "acc-usd", "acc-btc")
        assert result == mock_data

    def test_get_convert_trade_uses_trade_id_in_path(self):
        with patch("coinbase.requests.get", return_value=_ok_response({})) as mock_get:
            self.client.get_convert_trade("trade-xyz", "a", "b")
        url = mock_get.call_args[0][0]
        assert "trade-xyz" in url

    def test_get_convert_trade_returns_none_on_error(self):
        with patch("coinbase.requests.get", return_value=_error_response(404)):
            result = self.client.get_convert_trade("bad-id", "a", "b")
        assert result is None

    def test_commit_convert_trade_payload(self):
        with patch("coinbase.requests.post", return_value=_ok_response({})) as mock_post:
            self.client.commit_convert_trade("t1", "acc-usd", "acc-btc")
        body = json.loads(mock_post.call_args[1]["data"])
        assert body["from_account"] == "acc-usd"
        assert body["to_account"]   == "acc-btc"

    def test_commit_convert_trade_uses_trade_id_in_path(self):
        with patch("coinbase.requests.post", return_value=_ok_response({})) as mock_post:
            self.client.commit_convert_trade("t99", "a", "b")
        url = mock_post.call_args[0][0]
        assert "t99" in url

    def test_commit_convert_trade_returns_none_on_error(self):
        with patch("coinbase.requests.post", return_value=_error_response(400)):
            result = self.client.commit_convert_trade("t1", "a", "b")
        assert result is None


# ── Payment Methods ───────────────────────────────────────────────────────────

class TestPaymentMethods(_ClientBase):
    def test_list_payment_methods_returns_list(self):
        mock_data = {"payment_methods": [{"id": "pm-1", "type": "ACH"}]}
        with patch("coinbase.requests.get", return_value=_ok_response(mock_data)):
            result = self.client.list_payment_methods()
        assert result == mock_data["payment_methods"]

    def test_list_payment_methods_returns_none_on_error(self):
        with patch("coinbase.requests.get", return_value=_error_response(401)):
            result = self.client.list_payment_methods()
        assert result is None

    def test_list_payment_methods_returns_none_on_missing_key(self):
        with patch("coinbase.requests.get", return_value=_ok_response({"error": "NO_AUTH"})):
            result = self.client.list_payment_methods()
        assert result is None

    def test_get_payment_method_returns_method(self):
        mock_data = {"payment_method": {"id": "pm-1", "type": "ACH"}}
        with patch("coinbase.requests.get", return_value=_ok_response(mock_data)):
            result = self.client.get_payment_method("pm-1")
        assert result == mock_data["payment_method"]

    def test_get_payment_method_uses_id_in_path(self):
        with patch("coinbase.requests.get", return_value=_ok_response({"payment_method": {}})) as mock_get:
            self.client.get_payment_method("pm-abc")
        url = mock_get.call_args[0][0]
        assert "pm-abc" in url

    def test_get_payment_method_returns_none_on_error(self):
        with patch("coinbase.requests.get", return_value=_error_response(404)):
            result = self.client.get_payment_method("bad-id")
        assert result is None
