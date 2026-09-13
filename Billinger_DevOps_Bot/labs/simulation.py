import json
import time
from pathlib import Path
from core.configuration.config import Config
from storage.db import db

SCENARIOS_PATH = Config.BASE_DIR / "content" / "company_scenarios.json"

class CompanySimulation:
    def __init__(self, scenarios_path: Path = None):
        self.scenarios_path = scenarios_path or SCENARIOS_PATH
        self.scenarios = self._load_scenarios()

    def _load_scenarios(self) -> list:
        if not self.scenarios_path.exists():
            return []
        try:
            with open(self.scenarios_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("scenarios", [])
        except Exception:
            return []

    def list_scenarios(self) -> list:
        return [
            {
                "id": s.get("id"),
                "title": s.get("title"),
                "company_type": s.get("company_type"),
                "company_name": s.get("company_name"),
                "role": s.get("role"),
                "incident_type": s.get("incident_type"),
                "severity": s.get("severity")
            }
            for s in self.scenarios
        ]

    def get_scenario(self, scenario_id: str) -> dict:
        for s in self.scenarios:
            if s.get("id") == scenario_id:
                return s
        return {}

    def evaluate_response(self, user_id: str, scenario_id: str, student_commands: list, root_cause_answer: str, mitigation_action: str) -> dict:
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return {"error": "Scenario not found"}

        score = 0.0
        feedback = []

        expected_cmds = [c.get("command", "").split()[0].lower() for c in scenario.get("investigation_commands", [])]
        attempted_cmds = [cmd.split()[0].lower() for cmd in student_commands if cmd.strip()]
        
        matches = sum(1 for c in attempted_cmds if any(exp in c for exp in expected_cmds))
        cmd_score = min(40.0, (matches / max(1, len(expected_cmds))) * 40.0)
        score += cmd_score

        expected_rc = scenario.get("root_cause", {}).get("technical_cause", "").lower()
        if any(keyword in root_cause_answer.lower() for keyword in expected_rc.split()[:5]):
            score += 30.0
            feedback.append("Accurate root cause diagnosis identified.")
        else:
            feedback.append("Root cause diagnosis was partial or imprecise.")

        expected_mitigation = scenario.get("mitigation", {}).get("immediate_steps", "").lower()
        if any(keyword in mitigation_action.lower() for keyword in ["rollback", "restart", "scale", "drain", "patch", "revoke"]):
            score += 30.0
            feedback.append("Effective immediate mitigation executed.")
        else:
            feedback.append("Mitigation did not follow standard SRE protocol.")

        passed = score >= 75.0
        status = "PASSED" if passed else "FAILED"

        run_id = f"sim_{scenario_id}_{int(time.time())}"
        db.execute("""
            INSERT INTO lab_runs (id, user_id, scenario_id, scenario_type, role, status, score, evaluation_json, duration_seconds, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, user_id, scenario_id,
            scenario.get("company_type", "General"),
            scenario.get("role", "DevOps Engineer"),
            status, score, json.dumps(feedback), 60.0, time.time()
        ))

        return {
            "run_id": run_id,
            "status": status,
            "score": round(score, 1),
            "feedback": feedback,
            "postmortem_rubric": scenario.get("postmortem_rubric")
        }

company_simulation = CompanySimulation()
