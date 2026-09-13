# BILLINGER DEVOPS BOT — END USER HANDBOOK v3.0.0

Welcome to **Billinger**, your comprehensive, private, offline-first DevOps learning and career acceleration platform.

---

## 1. Quick Start Guide

### On Windows
1. Double-click `Start_Billinger_Bot.bat` (or right-click `Start_Billinger_Bot.ps1` and select **Run with PowerShell**).
2. The server will initialize and launch your default browser to `http://127.0.0.1:8080`.
3. Log in with the default credentials:
   - **Username:** `student`
   - **Password:** `billinger123`

### On Linux
1. Open your terminal in the Billinger directory.
2. Execute the launcher script:
   ```bash
   ./start_billinger.sh
   ```
3. Navigate to `http://127.0.0.1:8080` in your web browser.

---

## 2. Platform Navigation & Subsystems

### 🏠 Home Dashboard
- **Personal Learning Twin:** Displays your real-time Job Readiness score and performance across 8 competency dimensions.
- **Next Best Action:** Tells you exactly what lesson, lab, or test to tackle next based on your weakest skills.

### 📚 Learning Core
- Access 12 exhaustive DevOps domains from Linux Kernel internals to Kubernetes and Cloud SRE.
- View deep concepts, syntax breakdowns, and production anti-patterns.

### 💻 Command Playground
- Type and run real commands inside an isolated student sandbox (`labs/student_sandbox`).
- Real-time safety analysis: Destructive commands (e.g. `rm -rf /`, `mkfs`) are automatically blocked to protect your machine.

### 🏢 Virtual Company Simulation
- Assume roles (DevOps Engineer, SRE, Security Engineer, Developer) inside simulated production companies.
- Solve real deployment failures, OIDC certificate rotations, and memory exhaustion issues.

### 🚨 Production Incident Center
- Experience on-call alerts. Acknowledge outages, run triage commands, mitigate root causes, and write blameless postmortems.
- Track your Mean Time To Resolution (MTTR).

### 📝 Assessment & Tests
- Take timed technical assessments across 5 difficulty levels (Beginner to Master).
- Receive automated grading and an instant remediation roadmap for any missed questions.

### 🎙️ Mock Technical Interview
- Practice with 9 distinct interviewer personas (Friendly HR, Strict HR, Senior DevOps, SRE, Stress Interviewer, CTO).
- Receive detailed 8-point feedback on every answer including what was correct, what was missing, and how to improve.

### 🎯 Career & Skill Matcher
- Paste any real job description to analyze required skills vs. your verified learner profile.
- View exact missing skills and the study modules required to close the gap.

### 📄 ATS Resume & Portfolio Engine
- Generate an ATS-compliant tailored resume in Markdown and PDF format.
- Strictly truthful: Only includes technologies and projects you have verified through hands-on labs.
