from services.alerts.rules import evaluate_portfolio
from services.billing.entitlements import get_entitlements
from services.execution.guard import ExecutionDisabled, assert_execution_allowed


def test_unknown_plan_fails_closed_to_free():
    assert get_entitlements("unknown").max_wallets == 1
    assert not get_entitlements("unknown").api_access


def test_alert_rules():
    alerts = evaluate_portfolio(-12, 85)
    assert {a.kind for a in alerts} == {"drawdown", "risk"}


def test_execution_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("READ_ONLY_MODE", raising=False)
    monkeypatch.delenv("EXECUTION_ENABLED", raising=False)
    try:
        assert_execution_allowed()
    except ExecutionDisabled:
        return
    raise AssertionError("execution must fail closed")
