"""
Balance Transfer Dashboard — FastAPI backend.

API keys are passed per-request via headers so they are never stored server-side.
Run with: uvicorn main:app --reload --port 8000
"""

import sys
import os
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Expose the existing Coinbase client from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.python.coinbase import CoinbaseAdvancedClient

from services.evm_service import EVMService, CHAINS, TOKENS

app = FastAPI(title="Balance Transfer Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

evm = EVMService()


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── Coinbase ───────────────────────────────────────────────────────────────────

def _cb_client(key: Optional[str], secret: Optional[str]) -> CoinbaseAdvancedClient:
    if not key or not secret:
        raise HTTPException(400, "Coinbase API key and secret are required (pass x-coinbase-key and x-coinbase-secret headers)")
    return CoinbaseAdvancedClient(key, secret)


@app.get("/api/coinbase/accounts")
def cb_accounts(
    x_coinbase_key: Optional[str] = Header(None),
    x_coinbase_secret: Optional[str] = Header(None),
):
    client = _cb_client(x_coinbase_key, x_coinbase_secret)
    accounts = client.list_accounts()
    if accounts is None:
        raise HTTPException(502, "Failed to fetch Coinbase accounts — check your API keys")
    # Filter to non-zero balances for readability, but return all
    return {"accounts": accounts}


@app.get("/api/coinbase/portfolios")
def cb_portfolios(
    x_coinbase_key: Optional[str] = Header(None),
    x_coinbase_secret: Optional[str] = Header(None),
):
    client = _cb_client(x_coinbase_key, x_coinbase_secret)
    portfolios = client.list_portfolios()
    if portfolios is None:
        raise HTTPException(502, "Failed to fetch Coinbase portfolios")
    return {"portfolios": portfolios}


@app.get("/api/coinbase/portfolio/{uuid}")
def cb_portfolio_detail(
    uuid: str,
    x_coinbase_key: Optional[str] = Header(None),
    x_coinbase_secret: Optional[str] = Header(None),
):
    client = _cb_client(x_coinbase_key, x_coinbase_secret)
    detail = client.get_portfolio(uuid)
    if detail is None:
        raise HTTPException(502, "Failed to fetch portfolio detail")
    return detail


@app.get("/api/coinbase/payment-methods")
def cb_payment_methods(
    x_coinbase_key: Optional[str] = Header(None),
    x_coinbase_secret: Optional[str] = Header(None),
):
    client = _cb_client(x_coinbase_key, x_coinbase_secret)
    methods = client.list_payment_methods()
    if methods is None:
        raise HTTPException(502, "Failed to fetch payment methods")
    return {"payment_methods": methods}


class PortfolioMoveRequest(BaseModel):
    funds: str
    currency: str
    source_portfolio_uuid: str
    target_portfolio_uuid: str


@app.post("/api/coinbase/portfolio/move")
def cb_portfolio_move(
    req: PortfolioMoveRequest,
    x_coinbase_key: Optional[str] = Header(None),
    x_coinbase_secret: Optional[str] = Header(None),
):
    client = _cb_client(x_coinbase_key, x_coinbase_secret)
    result = client.move_portfolio_funds(req.funds, req.currency, req.source_portfolio_uuid, req.target_portfolio_uuid)
    if result is None:
        raise HTTPException(502, "Portfolio move failed — check balances and UUIDs")
    return result


class ConvertRequest(BaseModel):
    from_account: str
    to_account: str
    amount: str


@app.post("/api/coinbase/convert/quote")
def cb_convert_quote(
    req: ConvertRequest,
    x_coinbase_key: Optional[str] = Header(None),
    x_coinbase_secret: Optional[str] = Header(None),
):
    client = _cb_client(x_coinbase_key, x_coinbase_secret)
    result = client.create_convert_quote(req.from_account, req.to_account, req.amount)
    if result is None:
        raise HTTPException(502, "Failed to create conversion quote")
    return result


class CommitConvertRequest(BaseModel):
    trade_id: str
    from_account: str
    to_account: str


@app.post("/api/coinbase/convert/commit")
def cb_convert_commit(
    req: CommitConvertRequest,
    x_coinbase_key: Optional[str] = Header(None),
    x_coinbase_secret: Optional[str] = Header(None),
):
    client = _cb_client(x_coinbase_key, x_coinbase_secret)
    result = client.commit_convert_trade(req.trade_id, req.from_account, req.to_account)
    if result is None:
        raise HTTPException(502, "Failed to commit conversion")
    return result


@app.get("/api/coinbase/orders")
def cb_orders(
    limit: int = 25,
    x_coinbase_key: Optional[str] = Header(None),
    x_coinbase_secret: Optional[str] = Header(None),
):
    client = _cb_client(x_coinbase_key, x_coinbase_secret)
    orders = client.list_orders(limit=limit)
    if orders is None:
        raise HTTPException(502, "Failed to fetch orders")
    return {"orders": orders}


# ── EVM ────────────────────────────────────────────────────────────────────────

@app.get("/api/evm/chains")
def evm_chains():
    return {"chains": EVMService.list_chains()}


@app.get("/api/evm/balance")
def evm_balance(
    address: str,
    network: str = "ethereum",
    x_rpc_url: Optional[str] = Header(None),
):
    try:
        native = evm.get_native_balance(address, network, x_rpc_url or None)
        tokens = evm.get_token_balances(address, network, x_rpc_url or None)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"RPC error: {e}")
    return {"network": network, "address": address, "native": native, "tokens": tokens}


class EVMTransferRequest(BaseModel):
    from_address: str
    to_address: str
    amount: str
    network: str = "ethereum"
    private_key: str
    rpc_url: Optional[str] = None
    # For ERC20 transfers
    token_address: Optional[str] = None
    token_decimals: Optional[int] = None


@app.post("/api/evm/transfer")
def evm_transfer(req: EVMTransferRequest):
    try:
        if req.token_address and req.token_decimals is not None:
            tx_hash = evm.send_token(
                req.from_address, req.to_address, req.token_address,
                req.amount, req.token_decimals, req.network, req.private_key, req.rpc_url,
            )
        else:
            tx_hash = evm.send_eth(
                req.from_address, req.to_address, req.amount,
                req.network, req.private_key, req.rpc_url,
            )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"Transfer failed: {e}")
    chain = CHAINS.get(req.network, {})
    return {"tx_hash": tx_hash, "network": req.network, "chain_id": chain.get("chain_id")}
