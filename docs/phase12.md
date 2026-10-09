# Phase 12 — verify MT5 DEMO mode

A read-only verification function compares the terminal account's `trade_mode` to the official MetaTrader5 `ACCOUNT_TRADE_MODE_DEMO` constant. Missing, malformed, live, or contest modes fail closed. This is **not** proof of connection to a real broker in CI: tests use synthetic account objects.

This verifier must be wired into every future execution preflight before any order submission is even considered. The project remains read-only/paper-only. Do not infer Demo status from a server name, account number or a user-supplied flag.
