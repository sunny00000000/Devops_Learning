# Billinger Bot v2.6.0 — Build and Validation Report

## Integrated scope

- Preserved v2.5.1 learning institute, verified library, company simulation, practical exams, portfolio, career, email, recruitment, administration, backups, studio dashboard, and security controls.
- Added Gemini, OpenAI API, Groq, and OpenRouter provider adapters.
- Added encrypted dashboard credential management, task routes, limits, cooldown, usage audit, adaptive test generation, test/interview analysis, company-role interview packs, and curriculum review proposals.

## Security controls

- Windows DPAPI key encryption.
- No full key in dashboard/API output.
- Provider key table excluded from normal JSON backup.
- Administrator authorization for credential, route, budget, and curriculum-audit operations.
- Per-student authorization for saved analyses and question sessions.
- PII/secret redaction before online requests.
- Provider error bodies not reflected to students.
- Request timeout, output limits, provider daily limits, global daily limit, and circuit-breaker cooldown.
- Fixed Billinger scoring remains authoritative.
- Curriculum proposals require administrator review.

## Automated validation

- Python compilation: passed.
- JavaScript syntax validation: passed.
- HTML duplicate-ID validation: passed.
- 74 unit, regression, and security tests: passed.
- Legacy core HTTP workflow: passed.
- Company/lab/recruitment HTTP workflow: passed.
- Institute/backup/practical HTTP workflow: passed.
- Career/portfolio HTTP workflow: passed.
- v2.6 AI API/dashboard/fallback HTTP workflow: passed.
- Adversarial local HTTP security workflow: passed.
- Browser-rendered AI Control Center desktop journey: passed.
- Browser-rendered mobile navigation and independent scroll journey: passed.
- Browser console errors in controlled UI journey: zero.

## Provider test boundary

No user credentials are bundled. Release validation uses controlled provider test doubles to verify payload shape, routing, fallback, quota handling, cooldown, logging, redaction, and response parsing without consuming paid credits or contacting a live third party. Real provider access must be confirmed with **Test Provider** after the administrator enters a valid key.
