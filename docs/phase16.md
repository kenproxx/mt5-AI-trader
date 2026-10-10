# Phase 16 — Audit file integrity

`verify_audit_file(path)` checks the strict audit JSON schema, size limit, mode and `can_trade: false`, then returns a SHA-256 digest of the file bytes. Any modified file produces a different digest. It rejects oversized files, unknown fields and explicit trading authorization.

A digest alone is **not authentication** or proof that a report came from a real LiteFinance Demo terminal; attackers who can edit both the file and its digest can forge evidence. For tamper-evident archiving, store digests independently in a trusted system. The verifier does not authorize trades, access the network, or connect to MT5.
