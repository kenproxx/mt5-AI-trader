# Phase 3 — initial paper-only trading MVP

Implements causal EMA/ATR and a conservative multi-timeframe trend alignment baseline, plus paper risk gating. Only fully closed candles may be passed by the caller; future live data integration must enforce this. No real/demo order sending, position journal, broker order_check orchestration, news/AI filter or persistent simulation is implemented yet. No profitability claims. Requires additional validation before phase acceptance.
