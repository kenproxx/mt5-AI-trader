# MT5 AI Trader — LiteFinance XAUUSD (Research / Demo only)

Python MetaTrader 5 research project for XAUUSD, **initial equity $5 USD** and **required leverage 1:50**. **No live trading, no `order_send`, and no guarantee of profitability.** Fail-closed: any invalid broker, risk, margin or Demo account condition must block trading. The repo is a set of research foundations, **not a complete autonomous AI trading bot**.

## Quick start — Windows 11

Install 64-bit Python 3.11/3.12 and MetaTrader 5 terminal. Sign into a **LiteFinance Demo** account and verify the terminal's account and leverage.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev,mt5]"
python -m pytest -q
python -m app.main --mock
python -m app.main --real
python -m scripts.demo_diagnostic --side BUY --stop 2999.00 --costs-usd 0
```

The stop price `2999.00` is an example only; choose a valid stop relative to the current Bid/Ask and symbol stop-distance rules. `--real` is **read-only**. The diagnostic checks MT5 `ACCOUNT_TRADE_MODE_DEMO` before margin/profit inspection and never places orders. The output excludes account login and credentials. GitHub CI uses mocks, not a real broker terminal.

## Implemented foundations

| Phase | Scope |
| --- | --- |
| 1 | Broker adapter, fixed Demo policy, risk engine, mock CI |
| 2 | OHLC market data collection and validation |
| 3 | EMA/ATR strategy and paper signal path |
| 4 | Basic backtest metrics and chronological split |
| 5 | Causal ML feature and label research helpers |
| 6 | Structured monitoring and fail-closed health assessment |
| 7 | Offline HTML dashboard snapshot/report |
| 8 | Opt-in Telegram alert sender and in-memory cooldown |
| 9 | Demo research readiness checklist |
| 10 | Read-only minimum-lot margin/stop-loss feasibility |
| 11 | Manual MT5 diagnostic CLI |
| 12 | Fail-closed MT5 Demo account mode verifier |
| 13 | Wire Demo account verifier into diagnostic workflow |

## Project safety policy

- `TradingPolicy`: fixed 1:50, Demo only, initial balance reference $5, target risk 0.5%, maximum risk 1%, daily loss 2%, weekly loss 5%, reserve free margin 30%, max one open position.
- Broker contract size, lot steps, tick value, spread and actual leverage must be read from MT5; never assume broker website terms override the terminal.
- Minimum lot may exceed both $5 margin and the risk budget. In that case **NO_TRADE**. Never bypass risk constraints to force a trade.
- Broker compatibility checks and `order_calc_margin` / `order_calc_profit` are read-only. The existing `order_check` helper also does not transmit an order.
- No credentials in source control or diagnostic output; Telegram is off by default.

## What remains incomplete

No verified real LiteFinance Demo connection in CI; no tick-level realistic backtesting, model training and calibrated out-of-sample evaluation, durable alert operations, recovery and execution integration, extended forward Demo testing, or production trading controls. CI PASS means unit/lint/security checks passed, **not** that the bot can trade safely or profitably.

See `docs/phase9.md`, `docs/phase10.md`, `docs/phase11.md` and `docs/phase12.md` for validation limitations.
