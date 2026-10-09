from decimal import Decimal

from app.broker.compatibility import CompatibilityChecker
from app.broker.mock import MockAdapter
from app.broker.models import BrokerState
from app.validation.demo_feasibility import inspect_minimum_lot


def test_five_dollar_demo_rejects_minimum_lot():
    broker = MockAdapter()
    status = CompatibilityChecker(broker).inspect(now_epoch=broker.tick.time)
    result = inspect_minimum_lot(
        broker, status, side="BUY", stop=Decimal("2999.00"),
    )
    assert result.state == BrokerState.LOT_BELOW_MINIMUM
    assert result.minimum_lot == Decimal("0.01")
    assert result.estimated_minimum_margin_usd > Decimal("5")


def test_bad_stop_rejected():
    broker = MockAdapter()
    status = CompatibilityChecker(broker).inspect(now_epoch=broker.tick.time)
    result = inspect_minimum_lot(
        broker, status, side="BUY", stop=Decimal("3001"),
    )
    assert result.state == BrokerState.NO_TRADE


def test_disconnected_rejected():
    broker = MockAdapter()
    broker.connected = False
    status = CompatibilityChecker(broker).inspect(now_epoch=broker.tick.time)
    result = inspect_minimum_lot(
        broker, status, side="BUY", stop=Decimal("2999"),
    )
    assert result.state == BrokerState.NO_TRADE


def test_non_decimal_inputs_rejected():
    broker = MockAdapter()
    status = CompatibilityChecker(broker).inspect(now_epoch=broker.tick.time)
    result = inspect_minimum_lot(broker, status, side="BUY", stop=2999)
    assert result.state == BrokerState.NO_TRADE
