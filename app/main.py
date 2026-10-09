"""Read-only Phase 1 diagnostics; no order_send method is implemented."""
import argparse
from decimal import Decimal

from app.broker.compatibility import CompatibilityChecker
from app.broker.mock import MockAdapter
from app.risk.engine import RiskEngine


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--mock", action="store_true")
    group.add_argument("--real", action="store_true")
    args = parser.parse_args()
    if args.mock:
        adapter = MockAdapter()
    else:
        from app.broker.adapter import MT5Adapter
        adapter = MT5Adapter()
    try:
        status = CompatibilityChecker(adapter).inspect()
        print(f"BROKER: {status.state.value}: {status.reason}")
        if status.account:
            print(f"ACCOUNT: leverage={status.account.leverage} currency={status.account.currency}")
        if status.symbol:
            print(f"SYMBOL: {status.symbol.name} min_lot={status.symbol.volume_min}")
        if status.eligible:
            stop = status.tick.bid - Decimal("1")
            result = RiskEngine(adapter).size_order(
                status, side="BUY", stop=stop, costs_usd=Decimal("0.005")
            )
            print(f"RISK: {result.state.value}: {result.reason}")
        print("Order sending is disabled in Phase 1")
        return 0 if args.mock else (0 if status.eligible else 2)
    finally:
        adapter.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
