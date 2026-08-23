# User Guide — Billinger Bot v2.9.0

## 1. Start the bot

1. Extract the complete `Billinger_DevOps_Bot` folder to the Windows computer or external hard disk.
2. Double-click `Start_Billinger_Bot.bat`.
3. The launcher uses the portable runtime when present, otherwise an installed Python, otherwise it offers the one-time portable-runtime setup.
4. Keep the command window open while using the dashboard.
5. Press `Ctrl+C` in that window to stop the bot.

The dashboard normally opens at `http://127.0.0.1:8765`.

## 2. Select the student

Create or select one of the 10 local student profiles. Use a student PIN where required. Progress, tests, interviews, projects, portfolio material, resume variants, and job applications are stored separately for each student.

## 3. Complete the learning pathway

Recommended order:

1. Follow the dependency-based Learning Roadmap.
2. Read the verified PDF/DOCX books assigned to the selected tool.
3. Complete lessons from Beginner through Master.
4. Perform guided Practice Labs.
5. Pass level tests.
6. Handle Virtual Company tickets, stand-ups, incidents, and reviewer feedback.
7. Use Safe Real Lab for allowlisted command practice.
8. Complete timed practical examinations and enterprise capstones.
9. Review the Skill Matrix and revise weak domains.
10. Complete adaptive interviews and the nine-round recruitment journey.

## 4. Read and question course books

1. Open **Learning Roadmap** and select a technical tool.
2. Only books verified for that primary tool are displayed.
3. Select **Read & ask**.
4. Use **PDF view** for the original layout or **Text view** for page-aware extracted text.
5. Ask a question about the selected book. Deterministic answers show supporting pages and passages.
6. Mark the book reviewed to save progress.
7. Program-wide manuals remain under **Program Library**, not under every technical tool.

## 5. Practice and labs

- **Simulator:** Default and safest; provides realistic output without executing host commands.
- **Windows allowlist:** Runs only approved non-destructive commands inside the student's workspace.
- **WSL allowlist:** Runs approved commands through WSL when WSL is installed.

Always inspect the task, collect evidence, validate the result, consider security, and provide rollback steps. The safe lab intentionally does not execute every command taught in the curriculum.

## 6. Build the verified DevOps portfolio

1. Open **Portfolio Studio**.
2. Add completed work and select the truthful origin: guided course project, independent project, simulated company assignment, practical assessment, or verified professional work.
3. Add architecture, implementation, security controls, tests, monitoring, troubleshooting, rollback, outcome, and evidence.
4. Correct any secret-scanner warning before publication.
5. Generate a general or job-specific portfolio.
6. Review the static website, PDF summary, and GitHub-ready ZIP before publishing.

Only approved, supportable work should be included in the public portfolio.

## 7. Configure the candidate profile

Open **Career Command → Candidate Profile** and enter only verified facts:

- Contact and professional links
- Education and certifications
- Employment and project experience
- DevOps skills and years of experience
- Preferred roles, locations, work arrangement, salary, and notice period
- Master resume source

Review the profile before marking it verified. Missing job requirements are reported but are not silently added to the resume.

## 8. Discover and analyze jobs

You can paste a job description or configure a permitted source such as a public company careers page, Greenhouse board, Lever site, or HTTPS RSS feed. Review:

- Overall suitability score
- Matched and missing requirements
- Experience/seniority fit
- Location and preference fit
- Relevant portfolio evidence
- Risks and recommendation

For restricted portals, use assisted mode: prepare the documents in the bot and complete the portal submission manually.

## 9. Tailor the resume and application

1. Select the analyzed job.
2. Generate the job-specific resume and optionally select the job-specific portfolio.
3. Review all changes and verify every statement.
4. Export PDF, DOCX, HTML, or TXT.
5. Prepare the recruiter email with the correct recipient, subject, body, and attachments.
6. Inspect the EML preview and attachment list.
7. Gmail sending requires OAuth and the exact confirmation word `SEND`.
8. Record or update the application status in the local tracker.

The master resume remains unchanged; each job receives a separate version.

## 10. Prepare for the employer interview

Select the applied job and generate the interview pack. The simulator uses the exact job description, verified candidate profile, selected portfolio evidence, and labelled public/company information. Complete recruiter, HR, technical, troubleshooting, scripting, system-design, managerial, and final rounds. Review the transcript, corrected answers, weak topics, and revision plan.

## 11. Back up and maintain the bot

- Create a full backup before importing learning content, restoring data, or applying an update.
- Keep at least one backup on a different physical disk.
- Use `Run_Self_Test.bat` after moving the bot or when a fault is suspected.
- Use `Run_Advanced_Sandbox_Tests.bat` only for the extended local validation suite.
- Never delete `data`, `portfolios`, `career_data`, `mail_outbox`, `student_workspaces`, `resumes`, or `certificates` unless you intentionally want to remove records.

See `CAREER_PORTFOLIO_GUIDE.md`, `ADMIN_GUIDE.md`, `SECURITY_AND_LIMITATIONS.md`, and `SYSTEM_REQUIREMENTS.md` for detailed operating boundaries.
