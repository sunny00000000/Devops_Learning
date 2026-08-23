# Billinger Bot v2.6.0 — Architecture

## Design objective

Provide a lightweight, local Windows platform for up to 10 students that combines DevOps learning, realistic company practice, institute management, verified portfolios, job matching, truthful resume tailoring, controlled email applications, application tracking, and vacancy-specific interview preparation. The core uses the Python standard library, SQLite, local files, and a browser dashboard.

## Runtime layers

1. **Portable launcher** — selects a bundled runtime, an installed Python, or performs one-time portable runtime setup.
2. **Local application server** — Python HTTP server, authorization, curriculum, scoring, file generation, job matching, application tracking, maintenance, and safe-lab controls.
3. **3D/VFX browser dashboard** — CSS-based interface for learning, company work, assessments, administration, portfolio, career, resume, email, and interview functions.
4. **Local data layer** — SQLite plus curriculum/question JSON, verified learning-resource index, student workspaces, portfolios, resume variants, outbox drafts, certificates, and backups.
5. **Optional local integrations** — WSL, installed allowlisted DevOps CLIs, a localhost OpenAI-compatible model, and browser/Windows voice features.
6. **Controlled internet integrations** — permitted job feeds/pages, public company research, and Gmail OAuth/send after explicit approval.

## Major application domains

### Learning and institute

- Verified single-primary-tool PDF/DOCX library
- Beginner-to-Master lessons, practices, tests, interviews, tickets, incidents, and capstones
- Student profiles, batches, assignments, planner, practical exams, reports, certificates, backup/restore, and offline update staging

### Portfolio

- Evidence register with truthful origin labels
- Multidimensional project scoring and secret scanning
- Static recruiter website, PDF summary, and GitHub-ready ZIP
- General and job-specific project selection

### Career and recruitment

- Verified candidate profile and preferences
- Greenhouse/Lever/public-source discovery plus manually supplied vacancies
- Explainable job suitability analysis
- Truthful job-specific resume generation
- EML preview and optional Gmail OAuth sending with explicit confirmation
- Application lifecycle tracker
- Company/job-specific nine-round interview preparation

## Local data boundaries

- `data/` — SQLite progress, institute, career, authorization, and tracking records
- `learning_resources/` — original verified books, page-aware text, and strict classification index
- `student_workspaces/` and `labs/` — student practical work and evidence
- `portfolios/` — portfolio websites, PDFs, exports, and project packages
- `resumes/` — master/tailored resume outputs
- `career_data/` — career-related generated artifacts and caches
- `mail_outbox/` — prepared EML drafts and approved local artifacts
- `certificates/` — locally generated certificates
- `backups/` — local backup packages

## Security architecture

- Server binds to localhost and validates Host and Origin for state-changing requests.
- Student-scoped session tokens separate career and portfolio records.
- Administrator/student authentication is rate limited.
- SQLite access uses parameterized statements.
- Generated HTML/XML escapes user-controlled content.
- Public URL fetching permits HTTPS public destinations only, validates redirects, limits response size, and blocks private/local/metadata targets.
- OAuth authorization/token endpoints are pinned to Google's official endpoints; state is single-use.
- Gmail sending validates recipient, headers, ownership, attachments, confirmation, duplicate state, and persistent send limits.
- Archive import/update/restore rejects traversal, symlinks, encrypted entries, oversized members, file-count abuse, extreme compression ratios, and corruption.
- Safe labs use executable/subcommand allowlists and workspace-contained paths.
- Portfolio secret scanning blocks likely credentials from publication.

## Learning-library retrieval

Original documents are stored under `learning_resources/files` and page-aware text under `learning_resources/text`. `learning_resources/index.json` assigns each technical volume to one verified primary tool; program-wide manuals remain isolated. Deterministic document questions retrieve the strongest passages and provide page evidence. When optional localhost AI is enabled, only retrieved passages are supplied and page citation remains required.

## Lightweight design decisions

- No Electron shell or bundled database server
- No mandatory Docker, WSL, cloud runtime, or local language model
- CSS-only 3D/VFX presentation
- Standard-library server and SQLite database
- Heavy real-lab and AI functions remain optional

## External-operation boundary

The bot assists with research, matching, document preparation, email preview, and interview practice. It does not bypass portal authentication, CAPTCHA, robots restrictions, or anti-bot controls. Final applications and external messages remain subject to user review, platform permission, and the user's own accounts.
