"""Manual read-only diagnostic. Run only on an MT5 DEMO terminal."""
import argparse
import json
from decimal import Decimal

from app.broker.adapter import MT5Adapter
from app.validation.audit import build_audit
from app.validation.audit_export import export_audit_json
from app.validation.demo_diagnostic import run_demo_diagnostic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--side", choices=("BUY", "SELL"), required=True)
    parser.add_argument("--stop", type=Decimal, required=True)
    parser.add_argument("--costs-usd", type=Decimal, default=Decimal("0"))
    parser.add_argument("--audit-json", help="Create a new sanitized audit JSON file")
    args = parser.parse_args()
    adapter = MT5Adapter()
    try:
        result = run_demo_diagnostic(
            adapter, side=args.side, stop=args.stop,
            costs_usd=args.costs_usd,
        )
        if args.audit_json:
            audit = build_audit(result)
            path = export_audit_json(audit, args.audit_json)
            print(json.dumps({"audit_file": str(path), "state": audit.state}))
        else:
            print(json.dumps(result.public_dict(), sort_keys=True))
    finally:
        adapter.shutdown()


if __name__ == "__main__":
    main()
