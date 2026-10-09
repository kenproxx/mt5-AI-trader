"""Fail-closed read-only health aggregation."""
from dataclasses import dataclass


@dataclass(frozen=True)
class HealthStatus:
    healthy: bool
    reasons: tuple[str, ...]


def assess_health(*, broker_connected, data_fresh, risk_ready, demo_account):
    failed = []
    for name, ok in (
        ("broker_disconnected", broker_connected),
        ("market_data_stale", data_fresh),
        ("risk_engine_unready", risk_ready),
        ("not_demo_account", demo_account),
    ):
        if not ok:
            failed.append(name)
    return HealthStatus(not failed, tuple(failed))
