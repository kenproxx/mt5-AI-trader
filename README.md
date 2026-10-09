# MT5 AI Trader — Phase 1

Fail-closed MT5 foundation for LiteFinance Classic XAUUSD, **USD 5 equity**, fixed **1:50 leverage**. It is a **read-only demo and research foundation**, not a profitable or complete trading bot. No `order_send` is implemented. If minimum lot/risk/margin fail, return NO_TRADE.

## Install (Windows 11)
Install Python 3.11 or 3.12 (64-bit) and the LiteFinance MT5 terminal. Open the desired **demo account** in the terminal and confirm leverage 1:50. Then in PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev,mt5]"
python -m pytest -q
python -m app.main --mock
python -m app.main --real
```

`--real` only inspects the attached MT5 terminal; it does not place trades. `--mock` uses synthetic broker data exclusively for testing and never validates LiteFinance account conditions. Account type cannot be independently determined from MT5 fields in all circumstances and must also be checked in the terminal/operator records.

## Modules
- app/broker/adapter.py: broker read-only API
- app/broker/compatibility.py: fail-closed leverage, account, symbol and quote validation
- app/risk/engine.py: broker-calculated risk and margin sizing
- app/broker/preflight.py: broker `order_check` helper; never transmits an order
- tests/: isolated mock tests with no credentials
- .github/workflows/ci.yml: test, lint and security scan on commits and PRs

**Limitations:** No real broker credentials, terminal session, margin/contract checks, news data or production order handling verified. MT5 stop losses do not guarantee maximum realized loss during market gaps. Main phases 2–9 (data, strategies, AI, backtesting, news, execution, dashboard and operations) remain outstanding. Use Windows MT5 terminal for broker validation; Linux GitHub CI uses mock only.
