"""
End-to-End Integration Test Pipeline
"""
import unittest
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.authentication.auth import auth_manager
from learning.playground import playground
from labs.simulation import company_simulation
from labs.incidents import incident_center
from assessment.tests import test_center
from interview.engine import interview_engine
from career.matcher import job_matcher
from resume.engine import resume_engine
from portfolio.engine import portfolio_engine

class TestE2EPipeline(unittest.TestCase):
    def test_full_student_journey(self):
        user_id = f"student_e2e_{int(time.time() * 1000)}"
        token = auth_manager.create_session(user_id, "sunny_tester", "student")
        self.assertTrue(token.startswith("btoken_"))

        play_res = playground.practice_command(user_id, "echo hello_devops", execute_in_sandbox=True)
        self.assertIn(play_res["status"], ["SUCCESS", "SIMULATED"])

        scenarios = company_simulation.list_scenarios()
        self.assertGreater(len(scenarios), 0)
        eval_res = company_simulation.evaluate_response(
            user_id,
            scenarios[0]["id"],
            ["kubectl get pods", "kubectl describe pod"],
            "Canary failure schema lock",
            "rollback deployment"
        )
        self.assertIn("score", eval_res)

        inc = incident_center.trigger_incident(user_id, "L1")
        ack = incident_center.acknowledge_incident(inc["incident_id"])
        res = incident_center.resolve_incident(inc["incident_id"], {"root_cause": "Traffic spike", "mitigation": "Scaled HPA"})
        self.assertEqual(res["status"], "RESOLVED")

        session = test_center.create_test_session(tool="All", difficulty="Beginner", count=5)
        self.assertEqual(session["question_count"], 5)
        mock_answers = {q["id"]: (q.get("options") or ["A"])[0] for q in session["questions"]}
        grade_res = test_center.grade_test(user_id, "All", "Beginner", mock_answers)
        self.assertIn("percentage", grade_res)

        int_sess = interview_engine.start_session(user_id, stage="DevOps Core")
        first_q = int_sess["first_question"]
        ans_eval = interview_engine.evaluate_answer(int_sess["session_id"], first_q.get("id", "q1"), "In our production environment, we implement automated Canary deployments with Prometheus metrics, automated rollback triggers, and comprehensive health checks.")
        self.assertGreaterEqual(ans_eval["score"], 50.0)

        jd_text = "Looking for Senior DevOps Engineer with Docker, Kubernetes, AWS, Terraform, and Jenkins experience."
        match_res = job_matcher.analyze_job_description(user_id, jd_text)
        self.assertGreaterEqual(match_res["match_score_pct"], 60.0)

        resume_res = resume_engine.generate_tailored_resume(user_id, jd_text)
        self.assertIn("PROFESSIONAL SUMMARY", resume_res["resume_markdown"])
        self.assertIn("VERIFIED PRACTICAL LAB PROJECTS", resume_res["resume_markdown"])

        portfolio_res = portfolio_engine.generate_portfolio(user_id)
        self.assertGreaterEqual(portfolio_res["total_verified_projects"], 2)
