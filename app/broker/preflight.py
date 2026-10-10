"""Read-only MT5 order preflight. Never sends orders."""
from app.broker.models import BrokerState


def order_preflight(adapter, decision, request):
    if not decision.allowed or not request or not request.get("sl"):
        return BrokerState.NO_TRADE
    # Only the MT5 documented DONE retcode may be accepted.
    try:
        account = adapter.account_info()
        if account is None or type(account.account_trade_mode) is not int or account.account_trade_mode != 0:
            return BrokerState.NO_TRADE
        result = adapter.order_check(request)
        if result is not None and type(result.retcode) is int and result.retcode == 10009:
            return BrokerState.TRADE_ELIGIBLE
    except (AttributeError, TypeError, ValueError, RuntimeError):
        pass
    return BrokerState.ORDER_REJECTED
