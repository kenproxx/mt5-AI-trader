# MT5 AI Trader — Agent Instructions

## Project
LiteFinance MT5 Classic XAUUSD research system. Reference initial equity USD 5, FIXED account leverage 1:50. Detect actual broker specifications and margin, never assume minimum lot, contract size, symbol leverage, or spread. Default DEMO; live trading permanently disabled for Phase 1.

## Risk
Max target risk 0.5% equity per order, hard limit 1%, max daily loss 2%, max weekly loss 5%, margin reserve 30%, at most one position. No martingale/grid/averaging down, no trades without SL, no trade when broker specs fail. Minimum broker lot exceeding risk = NO_TRADE. Never change leverage to force trading.

## GitHub
Use this repo, feature branches and pull requests, run tests and CI, do not force push or automatically merge without checks/reviews. Do not commit secrets, .env, MT5 passwords, Telegram keys, account statements, real data, private model artifacts or logs. Read AGENTS.md before work.
