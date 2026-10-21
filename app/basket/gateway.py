"""Write-capable boundary for an explicitly selected MT5 hedging account."""
import hashlib
import time
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

from app.basket.models import Position, Snapshot
from app.broker.adapter import MT5Adapter, dec
from app.broker.compatibility import CompatibilityChecker

D = Decimal


class Blocked(ValueError):
    """Sanitized machine-readable reason; never include terminal secrets."""


class NotSent(Blocked):
    """Validation failed before order_send was called; intent can be cleared."""


def position_structure(snapshot):
    # Floating profit changes with quotes; ownership/size/protection must not.
    return tuple((p.ticket, p.side, p.lots, p.entry, p.stop, p.role)
                 for p in snapshot.positions)


class MT5Gateway:
    def __init__(self, mt5, config, *, expected_login=None, clock=None):
        self.mt5, self.config = mt5, config
        self.adapter = MT5Adapter(mt5)
        self.expected_login = expected_login
        self.clock = clock or time.time

    def snapshot(self, now, roles=None):
        status = CompatibilityChecker(self.adapter).inspect(now_epoch=now)
        if not status.eligible:
            raise Blocked(status.state.value)
        raw = self.mt5.account_info()
        terminal = self.mt5.terminal_info()
        if (raw is None or type(raw.login) is not int or raw.login <= 0
            or type(raw.margin_mode) is not int or raw.margin_mode != 2
            or raw.hedge_allowed is not True or raw.fifo_close is not False
            or raw.leverage != 50 or raw.currency != 'USD'
            or raw.trade_allowed is not True or raw.trade_expert is not True):
            raise Blocked('HEDGING_ACCOUNT_REQUIRED')
        if self.expected_login is not None and raw.login != self.expected_login:
            raise Blocked('ACCOUNT_LOGIN_MISMATCH')
        if (terminal is None or terminal.connected is not True
            or terminal.trade_allowed is not True or terminal.tradeapi_disabled is not False):
            raise Blocked('TERMINAL_TRADING_DISABLED')
        orders = self.mt5.orders_get()
        if orders is None or len(orders):
            raise Blocked('PENDING_ORDERS_PRESENT_OR_UNKNOWN')
        positions = self.mt5.positions_get()
        if positions is None:
            raise Blocked('POSITIONS_UNKNOWN')
        parsed = []
        for p in positions:
            if p.magic != self.config.magic or p.symbol != 'XAUUSD':
                raise Blocked('FOREIGN_POSITION')
            if type(p.ticket) is not int or p.ticket <= 0 or type(p.type) is not int or p.type not in (0, 1):
                raise Blocked('INVALID_POSITION')
            position = Position(p.ticket, 'BUY' if p.type == 0 else 'SELL', dec(p.volume),
                dec(p.price_open), dec(p.sl), dec(p.profit) + dec(p.swap),
                (roles or {}).get(str(p.ticket), 'unknown'))
            if (position.lots <= 0 or position.entry <= 0 or position.stop < 0
                or position.lots % status.symbol.volume_step):
                raise Blocked('INVALID_POSITION')
            parsed.append(position)
        if len({p.ticket for p in parsed}) != len(parsed):
            raise Blocked('DUPLICATE_POSITION')
        # The raw account and normalized account must be the same read context.
        if str(raw.server) != status.account.server:
            raise Blocked('ACCOUNT_SNAPSHOT_CHANGED')
        account = replace(status.account, equity=dec(raw.equity), balance=dec(raw.balance),
                          free_margin=dec(raw.margin_free), margin=dec(raw.margin))
        if account.equity <= 0 or account.balance <= 0 or account.free_margin < 0 or account.margin < 0:
            raise Blocked('ACCOUNT_FUNDS_INVALID')
        status = replace(status, account=account)
        identity = hashlib.sha256(f'{raw.login}|{raw.server}'.encode()).hexdigest()
        return Snapshot(status, tuple(sorted(parsed, key=lambda p: p.ticket)), identity, now)

    def cashflow_since(self, start, now):
        history = self.mt5.history_deals_get(datetime.fromtimestamp(start, UTC),
                                           datetime.fromtimestamp(now, UTC))
        if history is None:
            raise Blocked('HISTORY_UNAVAILABLE')
        return any(d.type not in (0, 1) and d.time >= start for d in history)

    def prepare(self, snapshot, decision, *, ticket=None):
        if type(self.expected_login) is not int or self.expected_login <= 0:
            raise Blocked('EXPLICIT_ACCOUNT_LOGIN_REQUIRED')
        fresh = self.snapshot(int(self.clock()), {str(p.ticket): p.role for p in snapshot.positions})
        if fresh.identity != snapshot.identity or position_structure(fresh) != position_structure(snapshot):
            raise Blocked('POSITION_OR_ACCOUNT_CHANGED')
        s, t = fresh.status.symbol, fresh.status.tick
        side, lots = decision.side, decision.lots
        if ticket is not None:
            p = next((p for p in fresh.positions if p.ticket == ticket), None)
            if p is None:
                raise Blocked('CLOSE_TICKET_MISSING')
            side, lots = ('SELL' if p.side == 'BUY' else 'BUY'), p.lots
        # FOK preferred. IOC only when advertised; partial fills are latched for review.
        if s.filling_mode & 1:
            filling = self.mt5.ORDER_FILLING_FOK
        elif s.filling_mode & 2:
            filling = self.mt5.ORDER_FILLING_IOC
        else:
            raise Blocked('UNSUPPORTED_FILLING_MODE')
        request = dict(action=self.mt5.TRADE_ACTION_DEAL, symbol='XAUUSD',
            volume=float(lots), type=self.mt5.ORDER_TYPE_BUY if side == 'BUY' else self.mt5.ORDER_TYPE_SELL,
            price=float(t.ask if side == 'BUY' else t.bid),
            deviation=self.config.deviation_points, magic=self.config.magic,
            comment='basket:' + decision.kind.lower(), type_time=self.mt5.ORDER_TIME_GTC,
            type_filling=filling)
        if ticket is not None:
            request['position'] = ticket
        else:
            request['sl'] = float(decision.stop)
        check = self.mt5.order_check(request)
        if check is None or type(check.retcode) is not int or check.retcode != 0:
            raise Blocked('ORDER_CHECK_REJECTED')
        equity, margin, free = dec(check.equity), dec(check.margin), dec(check.margin_free)
        if equity <= 0 or margin < 0:
            raise Blocked('ORDER_CHECK_INVALID')
        # Opening and hedge removal must both retain sufficient margin. A close
        # which improves free margin is permitted while already below the reserve.
        improves = ticket is not None and free >= fresh.status.account.free_margin
        if not improves and (free < equity * D('.3') or
                margin > 0 and equity * 100 / margin < self.config.min_margin_level_pct):
            raise Blocked('ORDER_CHECK_MARGIN_RESERVE')
        return request, fresh

    def send_verified(self, request, before, validate):
        """Caller MUST durably journal the intent before entering this method."""
        # Last identity/position check after order_check, with no permissive fallback.
        try:
            latest = self.snapshot(int(self.clock()), {str(p.ticket): p.role for p in before.positions})
            if latest.identity != before.identity or position_structure(latest) != position_structure(before):
                raise Blocked('PRE_SEND_SNAPSHOT_CHANGED')
            validate(latest)
        except (ValueError, TypeError, AttributeError, RuntimeError, ArithmeticError) as exc:
            raise NotSent(str(exc) if isinstance(exc, Blocked) else 'PRE_SEND_VALIDATION') from exc
        result = self.mt5.order_send(request)
        if (result is None or type(result.retcode) is not int or result.retcode != 10009
            or dec(result.volume) != dec(request['volume'])
            or type(result.order) is not int or result.order <= 0
            or type(result.deal) is not int or result.deal <= 0
            or dec(result.price) <= 0):
            raise Blocked('EXECUTION_UNCERTAIN')
        after = self.snapshot(int(self.clock()), {str(p.ticket): p.role for p in before.positions})
        if after.identity != before.identity:
            raise Blocked('POST_SEND_ACCOUNT_CHANGED')
        prior_ids = {p.ticket for p in before.positions}
        if 'position' in request:
            if {p.ticket for p in after.positions} != prior_ids - {request['position']}:
                raise Blocked('CLOSE_NOT_RECONCILED')
            deals = self.mt5.history_deals_get(ticket=result.order)
            if not deals or any(d.entry != 1 or d.order != result.order or
                                d.symbol != 'XAUUSD' or d.magic != self.config.magic for d in deals):
                raise Blocked('CLOSE_HISTORY_UNVERIFIED')
            if sum((dec(d.volume) for d in deals), D('0')) != dec(request['volume']):
                raise Blocked('CLOSE_HISTORY_VOLUME')
            realized = sum((dec(d.profit) + dec(d.swap) + dec(d.commission) + dec(d.fee)
                            for d in deals), D('0'))
            return after, None, realized
        added = [p for p in after.positions if p.ticket not in prior_ids]
        if len(added) != 1 or len(after.positions) != len(before.positions) + 1:
            raise Blocked('OPEN_NOT_RECONCILED')
        p = added[0]
        expected_side = 'BUY' if request['type'] == self.mt5.ORDER_TYPE_BUY else 'SELL'
        if p.side != expected_side or p.lots != dec(request['volume']) or p.stop != dec(request['sl']):
            raise Blocked('OPEN_PROTECTION_UNVERIFIED')
        return after, replace(p, role='hedge' if request['comment'] == 'basket:hedge' else 'primary'), D('0')
