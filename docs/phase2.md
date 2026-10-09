# Phase 2 — Market Data (initial implementation)

Read-only M1/M5/M15/H1 history via MT5 copy_rates_range, UTC-aware ranges, strict OHLC validation, missing-bar reporting, Parquet atomic writes and idempotent incremental merge. Gaps are reported rather than synthesized.

Not yet completed: tick Bid/Ask history, broker session calendar, persistent collection checkpoints, production recovery, spread anomaly thresholds, historical execution costs and broker verification. Weekend/session gaps need calendar-aware classification. No claims of complete Phase 2 acceptance or trading readiness.
