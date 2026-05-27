"""
Tests for coinbase.py
All HTTP calls are mocked – no real network requests are made.

Run with:  pytest src/python/tests/
"""

import os
import sys
from unittest.mock import MagicMock, patch

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
        # Regardless of exchange, the Coinbase Exchange URL is always used
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

        # sleep should be called between retries (retries-1 times)
        assert len(sleep_calls) == 2
        assert all(v == 1.5 for v in sleep_calls)


# ── CoinbaseAdvancedClient ────────────────────────────────────────────────────

class TestCoinbaseAdvancedClient:
    def setup_method(self):
        self.client = CoinbaseAdvancedClient(api_key="test-key", api_secret="test-secret")

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
