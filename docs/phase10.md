# Phase 10 — Demo feasibility diagnostic

This is a read-only diagnostic built on the existing MT5 adapter and compatibility checker. It calculates the **minimum-lot** broker-reported stop loss and margin using `order_calc_profit` and `order_calc_margin`, compares them against a risk budget and reserved free margin, and returns a blocked state unless full checks are performed separately. It **never** sends an order and does not certify trading eligibility.

Example synthetic MockAdapter: equity $5, leverage 1:50, XAUUSD 100 oz/lot, price around $3000, minimum lot 0.01. The simplified mock margin estimate is about $60, above $5. This is a **mock calculation**, not observed LiteFinance broker data.

Next: test with the actual LiteFinance MT5 Classic **Demo** terminal on a supported Windows environment; confirm account server/demo status (current snapshot does not carry account trade_mode), contract size, symbol tick properties, broker margin/profit calculations, spread, and order_check without order_send. Do not enable live orders or weaken stop-loss/risk limits to make $5 appear tradable.
