"""Deterministic alert rules for the read-only MVP."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Alert:
    kind: str
    message: str
    severity: str


def evaluate_portfolio(drawdown_pct: float, risk_score: float) -> list[Alert]:
    alerts: list[Alert] = []
    if drawdown_pct <= -10:
        alerts.append(Alert("drawdown", f"Portfolio drawdown is {drawdown_pct:.2f}%", "high"))
    elif drawdown_pct <= -5:
        alerts.append(Alert("drawdown", f"Portfolio drawdown is {drawdown_pct:.2f}%", "medium"))
    if risk_score >= 80:
        alerts.append(Alert("risk", f"Portfolio risk score is {risk_score:.1f}/100", "high"))
    elif risk_score >= 65:
        alerts.append(Alert("risk", f"Portfolio risk score is {risk_score:.1f}/100", "medium"))
    return alerts
