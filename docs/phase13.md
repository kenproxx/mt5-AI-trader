# Phase 13 — verified Demo diagnostic integration

The manual diagnostic now checks MT5 `ACCOUNT_TRADE_MODE_DEMO` after compatibility inspection and **before** invoking minimum-lot margin and profit calculations. Missing metadata, LIVE and contest accounts fail closed with `NO_TRADE`. Synthetic unit tests cover verified Demo, Live, missing metadata, disconnected broker and redaction.

The diagnostic still does not send orders, certify the stop can fill, or prove LiteFinance Demo connectivity from CI. An operator must run the script against an actual Windows MT5 Demo terminal and independently inspect the broker output.
