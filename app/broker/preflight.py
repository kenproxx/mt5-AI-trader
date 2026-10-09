"""Read-only MT5 order preflight. Never sends orders."""
from app.broker.models import BrokerState


def order_preflight(adapter, decision, request):
    if not decision.allowed or not request or not request.get("sl"):
        return BrokerState.NO_TRADE
    try:
        result = adapter.order_check(request)
        if result is not None and int(result.retcode) == 0:
            return BrokerState.TRADE_ELIGIBLE
    except (AttributeError, TypeError, ValueError, RuntimeError):
        pass
    return BrokerState.ORDER_REJECTED
