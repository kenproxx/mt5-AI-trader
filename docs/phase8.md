# Phase 8 — alerting foundation

Includes in-memory per-key alert cooldown and optional Telegram message delivery (off by default). No scheduling, queue, retry/backoff, persistence, monitoring-to-alert wiring, webhook or on-call escalation yet. Telegram token must come from a runtime secret; never log it. Avoid using untrusted raw broker output as Telegram message content. The transport sends only when explicitly enabled; it never places MT5 orders. Alert cooldown resets on restart.
