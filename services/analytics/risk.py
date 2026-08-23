"""Deterministic, explainable portfolio risk scoring for the read-only MVP."""
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class RiskInputs:
    concentration: float  # 0..1, higher is worse
    volatility: float  # 0..1, higher is worse
    liquidity_risk: float  # 0..1, higher is worse
    stablecoin_share: float  # 0..1, higher reduces risk


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def score_portfolio(inputs: RiskInputs) -> dict:
    """Return a 0..100 risk score plus explainable components.

    Higher score means higher portfolio risk. This is an analytics score,
    not investment advice or a prediction of future returns.
    """
    concentration = _clamp(inputs.concentration)
    volatility = _clamp(inputs.volatility)
    liquidity = _clamp(inputs.liquidity_risk)
    stablecoin = _clamp(inputs.stablecoin_share)

    raw = (
        concentration * 0.35
        + volatility * 0.30
        + liquidity * 0.25
        + (1.0 - stablecoin) * 0.10
    )
    score = round(raw * 100, 2)
    return {
        "score": score,
        "band": "low" if score < 33 else "moderate" if score < 66 else "high",
        "components": {
            "concentration": round(concentration * 35, 2),
            "volatility": round(volatility * 30, 2),
            "liquidity": round(liquidity * 25, 2),
            "non_stable_exposure": round((1.0 - stablecoin) * 10, 2),
        },
        "inputs": asdict(inputs),
    }
