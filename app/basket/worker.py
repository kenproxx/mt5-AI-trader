"""Windows VPS entry point. Preview unless --execute AND login are supplied."""
import argparse
import json
import time
from datetime import UTC, datetime

from app.automation.worker import write_status
from app.basket.config import BasketConfig
from app.basket.models import BasketState, Snapshot
from app.basket.planner import plan
from app.basket.risk import check_open


def mock_preview(config):
    from app.broker.compatibility import CompatibilityChecker
    from app.broker.mock import MockAdapter
    broker = MockAdapter()
    status = CompatibilityChecker(broker).inspect(now_epoch=broker.tick.time)
    snap = Snapshot(status, (), '0' * 64, broker.tick.time)
    decision = plan(snap, BasketState(), config, 'BUY')
    blocked = check_open(broker, snap, decision, config)
    return dict(timestamp_utc=datetime.now(UTC).isoformat(), mode='MOCK_PREVIEW',
        can_place_order=False, execution='PREVIEW', broker_state=status.state.value,
        entry_allowed=blocked is None, action=decision.kind,
        action_reason='SYNTHETIC_BUY_FOR_PIPELINE_CHECK', signal='BUY (synthetic)',
        blockers=[blocked] if blocked else [], equity_usd=str(status.account.equity),
        open_positions=0, total_lots='0', basket_pnl_usd='0', basket_phase='IDLE',
        paper_lots=str(decision.lots), paper_stop=str(decision.stop))


def main(argv=None):
    parser = argparse.ArgumentParser(description='XAUUSD basket controller: preview / MT5 execution',
                                     allow_abbrev=False)
    parser.add_argument('--mode', choices=('mock', 'mt5'), default='mock')
    parser.add_argument('--config', help='Optional strict JSON configuration')
    parser.add_argument('--execute', action='store_true', help='Send orders on the selected MT5 account')
    parser.add_argument('--account-login', type=int, help='Pin expected MT5 login; never a password')
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--interval', type=int, default=30)
    parser.add_argument('--state-file', default='data/basket-state.sqlite3')
    parser.add_argument('--status-file', default='data/basket-status.json')
    args = parser.parse_args(argv)
    if not 5 <= args.interval <= 3600:
        parser.error('Interval must be 5..3600 seconds')
    if args.account_login is not None and args.account_login <= 0:
        parser.error('Invalid expected login')
    if args.execute and (args.mode != 'mt5' or args.account_login is None):
        parser.error('Execution requires --mode mt5 and --account-login')
    try:
        config = BasketConfig.load(args.config) if args.config else BasketConfig()
    except (ValueError, OSError, TypeError, ArithmeticError):
        parser.error('Invalid basket configuration')
    gateway = None
    if args.mode == 'mt5':
        from app.basket.gateway import MT5Gateway
        from app.basket.runner import BasketRunner
        try:
            import MetaTrader5 as mt5
        except ImportError:
            parser.error('Install the mt5 extra on Windows with a running MT5 terminal')
        gateway = MT5Gateway(mt5, config, expected_login=args.account_login)
        runner = BasketRunner(gateway, args.state_file, config)
    try:
        while True:
            report = (mock_preview(config) if args.mode == 'mock'
                      else runner.cycle(execute=args.execute))
            write_status(args.status_file, report)
            print(json.dumps(report, ensure_ascii=False, sort_keys=True), flush=True)
            if args.once:
                return 2 if report['execution'] == 'BLOCKED' else 0
            time.sleep(args.interval)
    except KeyboardInterrupt:
        return 0
    finally:
        if gateway:
            gateway.adapter.shutdown()


if __name__ == '__main__':
    raise SystemExit(main())
