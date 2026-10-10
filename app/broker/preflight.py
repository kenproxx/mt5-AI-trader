"""Read-only MT5 order preflight. Never sends orders."""
from app.broker.models import BrokerState


def order_preflight(adapter, decision, request):
    if not decision.allowed or not request or not request.get("sl"):
        return BrokerState.NO_TRADE
    # Only the MT5 documented DONE retcode may be accepted.
    if getattr(adapter, "account_info", None) is None:
        return BrokerState.NO_TRADE
    try:
        result = adapter.order_check(request)
        if result is not None and type(result.retcode) is int and result.retcode == 10009:
            return BrokerState.TRADE_ELIGIBLE
    except (AttributeError, TypeError, ValueError, RuntimeError):
        pass
    return BrokerState.ORDER_REJECTED
