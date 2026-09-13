import json
import random
import time
from pathlib import Path
from core.configuration.config import Config
from storage.db import db

QUESTION_BANK_PATH = Config.BASE_DIR / "content" / "question_bank.json"

class TestCenter:
    def __init__(self, bank_path: Path = None):
        self.bank_path = bank_path or QUESTION_BANK_PATH
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

    def create_test_session(self, tool: str = "All", difficulty: str = "Beginner", count: int = 10) -> dict:
        pool = self.questions
        if tool != "All":
            pool = [q for q in pool if q.get("tool", "").lower() == tool.lower()]
        if difficulty != "All":
            pool = [q for q in pool if q.get("difficulty", "").lower() == difficulty.lower()]

        selected = random.sample(pool, min(count, len(pool))) if pool else []

        student_questions = []
        for q in selected:
            student_questions.append({
                "id": q.get("id"),
                "tool": q.get("tool"),
                "difficulty": q.get("difficulty"),
                "type": q.get("type"),
                "question": q.get("question"),
                "options": q.get("options", []),
                "tags": q.get("tags", [])
            })

        session_id = f"test_{int(time.time())}"
        return {
            "session_id": session_id,
            "tool": tool,
            "difficulty": difficulty,
            "question_count": len(student_questions),
            "time_limit_minutes": len(student_questions) * 2,
            "questions": student_questions
        }

    def grade_test(self, user_id: str, tool: str, difficulty: str, student_answers: dict) -> dict:
        total = 0
        correct = 0
        gaps = []
        remediations = []

        q_map = {q["id"]: q for q in self.questions}

        for q_id, given_ans in student_answers.items():
            if q_id in q_map:
                total += 1
                q_item = q_map[q_id]
                expected = str(q_item.get("correct_answer", "")).strip().lower()
                given = str(given_ans).strip().lower()
                
                if given == expected or (expected in given and len(expected) > 3):
                    correct += 1
                else:
                    gaps.append({
                        "question_id": q_id,
                        "question": q_item["question"],
                        "expected": q_item["correct_answer"],
                        "given": given_ans,
                        "explanation": q_item.get("explanation", "")
                    })
                    remediation = q_item.get("remediation_lesson")
                    if remediation and remediation not in remediations:
                        remediations.append(remediation)

        percentage = round((correct / total * 100) if total > 0 else 0.0, 1)
        passed = percentage >= 80.0

        test_id = f"res_{int(time.time())}"
        db.execute("""
            INSERT INTO test_results (id, user_id, tool, difficulty, total_questions, correct_answers, percentage, passed, gaps_json, remediation_json, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_id, user_id, tool, difficulty, total, correct, percentage,
            1 if passed else 0, json.dumps(gaps), json.dumps(remediations), time.time()
        ))

        return {
            "test_id": test_id,
            "total_questions": total,
            "correct_answers": correct,
            "percentage": percentage,
            "passed": passed,
            "gaps": gaps,
            "remediation_plan": remediations
        }

test_center = TestCenter()
