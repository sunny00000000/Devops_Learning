# BILLINGER PLATFORM — ENTERPRISE ARCHITECTURE SPECIFICATION v3.0.0

## 1. System Overview
Billinger is a lightweight, zero-external-dependency, production-grade DevOps and SRE learning and career acceleration platform. It runs natively across Windows (10/11) and Linux (Ubuntu/Debian/RHEL/CentOS/Arch) under Python 3.10+ within a strict 4 GB RAM footprint.

```
+-----------------------------------------------------------------------------------+
|                            BILLINGER FRONTEND DASHBOARD                          |
|         Comfort Dark UI • WCAG AA Accessible • 4K-Responsive SPA • REST API      |
+-----------------------------------------------------------------------------------+
                                        | (HTTP / JSON / SSE)
+-----------------------------------------------------------------------------------+
|                             BILLINGER API ROUTER                                  |
|         Health • Learning • Labs • Incidents • Assessments • Interviews • AI      |
+-----------------------------------------------------------------------------------+
   |             |            |               |               |              |
   v             v            v               v               v              v
+---------+ +---------+ +-----------+ +---------------+ +-----------+ +------------+
|  CORE   | | STORAGE | | SECURITY  | |   LEARNING    | |   LABS    | | ASSESSMENT |
| Auth/ACL| | SQLite  | | Sandbox   | |  12 Domains   | | Company   | | 5 Levels   |
| Config  | | Backups | | Command   | |  Mastery Gate | | Simulation| | Tests &    |
| Telemetry | Migrat. | | Sanitizer | |  Learning Twin| | Incidents | | Remediation|
+---------+ +---------+ +-----------+ +---------------+ +-----------+ +------------+
   |             |            |               |               |              |
   +-------------+------------+-------+-------+---------------+--------------+
                                      |
         +----------------------------+----------------------------+
         v                                                         v
+------------------+                                      +-----------------+
|    DOCUMENTS     |                                      |   AI ROUTER     |
| Strict 0-Mixing  |                                      | Workload Matrix |
| Classification   |                                      | Gemini • Groq   |
| Version Tracking |                                      | OpenAI • Router |
+------------------+                                      +-----------------+
```

## 2. Decoupled Subsystem Architecture

### 2.1 Core Subsystem (`core/`)
- `configuration/config.py`: Centralized environment variable binding, path anchors, and runtime defaults.
- `authentication/auth.py`: Cryptographically secure authentication utilizing PBKDF2-HMAC-SHA256 with unique 16-byte salts and URL-safe 256-bit session tokens.
- `authorization/rbac.py`: Hierarchical Role-Based Access Control (`guest` < `student` < `recruiter` < `admin`).
- `logging/logger.py`: Thread-safe structured logging with regex-based redaction of Bearer tokens and API keys.
- `system_monitor.py`: Real-time tracking of CPU, RAM, disk, and local network reachability (ONLINE, OFFLINE, DEGRADED).

### 2.2 Storage Subsystem (`storage/`)
- `db.py`: Thread-local SQLite connection manager with WAL (Write-Ahead Logging) mode and foreign key enforcement.
- `backup_manager.py`: Atomic ZIP snapshot creation with SHA256 integrity manifest generation and safe pre-restore rollback safeguards.

### 2.3 Security Subsystem (`security/`)
- `guard.py`: 3-tier command inspection engine (`SAFE`, `CAUTION`, `BLOCKED`). Blacklists destructive host mutations (`rm -rf /`, `mkfs`, fork bombs, raw disk writes, unverified curl pipes).
- `sandbox.py`: Isolated student workspace directory runner with strict timeout caps (15s default) and process isolation.
- `sanitizer.py`: Directory traversal prevention (`safe_join`), XSS HTML entity escaping, and filename sanitization.

### 2.4 Learning Subsystem (`learning/`)
- `catalog.py`: 12 core DevOps curriculum domains spanning 6 mastery tiers (Beginner to Master).
- `playground.py`: Interactive command sandbox logger; detects common mistakes and awards mastery upon proven execution.
- `twin.py`: Personal Learning Twin tracking 8 competency dimensions, weakness diagnosis, and Next Best Action recommendations.
- `mastery.py`: Dynamic mastery gates requiring Knowledge >= 85%, Practical >= 80%, Scenario = PASS, and Incident = PASS.
- `coverage.py`: Course coverage auditor auditing command, concept, lab, and scenario completeness across tools.

### 2.5 Documents Subsystem (`documents/`)
- `ingestion.py`: Text extractor supporting PDF, DOCX, TXT, MD, and CSV with SHA256 content hashing.
- `classifier.py`: Domain classifier with anti-keyword penalties ensuring zero cross-contamination.
- `versioning.py`: Hash-based version tracking supporting View, Compare (unified diff), and Archived versions.
- `search.py`: Fast indexed search engine.

### 2.6 Labs Subsystem (`labs/`)
- `simulation.py`: Virtual company scenarios across E-Commerce, Fintech, HealthTech, and SaaS with multi-role assignments.
- `incidents.py`: Production Incident / On-Call Center measuring MTTR, acknowledgment latency, and postmortem quality.

### 2.7 Assessment Subsystem (`assessment/`)
- `tests.py`: Timed test generator with randomized pools across 7 question types.
- `gap_analysis.py`: Error pinpointing mapping failed questions to exact remediation modules.

### 2.8 Interview Subsystem (`interview/`)
- `engine.py`: Adaptive interview runner with 9 interviewer personas.
- `analyzer.py`: 8-point answer evaluator offering constructive rubric feedback and contextual follow-up questions.

### 2.9 AI Subsystem (`ai/`)
- `providers.py`: Multi-provider manager supporting Gemini, Groq, OpenAI, and OpenRouter with key masking.
- `router.py`: Workload-specific priority routing with automatic failover and local deterministic fallback.

### 2.10 Career Subsystem (`career/`, `resume/`, `portfolio/`)
- `matcher.py`: Skill gap analyzer comparing Job Descriptions against verified learner skills without qualification fabrication.
- `resume/engine.py`: ATS resume generator producing truth-verified resumes.
- `portfolio/engine.py`: Evidence-based portfolio compiler linking completed labs and capstones to verified achievements.
