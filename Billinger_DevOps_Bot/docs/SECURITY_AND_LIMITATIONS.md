# Security and Operating Boundaries — Billinger Bot v2.6.0

## Local operating model

- The application server binds to `127.0.0.1` by default and is not designed to be exposed directly to a LAN or the public internet.
- Localhost Host validation and origin checks reject unexpected cross-origin state-changing requests.
- Career, portfolio, resume, and application operations require a student-scoped session token.
- Administrator and student sign-ins are rate limited to reduce brute-force attempts.
- Student PINs are local convenience controls; they are not enterprise identity management or full-disk encryption.

## File and archive safety

- ZIP import, restore, and update staging reject path traversal, symbolic links, encrypted entries, excessive file counts, oversized members, extreme compression ratios, and corrupt archives.
- Generated and downloaded files are constrained to approved application directories.
- Portfolio publication is blocked when likely passwords, private keys, tokens, or other secrets are detected.
- Imported PDFs, DOCX files, screenshots, and project archives should still come from trusted sources. The bot is not an antivirus product.

## Safe-lab boundaries

- Simulator mode is the default and does not execute commands on the host computer.
- Optional Windows and WSL execution modes use executable and subcommand allowlists and workspace-contained paths.
- Destructive operations, privilege escalation, shell chaining, redirection, remote access, path traversal, unrestricted Python execution, Kubernetes secret access, and host administration are blocked.
- The allowlist reduces risk but does not turn the laptop into an enterprise-grade sandbox. Use disposable WSL or virtual environments for untrusted code.

## Gmail and external services

- Gmail integration uses OAuth and does not request or store the user's Gmail password.
- OAuth client configuration and tokens are stored locally; on Windows, supported OAuth material is protected for the current Windows user with DPAPI.
- Sending requires a prepared draft, attachment/ownership validation, the exact confirmation word `SEND`, duplicate-send protection, and persistent rate limits.
- A compromised Windows account, browser, OAuth token, or Google account can still affect email security. Revoke the OAuth grant immediately if the hard disk or computer is lost.
- Job discovery supports permitted public sources and official/public feeds. It does not bypass CAPTCHAs, logins, anti-bot controls, robots restrictions, or portal terms.

## Truthfulness and recruitment boundaries

- Candidate profiles, resumes, cover letters, portfolios, and interview preparation must use verified information supplied by the user.
- The bot does not intentionally fabricate employment, qualifications, projects, certifications, or production experience.
- Simulated company work, guided labs, independent projects, assessments, and professional employment are labelled separately.
- Job-match scores, ATS analysis, company research, and interview predictions are advisory and do not guarantee selection or employment.
- Every external application and email should be reviewed by the user before submission.

## AI and internet limitations

- The core system works without a local AI model.
- Optional AI endpoints are restricted to localhost. Model output may be inaccurate and is not the sole authority for pass/fail, hiring, or security decisions.
- Internet access is required for live job discovery, company research, Gmail OAuth/send, and the one-time portable-runtime download when no Python runtime is available.
- External websites, APIs, job data, and interview processes may change or become unavailable.

## Residual risk

No application can be proven unhackable. The release was hardened against the documented threat model and automated adversarial cases, but new vulnerabilities, operating-system or browser compromise, malicious documents, DNS/network manipulation, stolen OAuth material, physical-drive theft, and configuration mistakes remain possible. Keep the bot local, maintain Windows/browser updates and separate backups, use strong PINs, encrypt the external drive when appropriate, and review all generated material before publication or submission.
