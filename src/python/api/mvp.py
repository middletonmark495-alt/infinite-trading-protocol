"""Read-only MVP FastAPI application.

This module intentionally exposes analytics/health endpoints only. It does
not sign transactions, place trades, transfer funds, or accept private keys.
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from services.analytics.risk import RiskInputs, score_portfolio
from services.alerts.rules import evaluate_portfolio

app = FastAPI(
    title="Infinite Trading Intelligence API",
    version="0.1.0",
    description="Read-only portfolio intelligence API. Financial execution is disabled.",
)


class RiskRequest(BaseModel):
    concentration: float = Field(0.0, ge=0.0, le=1.0)
    volatility: float = Field(0.0, ge=0.0, le=1.0)
    liquidity_risk: float = Field(0.0, ge=0.0, le=1.0)
    stablecoin_share: float = Field(0.0, ge=0.0, le=1.0)


class AlertRequest(BaseModel):
    drawdown_pct: float = 0.0
    risk_score: float = Field(0.0, ge=0.0, le=100.0)


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "Infinite Trading Intelligence API",
        "version": app.version,
        "mode": "read_only",
        "execution_enabled": False,
        "docs": "/docs",
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "mode": "read_only",
        "execution_enabled": False,
    }


@app.get("/system")
def system() -> dict[str, Any]:
    return {
        "api": "online",
        "market_data": "not_configured",
        "blockchain_data": "not_configured",
        "alerts": "enabled",
        "paper_trading": "enabled",
        "live_execution": "locked",
    }


@app.post("/risk/score")
def risk_score(request: RiskRequest) -> dict[str, Any]:
    return score_portfolio(
        RiskInputs(
            concentration=request.concentration,
            volatility=request.volatility,
            liquidity_risk=request.liquidity_risk,
            stablecoin_share=request.stablecoin_share,
        )
    )


@app.post("/alerts/evaluate")
def alerts(request: AlertRequest) -> dict[str, Any]:
    alerts = evaluate_portfolio(request.drawdown_pct, request.risk_score)
    return {"alerts": [alert.__dict__ for alert in alerts]}


@app.get("/execution")
def execution_status() -> dict[str, Any]:
    return {
        "enabled": False,
        "mode": "locked",
        "reason": "Live financial execution is disabled in the MVP.",
    }
