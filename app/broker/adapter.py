"""Read-only MT5 API adapter."""
from decimal import Decimal

from app.broker.models import AccountSnapshot, SymbolSnapshot, TickSnapshot


def dec(value):
    if value is None:
        raise ValueError("Missing value")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("Nonfinite value")
    return result


class MT5Adapter:
    def __init__(self, module=None):
        if module is None:
            import MetaTrader5 as module
        self.mt5 = module

    def initialize(self):
        return bool(self.mt5.initialize())

    def shutdown(self):
        self.mt5.shutdown()

    def terminal_info(self):
        return self.mt5.terminal_info()

    def account_info(self):
        a = self.mt5.account_info()
        if a is None:
            return None
        return AccountSnapshot(
            leverage=int(a.leverage), currency=str(a.currency),
            equity=dec(a.equity), free_margin=dec(a.margin_free),
            balance=dec(a.balance), margin=dec(a.margin),
            trade_allowed=bool(a.trade_allowed), trade_expert=bool(a.trade_expert),
            server=str(a.server), margin_so_call=dec(a.margin_so_call),
            margin_so_so=dec(a.margin_so_so),
        )

    def symbols_get(self):
        symbols = self.mt5.symbols_get()
        return [] if symbols is None else [str(s.name) for s in symbols]

    def symbol_select(self, name):
        return bool(self.mt5.symbol_select(name, True))

    def symbol_info(self, name):
        s = self.mt5.symbol_info(name)
        if s is None:
            return None
        return SymbolSnapshot(
            name=str(s.name), trade_mode=int(s.trade_mode),
            volume_min=dec(s.volume_min), volume_max=dec(s.volume_max),
            volume_step=dec(s.volume_step),
            trade_contract_size=dec(s.trade_contract_size),
            trade_tick_size=dec(s.trade_tick_size),
            trade_tick_value=dec(s.trade_tick_value),
            trade_stops_level=int(s.trade_stops_level),
            trade_freeze_level=int(s.trade_freeze_level),
            trade_exemode=int(s.trade_exemode), filling_mode=int(s.filling_mode),
            point=dec(s.point), digits=int(s.digits), visible=bool(s.visible),
        )

    def symbol_info_tick(self, name):
        t = self.mt5.symbol_info_tick(name)
        return None if t is None else TickSnapshot(
            bid=dec(t.bid), ask=dec(t.ask), time=int(t.time)
        )

    def order_calc_margin(self, side, symbol, lots, price):
        action = self.mt5.ORDER_TYPE_BUY if side == "BUY" else self.mt5.ORDER_TYPE_SELL
        return self.mt5.order_calc_margin(action, symbol, lots, price)

    def order_calc_profit(self, side, symbol, lots, entry, stop):
        action = self.mt5.ORDER_TYPE_BUY if side == "BUY" else self.mt5.ORDER_TYPE_SELL
        return self.mt5.order_calc_profit(action, symbol, lots, entry, stop)

    def order_check(self, request):
        return self.mt5.order_check(request)
