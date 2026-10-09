"""Sanitized, non-authorizing audit summary for read-only Demo diagnostics."""
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from app.broker.models import BrokerState

BLOCKED_STATES = {state.value for state in BrokerState}


@dataclass(frozen=True)
class DiagnosticAudit:
    checked_at_utc: str
    mode: str
    state: str
    reason: str
    risk_budget_usd: str | None
    estimated_minimum_margin_usd: str | None
    estimated_minimum_stop_loss_usd: str | None
    minimum_lot: str | None
    can_trade: bool = False

    def public_dict(self):
        return asdict(self)


def build_audit(diagnostic, *, now=None):
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError("UTC-aware timestamp required")
    state = diagnostic.state
    if state not in BLOCKED_STATES:
        state = BrokerState.NO_TRADE.value
    # A read-only report never authorizes execution, even if the estimates pass.
    reason = state if state != BrokerState.NO_TRADE.value else "NO_TRADE"
    def safe_decimal(value):
        if value is None:
            return None
        try:
            parsed = Decimal(value)
        except (InvalidOperation, ValueError, TypeError):
            return None
        if not parsed.is_finite() or parsed < 0:
            return None
        return str(parsed)
    return DiagnosticAudit(
        checked_at_utc=now.astimezone(UTC).isoformat(),
        mode="DEMO" if diagnostic.verified_demo else "UNVERIFIED",
        state=state,
        reason=reason,
        risk_budget_usd=safe_decimal(diagnostic.risk_budget_usd),
        estimated_minimum_margin_usd=safe_decimal(diagnostic.margin_min_lot_usd),
        estimated_minimum_stop_loss_usd=safe_decimal(diagnostic.stop_loss_min_lot_usd),
        minimum_lot=safe_decimal(diagnostic.volume_min),
    )
