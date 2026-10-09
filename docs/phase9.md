# Phase 9 — Final validation checklist foundation

The readiness evaluator defaults to blocked unless all seven independently verified gates are explicitly True. Even if all pass, it authorizes **DEMO research only**, never live trading.

## Mandatory external evidence before calling the bot ready

- Confirm actual LiteFinance Classic Demo login, leverage exactly 1:50, USD balance and symbol_info/tick properties on the running MT5 terminal.
- Check order_calc_margin/order_calc_profit for minimum 0.01 lot with $5 equity and a realistic XAUUSD spread/stop. If the trade violates any risk or margin constraint, NO_TRADE; do not reduce stops or bypass risk.
- Build a realistic bid/ask tick replay backtester with spreads, commissions, slippage, stop execution, overnight swaps and data gaps.
- Train and evaluate a calibrated model with purged time-series walk-forward validation and true out-of-sample holdout; no guaranteed returns.
- Test broker disconnect, stale quotes, restart/recovery, unexpected positions, repeated fills, loss limits, drawdown limits and emergency kill switch.
- Perform extended forward tests on Demo with independent audit of every order and incident.
- Harden alert delivery, authentication, observability and deployment.

This PR is a **checklist implementation**, not evidence any external check has passed. Do not enable LIVE trading.
