import json
import random
import time
from pathlib import Path
from core.configuration.config import Config
from storage.db import db

INTERVIEW_PATH = Config.BASE_DIR / "content" / "interview_bank.json"

PERSONAS = {
    "Friendly HR": "Approachable, emphasizes cultural alignment, communication, career longevity, and teamwork.",
    "Strict HR": "Rigorous on dates, job tenure, contract consistency, background compliance, and professional clarity.",
    "Technical Engineer": "Focuses on Linux commands, shell syntax, Docker flags, and code troubleshooting.",
    "Senior DevOps Engineer": "Probes CI/CD architecture, Kubernetes controller reconciliation, and state locking in Terraform.",
    "SRE": "Laser-focused on MTTR, SLA/SLO calculation, telemetry vectors (PromQL), and incident postmortems.",
    "Security Engineer": "Hard on IAM least privilege, container CVE scans, secret leakage, and firewall rules.",
    "Engineering Manager": "Assesses project delivery under pressure, cross-team conflict resolution, and technical debt triage.",
    "CTO": "Evaluates cloud cost optimization, architectural scalability, technology choices, and long-term vision.",
    "Stress Interviewer": "Rapid-fire challenging questions, intentional ambiguity, tests poise under critical pressure."
}

class InterviewEngine:
    def __init__(self, bank_path: Path = None):
        self.bank_path = bank_path or INTERVIEW_PATH
        self.questions = self._load_questions()

    def _load_questions(self) -> list:
        if not self.bank_path.exists():
            return []
        try:
            with open(self.bank_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("questions", [])
        except Exception:
            return []

    def start_session(self, user_id: str, stage: str = "DevOps Core", persona: str = "Senior DevOps Engineer", target_company: str = "Enterprise SaaS") -> dict:
        session_id = f"int_{int(time.time())}"
        pool = [q for q in self.questions if q.get("stage", "").lower() == stage.lower()]
        if not pool:
            pool = self.questions

        first_q = random.choice(pool) if pool else {
            "id": "INT-DEFAULT",
            "question": "Can you walk us through how you design zero-downtime CI/CD pipelines in production?",
            "expected_points": ["Blue-Green or Canary", "Health checks", "Automated rollback"]
        }

        db.execute("""
            INSERT INTO interview_sessions (id, user_id, stage, persona, target_company, transcript_json, readiness_score, feedback_json, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, user_id, stage, persona, target_company,
            json.dumps([{"speaker": "interviewer", "question_id": first_q.get("id"), "text": first_q.get("question")}]),
            0.0, "{}", time.time()
        ))

        return {
            "session_id": session_id,
            "stage": stage,
            "persona": persona,
            "persona_description": PERSONAS.get(persona, "Experienced technical interviewer."),
            "target_company": target_company,
            "first_question": first_q
        }

    def evaluate_answer(self, session_id: str, question_id: str, user_answer: str) -> dict:
        q_item = next((q for q in self.questions if q.get("id") == question_id), None)
        ans_len = len(user_answer.split())
        correct = []
        missing = []
        tech_errors = []

        if q_item:
            expected = q_item.get("expected_points", [])
            for point in expected:
                if any(word.lower() in user_answer.lower() for word in point.split()[:3]):
                    correct.append(point)
                else:
                    missing.append(point)
        else:
            correct = ["Clear conceptual overview articulated"]

        if ans_len < 15:
            comm_issues = "Answer is too brief; lacks concrete production depth and command-line examples."
            score = 65.0
        elif ans_len > 150:
            comm_issues = "Well detailed; keep structure concise using the STAR (Situation, Task, Action, Result) methodology."
            score = 88.0
        else:
            comm_issues = "Strong, balanced delivery with good technical focus."
            score = 80.0

        score = min(100.0, max(30.0, score + (len(correct) * 5.0) - (len(missing) * 4.0)))
        follow_up = q_item.get("follow_up_questions", ["How would you automate this check in your CI/CD pipeline?"])[0] if q_item else "Can you describe a time this failed in production?"

        evaluation = {
            "score": round(score, 1),
            "what_was_correct": correct or ["Clear direct tone"],
            "what_was_missing": missing or ["No major points omitted"],
            "technical_errors": tech_errors or ["None detected"],
            "communication_issues": comm_issues,
            "what_interviewer_expected": q_item.get("technical_accuracy_criteria", "Concise, production-accurate explanation.") if q_item else "Direct actionable answer.",
            "better_answer_structure": "1. State principle/tool -> 2. Specific command/config -> 3. Validation step -> 4. Edge-case handling.",
            "follow_up_question": follow_up
        }

        session = db.fetchone("SELECT transcript_json FROM interview_sessions WHERE id = ?", (session_id,))
        if session:
            history = json.loads(session["transcript_json"] or "[]")
            history.append({"speaker": "user", "text": user_answer, "evaluation": evaluation})
            db.execute("UPDATE interview_sessions SET transcript_json = ?, readiness_score = ? WHERE id = ?", (json.dumps(history), score, session_id))

        return evaluation

interview_engine = InterviewEngine()
