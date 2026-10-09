# GitHub reference research — structural pass (2026-10-09)

| Repository | Inspected root layout | GitHub license metadata | Assessment |
|---|---|---|---|
| pressure679/LSTM-PPO-Reinforcement-Learning-Trading-Bot-for-MetaTrader-5-XAUUSD | bot.py, requirements.txt, model saves | BSD-3-Clause | Research RL only after baseline; claimed performance unverified |
| maghdam/AlphaFlow-MT5-ML-DL-Trading-Lab | backtests/, features/, models/, live_trading/ | MIT | Separation of training and execution is useful |
| a1shmuk/xauusd-algo-trader | ML, backtest and optimizer Python modules | Not identified | Avoid code reuse until licensing clarified; promotional statistics unverified |
| flegardev/ai-bot | brokers/, risk/, execution/, tests/ | Not identified | Modular adapter pattern, do not copy code |
| Anaswar-ash/MT5-PY-AI-Tbot | Python/MQL project and documentation | MIT | ONNX deployment possibility, not needed in Phase 1 |

Only root trees and GitHub license metadata were inspected. Deep code quality review, leakage audit, order failure semantics, point-in-time backtests and reconnect behaviour **are not yet verified**. No code has been borrowed. Complete code-level audit and license review before any reuse.
