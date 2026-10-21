"""One durable basket decision per cycle. No retries for ambiguous broker writes."""
import hashlib
import sqlite3
import tempfile
from dataclasses import asdict, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from app.automation.guards import GuardSettings, GuardState, evaluate_guards, update_periods
from app.automation.scanner import scan_xauusd
from app.basket.gateway import Blocked, NotSent
from app.basket.journal import FileLock, Journal
from app.basket.models import BasketState
from app.basket.planner import cost, plan
from app.basket.risk import check_open
from app.config.policy import TradingPolicy

D = Decimal


def decode_state(raw):
    if not isinstance(raw, dict) or set(raw) != set(BasketState.__dataclass_fields__):
        raise Blocked('STATE_SCHEMA_INVALID')
    raw = dict(raw)
    raw['anchor'] = D(raw['anchor'])
    if not raw['anchor'].is_finite() or raw['anchor'] < 0:
        raise Blocked('STATE_ANCHOR_INVALID')
    for key in ('dca_before', 'dca_after', 'hedge_count', 'pyramid_count', 'last_action'):
        if type(raw[key]) is not int or raw[key] < 0:
            raise Blocked('STATE_COUNTER_INVALID')
    for key in ('hedged', 'exiting'):
        if type(raw[key]) is not bool:
            raise Blocked('STATE_FLAG_INVALID')
    if raw['side'] not in (None, 'BUY', 'SELL') or (raw['side'] and raw['anchor'] <= 0):
        raise Blocked('STATE_SIDE_INVALID')
    if not isinstance(raw['tickets'], dict) or any(
        not key.isdecimal() or int(key) <= 0 or role not in ('primary', 'hedge')
        for key, role in raw['tickets'].items()
    ):
        raise Blocked('STATE_TICKETS_INVALID')
    return BasketState(**raw)


def decode_guard(raw):
    if raw is None:
        return None
    if not isinstance(raw, dict) or set(raw) != set(GuardState.__dataclass_fields__):
        raise Blocked('GUARD_SCHEMA_INVALID')
    raw = dict(raw)
    for key in ('day_start_equity', 'week_start_equity', 'week_peak_equity'):
        raw[key] = D(raw[key])
    for key in ('day_locked', 'week_locked'):
        if type(raw[key]) is not bool:
            raise Blocked('GUARD_FLAG_INVALID')
    return GuardState(**raw)


