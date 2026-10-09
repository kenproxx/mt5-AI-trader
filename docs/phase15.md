# Phase 15 — sanitized JSON audit export

The read-only MT5 diagnostic CLI now supports `--audit-json <new-file.json>`. This exports only the sanitized audit structure (no account login, password, arbitrary error strings or order authorization). Output files are exclusive-create, never overwritten, and capped at 8 KiB. The exporter does not transmit data.

Example (Windows PowerShell; stop price is illustrative only):

```powershell
python -m scripts.demo_diagnostic --side BUY --stop 2999.00 --audit-json demo-audit.json
```

Review file permissions and keep audit records private. `can_trade` is always false; this does not prove LiteFinance Demo connectivity in CI. The default CLI output remains the previous diagnostic JSON for backwards compatibility.
