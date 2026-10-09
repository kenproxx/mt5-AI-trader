"""Manual read-only diagnostic. Run only on an MT5 DEMO terminal."""
import argparse
import json
from decimal import Decimal

from app.broker.adapter import MT5Adapter
from app.validation.demo_diagnostic import run_demo_diagnostic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--side", choices=("BUY", "SELL"), required=True)
    parser.add_argument("--stop", type=Decimal, required=True)
    parser.add_argument("--costs-usd", type=Decimal, default=Decimal("0"))
    args = parser.parse_args()
    adapter = MT5Adapter()
    try:
        result = run_demo_diagnostic(
            adapter, side=args.side, stop=args.stop,
            costs_usd=args.costs_usd,
        )
        print(json.dumps(result.public_dict(), sort_keys=True))
    finally:
        adapter.shutdown()


if __name__ == "__main__":
    main()