class BasketRunner:
    def __init__(self, gateway, path, config):
        self.gateway, self.path, self.config = gateway, Path(path), config

    def cycle(self, *, now=None, signal=None, execute=False):
        now = now if now is not None else int(datetime.now(UTC).timestamp())
        report = dict(timestamp_utc=datetime.fromtimestamp(now, UTC).isoformat(),
            mode='DEMO_EXECUTION' if execute else 'DEMO_PREVIEW',
            can_place_order=False, entry_allowed=False, blockers=[], action='HOLD',
            execution='BLOCKED', broker_state='NO_TRADE', signal=signal or 'HOLD')
        try:
            # All copies for the pinned login share this OS lock, even with different journals.
            key = hashlib.sha256(str(self.gateway.expected_login).encode()).hexdigest()
            lock_path = Path(tempfile.gettempdir()) / f'mt5-basket-{key}.lock'
            with FileLock(lock_path), Journal(self.path) as journal:
                data = journal.load()
                state = decode_state(data['state']) if data else BasketState()
                snap = self.gateway.snapshot(now, state.tickets)
                if data is None:
                    if snap.positions:
                        raise Blocked('ORPHAN_BASKET_REVIEW')
                    data = dict(schema=1, identity=snap.identity, config=self.config.fingerprint,
                                created=now, last_seen=now, pending=None, guard=None,
                                state=asdict(state))
                if (data['schema'] != 1 or data['identity'] != snap.identity
                    or data['config'] != self.config.fingerprint
                    or type(data['created']) is not int or data['created'] > now
                    or type(data['last_seen']) is not int or data['last_seen'] > now):
                    raise Blocked('JOURNAL_IDENTITY_CONFIG_OR_CLOCK')
                if data['pending'] is not None:
                    raise Blocked('PENDING_EXECUTION_REVIEW')
                if any(str(p.ticket) not in state.tickets for p in snap.positions):
                    raise Blocked('UNRECOGNIZED_BOT_POSITION')
                if not snap.positions:
                    state = BasketState(last_action=state.last_action)
                elif state.side is None:
                    raise Blocked('STATE_SIDE_UNKNOWN')
                if any((p.role == 'primary') != (p.side == state.side) for p in snap.positions):
                    raise Blocked('POSITION_ROLE_MISMATCH')
                stamp = datetime.fromtimestamp(now, UTC)
                guard_state = update_periods(decode_guard(data['guard']),
                    account_fingerprint=snap.identity, equity=snap.status.account.equity, now=stamp)
                guard = evaluate_guards(guard_state, equity=snap.status.account.equity,
                    spread_points=(snap.status.tick.ask - snap.status.tick.bid) / snap.status.symbol.point,
                    open_positions=len(snap.positions), now=stamp, broker_eligible=True,
                    settings=GuardSettings(max_spread_points=self.config.max_spread_points),
                    policy=TradingPolicy(max_open_positions=self.config.max_positions))
                if snap.positions and (guard.state.day_locked or guard.state.week_locked):
                    state.exiting = True
                data.update(guard=asdict(guard.state), state=asdict(state), last_seen=now)
                journal.save(data)
                if signal is None:
                    try:
                        signal = scan_xauusd(self.gateway.mt5, snap.status, now_epoch=now)[0].side
                    except (ValueError, RuntimeError, TypeError, AttributeError, IndexError):
                        signal = 'HOLD'
                decision = plan(snap, state, self.config, signal)
                report.update(broker_state=snap.status.state.value, signal=signal,
                    equity_usd=str(snap.status.account.equity),
                    spread_points=str((snap.status.tick.ask - snap.status.tick.bid) / snap.status.symbol.point),
                    day_equity_change_pct=str(guard.day_pnl_pct), week_drawdown_pct=str(guard.week_drawdown_pct),
                    open_positions=len(snap.positions), total_lots=str(sum((p.lots for p in snap.positions), D('0'))),
                    basket_pnl_usd=str(sum((p.pnl for p in snap.positions), D('0'))),
                    basket_phase='HEDGED' if state.hedged else ('ACTIVE' if snap.positions else 'IDLE'),
                    layers=f'DCA {state.dca_before}/{state.dca_after} · Hedge {state.hedge_count} · Pyramid {state.pyramid_count}',
                    action=decision.kind, action_reason=decision.reason,
                    paper_lots=str(decision.lots), paper_stop=str(decision.stop) if decision.stop else None)
                if decision.opens_position:
                    if not guard.allowed:
                        report['blockers'] = list(guard.reasons)
                        return report
                    if self.gateway.cashflow_since(data['created'], now):
                        raise Blocked('CASHFLOW_REVIEW')
                    remaining = min(guard.state.day_start_equity * D('.02') - guard.day_loss_usd,
                                    guard.state.week_start_equity * D('.05') - guard.week_loss_usd)
                    blocked = check_open(self.gateway.adapter, snap, decision, self.config,
                                         remaining_budget=remaining)
                    if blocked:
                        raise Blocked(blocked)
                report['entry_allowed'] = decision.opens_position
                if decision.kind == 'HOLD' or not execute:
                    report['execution'] = 'PREVIEW' if not execute else 'IDLE'
                    return report
                if decision.kind == 'EXIT':
                    state.exiting = True
                    data['state'] = asdict(state)
                    journal.save(data)
                if decision.opens_position:
                    self._transact(journal, data, state, snap, decision)
                elif decision.kind == 'EXIT':
                    failure = None
                    for candidate in decision.tickets:
                        try:
                            self._transact(journal, data, state, snap, decision, ticket=candidate)
                            break
                        except Blocked as exc:
                            if data['pending'] is not None:
                                raise  # A write might have happened: do not try another ticket.
                            failure = exc
                    else:
                        raise failure or Blocked('NO_SAFE_EXIT')
                else:
                    after, realized = self._transact(journal, data, state, snap, decision,
                                                    ticket=decision.tickets[0])
                    if decision.kind == 'TRIM':
                        loser = next((p for p in after.positions if p.ticket == decision.tickets[1]), None)
                        winner = next(p for p in snap.positions if p.ticket == decision.tickets[0])
                        # Reserve costs again for unreported entry fees / price movement.
                        available = realized - cost(winner, self.config)
                        if (loser is None or available + loser.pnl - cost(loser, self.config)
                            < self.config.trim_buffer_usd):
                            report['execution'] = 'TRIM_WINNER_ONLY'
                            return report
                        self._transact(journal, data, state, after, decision,
                                       ticket=loser.ticket, trim_budget=available)
                report['execution'] = 'FILLED'
                report['can_place_order'] = True
                return report
        except Blocked as exc:
            report['blockers'] = [str(exc)]
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError,
                ArithmeticError, OSError, sqlite3.Error):
            report['blockers'] = ['BASKET_ERROR_REVIEW']
        report['entry_allowed'] = False
        return report

    def _transact(self, journal, data, state, snapshot, decision, *, ticket=None, trim_budget=None):
        request, fresh = self.gateway.prepare(snapshot, decision, ticket=ticket)
        if ticket is None:
            blocked = check_open(self.gateway.adapter, fresh, decision, self.config)
            if blocked:
                raise Blocked(blocked)
        elif trim_budget is not None:
            loser = next(p for p in fresh.positions if p.ticket == ticket)
            if trim_budget + loser.pnl - cost(loser, self.config) < self.config.trim_buffer_usd:
                raise Blocked('TRIM_FUNDING_CHANGED')
        data['pending'] = dict(id=uuid4().hex, kind=decision.kind, ticket=ticket,
                               side=decision.side, lots=str(decision.lots), time=fresh.now)
        journal.save(data)  # Must succeed BEFORE order_send; never clear on uncertainty.
        def revalidate(current):
            if ticket is None:
                stamp = datetime.fromtimestamp(current.now, UTC)
                base = update_periods(decode_guard(data['guard']), account_fingerprint=current.identity,
                                      equity=current.status.account.equity, now=stamp)
                guard = evaluate_guards(base, equity=current.status.account.equity,
                    spread_points=(current.status.tick.ask - current.status.tick.bid) / current.status.symbol.point,
                    open_positions=len(current.positions), now=stamp, broker_eligible=True,
                    settings=GuardSettings(max_spread_points=self.config.max_spread_points),
                    policy=TradingPolicy(max_open_positions=self.config.max_positions))
                data['guard'] = asdict(guard.state)
                journal.save(data)
                if not guard.allowed:
                    raise Blocked(guard.reasons[0])
                if self.gateway.cashflow_since(data['created'], current.now):
                    raise Blocked('CASHFLOW_REVIEW')
                remaining = min(guard.state.day_start_equity * D('.02') - guard.day_loss_usd,
                                guard.state.week_start_equity * D('.05') - guard.week_loss_usd)
                blocked = check_open(self.gateway.adapter, current, decision, self.config,
                                     remaining_budget=remaining)
                if blocked:
                    raise Blocked(blocked)
            elif trim_budget is not None:
                loser = next(p for p in current.positions if p.ticket == ticket)
                if trim_budget + loser.pnl - cost(loser, self.config) < self.config.trim_buffer_usd:
                    raise Blocked('TRIM_FUNDING_CHANGED')
        try:
            after, added, realized = self.gateway.send_verified(request, fresh, revalidate)
        except NotSent:
            data['pending'] = None  # The gateway proves no broker write occurred.
            journal.save(data)
            raise
        if added:
            state.tickets[str(added.ticket)] = added.role
            if decision.kind == 'SEED':
                state.side, state.anchor = added.side, added.entry
            elif decision.kind == 'HEDGE':
                state.hedged = True
                state.hedge_count += 1
            else:
                counter = {'DCA_BEFORE': 'dca_before', 'DCA_AFTER': 'dca_after',
                           'PYRAMID': 'pyramid_count'}[decision.kind]
                setattr(state, counter, getattr(state, counter) + 1)
        if ticket is not None:
            state.tickets.pop(str(ticket), None)
        state.last_action = fresh.now
        data.update(state=asdict(state), pending=None)
        journal.save(data)
        after = replace(after, positions=tuple(replace(p, role=state.tickets.get(str(p.ticket), 'unknown'))
                                               for p in after.positions))
        return after, realized
