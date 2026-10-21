# VTrade-style Basket Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans for implementation;
> steps follow test-first development and a final independent code review.

**Goal:** Implement the five requested basket-management features with an
explicit Demo execution mode and a default preview mode.

**Architecture:** Pure planner and risk checks consume immutable snapshots.
A separate MT5 gateway validates identity and execution outcomes. SQLite
records intents and strategy state; the worker owns polling and reporting.

**Tech Stack:** Python 3.11+, Decimal, sqlite3, MetaTrader5 on Windows.

**Spec:** docs/superpowers/specs/2026-10-20-vtrade-basket-design.md

## Global Constraints
- Demo only, USD, leverage 1:50; no order execution during development.
- Fixed lots, no martingale; SL mandatory; per-order risk 0.5%, basket 1%.
- Daily/weekly loss 2%/5%; free-margin reserve 30%.
- Preserve legacy read-only CLI; update PR #28 without automatic merge.

## Review Focus
- A trim winner is closed but the losing leg becomes too expensive.
- A broker times out after accepting an order, then the process restarts.
- A position is closed externally; counters must not recreate its layer.
- A manual/pending order or account change appears between decisions.
- Closing a hedge can increase margin; re-check close requests too.

### Task 1: Pure basket planning and risk
Files: app/basket/config.py, models.py, planner.py, risk.py;
tests/test_basket_planner.py, tests/test_basket_risk.py.
Interfaces: `plan(snapshot, state, config, signal) -> Decision`;
`check_open(adapter, snapshot, decision, config) -> str | None`.
- [x] Write tests covering all five features, priorities and risk rejection.
- [x] Run new tests and observe missing feature failure.
- [x] Implement validated configuration, snapshots, planner and risk budget.
- [x] Run tests and commit the verified unit.

### Task 2: Demo gateway and durable execution
Files: app/basket/gateway.py, journal.py, runner.py;
tests/test_basket_execution.py.
Interfaces: `DemoGateway.snapshot(now) -> Snapshot`; `execute(decision)`;
`BasketRunner.cycle(signal, now, execute=False) -> dict`.
- [x] Write tests for no-write preview, wrong account, hedging, risk, foreign
  positions, pending orders, order_check refusal, partial fills, timeout,
  trim realized funding, restart and identity mismatch.
- [x] Observe failures, implement only guarded Demo execution and journal.
- [x] Run complete pytest suite and commit.

### Task 3: Windows entry point, dashboard and documentation
Files: app/basket/worker.py, app/automation/dashboard.py,
config/basket.example.json, scripts/run_vps_basket.ps1, README.md,
docs/vtrade-basket.md; tests/test_basket_cli.py.
- [x] Verify CLI config rejection and preview integration before wiring UI.
- [x] Add CLI, example configuration, launcher and dashboard basket fields.
- [x] Document each feature, defaults, commands and remaining VPS check.
- [x] Run pytest, ruff and bandit; obtain independent review and fix blockers.
- [ ] Push to PR #28, inspect CI for final commit, report exact scope.


## Review record
Independent reviewer found four Important issues: quote-dependent PnL equality,
missing pre-send spread/period-budget refresh, stale cycle-start clock at send,
and exit blocked on the oldest hedge while another close was margin-safe.
All four received regression coverage and were corrected. Additional checks
cover account-wide OS lock across journal paths and changing account equity.
No broker order was sent; all execution verification used the test terminal.
