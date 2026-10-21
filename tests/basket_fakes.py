"""MT5 boundary double; all strategy, state, risk and execution code stay real."""
from types import SimpleNamespace as NS


class Terminal:
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ACCOUNT_TRADE_MODE_DEMO = 0
    ACCOUNT_MARGIN_MODE_RETAIL_HEDGING = 2
    TRADE_ACTION_DEAL = 1
    ORDER_TIME_GTC = 0
    ORDER_FILLING_FOK = 0
    ORDER_FILLING_IOC = 1
    TRADE_RETCODE_DONE = 10009

    def __init__(self, now=1792497600):
        self.account = NS(login=123, trade_mode=0, leverage=50, currency='USD',
            equity=10000, balance=10000, margin_free=10000, margin=0,
            trade_allowed=True, trade_expert=True, server='FakeDemo',
            margin_so_call=50, margin_so_so=30, margin_mode=2,
            hedge_allowed=True, fifo_close=False)
        self.terminal = NS(connected=True, trade_allowed=True, tradeapi_disabled=False)
        self.symbol = NS(name='XAUUSD', trade_mode=4, volume_min=.01, volume_max=10,
            volume_step=.01, trade_contract_size=100, trade_tick_size=.01,
            trade_tick_value=1, trade_stops_level=10, trade_freeze_level=0,
            trade_exemode=2, filling_mode=1, point=.01, digits=2, visible=True)
        self.tick = NS(bid=3000, ask=3000.2, time=now)
        self.positions = []
        self.orders = []
        self.sent = []
        self.deals = []
        self.check_code = 0
        self.send_mode = 'done'
        self.realized_override = None

    def initialize(self): return True
    def shutdown(self): pass
    def terminal_info(self): return self.terminal
    def account_info(self): return self.account
    def symbols_get(self): return [self.symbol]
    def symbol_select(self, name, select): return True
    def symbol_info(self, name): return self.symbol
    def symbol_info_tick(self, name): return self.tick
    def positions_get(self): return self.positions
    def orders_get(self): return self.orders
    def order_calc_margin(self, side, symbol, lots, price): return price * lots * 100 / 50
    def order_calc_profit(self, side, symbol, lots, entry, stop):
        return (stop - entry) * lots * 100 * (1 if side == 0 else -1)
    def order_check(self, request):
        return NS(retcode=self.check_code, equity=self.account.equity,
                  margin_free=self.account.margin_free - 100, margin=100, margin_level=10000)
    def history_deals_get(self, *args, **kwargs):
        if 'ticket' in kwargs:
            return [d for d in self.deals if d.order == kwargs['ticket']]
        return self.deals
    def order_send(self, request):
        self.sent.append(request.copy())
        if self.send_mode == 'timeout':
            return None
        if self.send_mode == 'partial':
            return NS(retcode=10010, volume=request['volume'] / 2, deal=1, order=1, price=3000)
        order = 100 + len(self.sent)
        if 'position' in request:
            p = next(p for p in self.positions if p.ticket == request['position'])
            self.positions.remove(p)
            profit = p.profit if self.realized_override is None else self.realized_override
            self.deals.append(NS(order=order, ticket=order + 1000, profit=profit,
                swap=p.swap, commission=-.01, fee=0, volume=request['volume'],
                type=request['type'], entry=1, time=self.tick.time,
                position_id=p.ticket, magic=request['magic'], symbol='XAUUSD'))
        else:
            self.positions.append(NS(ticket=order, type=request['type'],
                magic=request['magic'], symbol='XAUUSD', volume=request['volume'],
                price_open=request['price'], sl=request['sl'], profit=0, swap=0))
            self.deals.append(NS(order=order, ticket=order + 1000, profit=0, swap=0,
                commission=-.01, fee=0, volume=request['volume'], type=request['type'],
                entry=0, time=self.tick.time, position_id=order,
                magic=request['magic'], symbol='XAUUSD'))
        return NS(retcode=10009, volume=request['volume'], deal=order + 1000,
                  order=order, price=request['price'])
