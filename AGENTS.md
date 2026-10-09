# MT5 AI Trader — Agent Instructions

## Project
Build a Python + MetaTrader 5 XAUUSD scalping research/trading system for LiteFinance (LiteForex) MT5 Classic, initial balance USD 100, target account leverage 1:50. Always discover actual broker symbol specifications, volume constraints, stop levels, margin requirements and spread with MT5 APIs. Never assume contract size, effective symbol leverage or margin. Default to demo/paper mode; do not place live orders without explicit approval.

## GitHub delivery
Repository: https://github.com/kenproxx/mt5-AI-trader
Default branch: main.
For each feature: inspect repository state; create a descriptive feature branch; implement code and tests; commit and push all changed source, tests, sample configurations, requirements and documentation; create a pull request targeting main; report PR URL, commit SHA, tests and blockers. Never claim uploaded until remote GitHub confirms the commit. Do not force-push main or automatically merge if checks are absent or failing. Merge only after required checks and review pass. Avoid making a new branch per trivial edit within the same feature.

## Safety and secrecy
Never commit passwords, tokens, account logins, private keys, .env, credentials, locally downloaded news datasets, account statements, trading logs, trained models or sensitive runtime artifacts. Add appropriate .gitignore and .env.example. Use environment variables or runtime secret management. Trading limits: target 0.5% equity risk per trade, hard max 1%; daily loss guard 2%, weekly 5%, maximum one open position, no martingale/grid; account for spread, commission, slippage and margin. If broker minimum lot violates risk constraints, NO TRADE. Always use broker-side SL and kill switch.

## Engineering
Separate market data, news, feature engineering, AI model training, inference, risk engine, broker execution, backtesting, monitoring, API and dashboard. Train candidate models offline with purged time-series validation and out-of-sample tests. Models never auto-promote to live. Include tests for broker contract discovery, order sizing, margin, risk gates, failures and prevention of duplicate orders. Keep a README with Windows 11/MT5 Classic demo setup and GitHub workflow.
