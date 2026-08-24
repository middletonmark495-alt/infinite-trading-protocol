"""Server-side subscription entitlements.

This module intentionally contains no payment credentials or provider-specific API calls.
A billing adapter can map provider events into these plan names.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Entitlements:
    max_wallets: int
    alerts: bool
    realtime: bool
    api_access: bool
    webhooks: bool


PLANS = {
    "free": Entitlements(max_wallets=1, alerts=False, realtime=False, api_access=False, webhooks=False),
    "pro": Entitlements(max_wallets=25, alerts=True, realtime=True, api_access=False, webhooks=False),
    "business": Entitlements(max_wallets=250, alerts=True, realtime=True, api_access=True, webhooks=True),
    "enterprise": Entitlements(max_wallets=10_000, alerts=True, realtime=True, api_access=True, webhooks=True),
}


def get_entitlements(plan: str) -> Entitlements:
    """Return entitlements for a plan; unknown plans fail closed to free."""
    return PLANS.get(plan.lower(), PLANS["free"])
