# Billinger Bot v2.7.0 — Build and Validation Report

## Release focus

- First-run readiness workflow.
- Balanced baseline assessment.
- Evidence-based mastery gates.
- Safe local environment detection.
- Backup integrity verification.
- Provider model discovery and credit-free fallback simulation.
- Course freshness and deprecation tracking.
- Regression preservation of learning, institute, company, career, portfolio, AI, and security modules.

## Automated validation

- Python compilation: passed.
- JavaScript syntax validation: passed.
- HTML duplicate-ID validation: **482 unique IDs, no duplicates**.
- Unit, regression, and security tests: **85 passed**.
- Core HTTP smoke test: passed.
- Company/lab/recruitment HTTP smoke test: passed.
- Institute/practical/backup HTTP smoke test: passed.
- Career/portfolio HTTP smoke test: passed.
- Adaptive AI HTTP smoke test: passed.
- Final-readiness HTTP smoke test: passed.
- Adversarial HTTP security test: passed.
- Four-provider desktop/mobile browser journey: passed.
- First-run readiness browser journey: passed.
- Browser console errors in controlled journeys: **0**.

## v2.7-specific cases

- 20-question baseline balanced across 10 domains.
- Baseline replay and cross-student session misuse rejected.
- Optional AI/environment checks do not block local learning.
- Passive dashboard loads do not create repeated backup-audit records.
- Python, `py`, and `python3` runtime detection supported.
- Environment commands are fixed by application code; user commands are not accepted.
- Backup checksum and ZIP integrity validated.
- Tampered backup detected.
- Nine mastery evidence categories present for all 21 domains.
- Non-HTTPS official documentation links rejected.
- Content older than 180 days can be marked review due.
- Provider model discovery does not expose API keys.
- Fallback dry run consumes zero provider credits.
- Administrator authorization enforced for model discovery, backup verification, freshness updates, and fallback simulation.

## External-service boundary

No paid Gemini, OpenAI, Groq, or OpenRouter request was made while packaging. Live account model access, quotas, network behavior, and billing must be validated using the dashboard after the user enters their own credentials.
