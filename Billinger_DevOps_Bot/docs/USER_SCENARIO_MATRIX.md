# User and Scenario Validation Matrix

## Content-wide execution

The automated suite validates all 21 DevOps domains and every generated company scenario:

- 336 lessons checked for title, explanation/example, company use, and level placement.
- 84 practice labs checked for scenario, deliverables, and acceptance criteria.
- All 84 virtual-company tickets submitted through the scoring engine.
- All 21 production incidents submitted through the incident engine.
- All 21 enterprise capstones submitted through the capstone-review engine.
- All 21 skill domains, 9 recruitment rounds, tests, interviews, document reading, resume import, and verified library classification validated.

## User journeys

1. New local student starts with an unprotected profile.
2. PIN-protected student signs in and is isolated from other student records.
3. Student reads tool-specific material without cross-tool document mixing.
4. Student learns, practices, tests, completes company work, and receives scores.
5. Student creates portfolio evidence and is blocked when a secret is detected.
6. Student generates a general or job-specific portfolio.
7. Student saves a verified candidate profile and analyzes a suitable job.
8. Student generates a truthful tailored resume without claiming missing skills.
9. Student prepares an email with owned attachments and explicit approval.
10. Student records assisted portal submission and follow-up.
11. Student creates a job-specific nine-round interview preparation pack.
12. Administrator manages batches, assignments, imports, backups, and updates.
13. Desktop and 360-pixel mobile/narrow-screen navigation scroll correctly without zooming.

## External actions intentionally not executed in automated tests

Automated tests do not send a real email, submit a real job application, use a real recruiter account, or alter a real company portal. Gmail and ATS adapters are tested with controlled mock responses; a live send requires the user's OAuth authorization and deliberate approval.
