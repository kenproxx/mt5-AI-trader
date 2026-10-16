# Multi-Agent advisory workflow

Five independent API calls (code, qa, review, cicd, merge-readiness) run in parallel on pull requests and manual workflow dispatch. Results are separate GitHub Actions artifacts; they are **advisory only**. This is not autonomous coding, testing, or merging. The agent input is limited to repository policy/docs, not full PR diffs. Do not trust it as comprehensive review.

## Setup
Repository Settings > Secrets and variables > Actions: create secret `OPENAI_API_KEY` using your own API key. Optionally set Actions variable `AGENT_MODEL` to an available model. Never commit API keys.

## Safety
No write permission, no execution of generated code, no live trading, no automatic PR approval or merge. A missing key causes the workflow to fail visibly. Each job produces an artifact if the API returns text. AI findings must be independently verified.

## Next steps
Add PR diff ingestion with safe size bounds, issue assignment and agent coding in isolated branches; configure required status checks and independent human review. Merge is permitted only after real CI success and required approvals. Review API usage and cost limits before enabling automatic triggers.
