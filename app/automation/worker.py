"""Windows VPS read-only controller. No MT5 order_send / order_modify / closes."""
import argparse
import hashlib
import json
import os
import tempfile
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.automation.guards import GuardSettings, evaluate_guards, update_periods
from app.automation.scanner import scan_xauusd
from app.automation.state import load_state, save_state
from app.broker.compatibility import CompatibilityChecker
from app.config.policy import TradingPolicy
from app.risk.engine import RiskEngine


def inspect_once(adapter, *, state_file, settings, costs_usd, now=None):
    now = now or datetime.now(UTC)
    status = CompatibilityChecker(adapter).inspect(now_epoch=int(now.timestamp()))
    report = {
        "timestamp_utc": now.astimezone(UTC).isoformat(),
        "mode": "MT5_READ_ONLY",
        "can_place_order": False,
        "broker_state": status.state.value,
        "entry_allowed": False,
        "blockers": [],
        "signal": "HOLD",
        "paper_lots": "0",
        "paper_stop": None,
    }
    if not status.eligible:
        report["blockers"] = ["BROKER_INELIGIBLE"]
        return report
    mt5 = getattr(adapter, "mt5", None)
    if mt5 is None:
        report["blockers"] = ["TERMINAL_REQUIRED"]
        return report
    raw_account = mt5.account_info()
    if (raw_account is None
        or type(getattr(raw_account, "login", None)) is not int
        or raw_account.login <= 0):
        report["blockers"] = ["ACCOUNT_IDENTITY_UNVERIFIED"]
        return report
    positions = mt5.positions_get()  # All symbols: account-wide one-position cap.
    if positions is None:
        report["blockers"] = ["POSITIONS_UNKNOWN"]
        return report

    acct, sym, tick = status.account, status.symbol, status.tick
    fingerprint = hashlib.sha256(
        f"{raw_account.login}|{acct.server}".encode()
    ).hexdigest()
    state = update_periods(
        load_state(state_file), account_fingerprint=fingerprint,
        equity=acct.equity, now=now,
    )
    spread = (tick.ask - tick.bid) / sym.point
    guard = evaluate_guards(
        state, equity=acct.equity, spread_points=spread,
        open_positions=len(positions), now=now,
        broker_eligible=True, settings=settings, policy=TradingPolicy(),
    )
    # Persist latched locks *before* publishing eligible decisions.
    save_state(state_file, guard.state)
    report.update({
        "equity_usd": str(acct.equity),
        "spread_points": str(spread),
        "day_equity_change_pct": str(guard.day_pnl_pct),
        "week_drawdown_pct": str(guard.week_drawdown_pct),
        "open_positions": len(positions),
        "entry_allowed": guard.allowed,
        "blockers": list(guard.reasons),
    })
    if not guard.allowed:
        return report
    try:
        signal, stop = scan_xauusd(mt5, status, now_epoch=int(now.timestamp()))
    except (AttributeError, TypeError, ValueError, RuntimeError, IndexError):
        report["entry_allowed"] = False
        report["blockers"] = ["CANDLE_SCAN_BLOCKED"]
        return report
    report["signal"] = signal.side
    if signal.side not in ("BUY", "SELL") or stop is None:
        report["entry_allowed"] = False
        report["blockers"] = ["NO_ENTRY_SIGNAL"]
        return report
    decision = RiskEngine(adapter).size_order(
        status, side=signal.side, stop=stop, costs_usd=costs_usd,
        open_positions=len(positions),
        daily_loss_usd=guard.day_loss_usd,
        weekly_loss_usd=guard.week_loss_usd,
        daily_start_equity=guard.state.day_start_equity,
        weekly_start_equity=guard.state.week_start_equity,
    )
    report.update({
        "paper_stop": str(stop),
        "paper_lots": str(decision.lots),
        "entry_allowed": decision.allowed,
        "blockers": [] if decision.allowed else [decision.state.value],
        "risk_reason": decision.reason,
    })
    return report


def write_status(path, report):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=".status-", suffix=".tmp", delete=False,
        ) as file:
            temporary = Path(file.name)
            os.chmod(temporary, 0o600)
            json.dump(report, file, ensure_ascii=False, sort_keys=True)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Read-only VTrade-style MT5 watcher")
    parser.add_argument("--mode", choices=("mock", "mt5"), default="mock")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--state-file", default="data/vps-guard-state.json")
    parser.add_argument("--status-file", default="data/vps-status.json")
    parser.add_argument("--max-spread-points", type=Decimal, default=Decimal("50"))
    parser.add_argument("--daily-target-pct", type=Decimal, default=Decimal("0"))
    parser.add_argument("--estimated-costs-usd", type=Decimal, default=Decimal("0.01"))
    args = parser.parse_args()
    if args.interval < 5 or args.estimated_costs_usd < 0 or not (
        args.estimated_costs_usd.is_finite()
    ):
        parser.error("Invalid interval or costs")
    try:
        settings = GuardSettings(
            max_spread_points=args.max_spread_points,
            daily_profit_target_pct=args.daily_target_pct,
        )
    except ValueError as exc:
        parser.error(str(exc))
    if args.mode == "mock":
        from app.broker.mock import MockAdapter
        adapter = MockAdapter()
    else:
        from app.broker.adapter import MT5Adapter
        adapter = MT5Adapter()
    try:
        while True:
            try:
                report = inspect_once(
                    adapter, state_file=args.state_file,
                    settings=settings, costs_usd=args.estimated_costs_usd,
                )
                write_status(args.status_file, report)
                print(json.dumps(report, sort_keys=True), flush=True)
            except (ValueError, OSError, RuntimeError, ArithmeticError):
                # No exception details: errors may contain terminal/account secrets.
                report = {"mode": "MT5_READ_ONLY", "can_place_order": False,
                          "entry_allowed": False, "blockers": ["WORKER_ERROR"]}
                print(json.dumps(report), flush=True)
                # Do not overwrite the previously verified persisted guard state.
                if args.once:
                    return 2
            if args.once:
                return 0
            time.sleep(args.interval)
    except KeyboardInterrupt:
        return 0
    finally:
        adapter.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
