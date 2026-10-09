# Phase 14 — sanitized read-only diagnostic audit

`build_audit` transforms a Demo diagnostic into a bounded, credential-free, serializable audit summary with UTC timestamp, verified account mode and broker-estimated minimum lot/margin/stop loss. The audit is **non-authorizing**: `can_trade` is always false, even if broker calculations appear acceptable.

No network, order submission, persistent storage or automatic scheduling is implemented. Results remain hypothetical until the operator runs the MT5 diagnostic against a real LiteFinance Demo terminal. The report deliberately avoids copying arbitrary broker/error text.
