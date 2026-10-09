# Phase 11 — manual MT5 Demo diagnostic

Run on a Windows computer with MetaTrader 5 terminal and Python MetaTrader5 installed, **after manually verifying the terminal is logged into a LiteFinance DEMO account**.

```powershell
python -m scripts.demo_diagnostic --side BUY --stop 2999.00 --costs-usd 0
```

Choose a stop price appropriate to the current quote; 2999.00 is illustrative only. The script initializes MT5, reads account, XAUUSD symbol and bid/ask, and invokes broker `order_calc_margin` and `order_calc_profit` for the minimum lot. It does not place or check an order. It never prints credentials or account login IDs.

Important limitations: the current AccountSnapshot lacks a trustworthy account trade-mode field; the script therefore cannot independently prove the account is DEMO. Do not treat this report as permission to trade. The script does not guarantee the stop-loss is executable and does not validate broker slippage or trading costs. A real broker test has not been performed by GitHub CI.
