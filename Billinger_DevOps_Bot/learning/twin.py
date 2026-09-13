from storage.db import db
from learning.catalog import catalog
import json

class PersonalLearningTwin:
    @staticmethod
    def get_learner_profile(user_id: str) -> dict:
        cmd_rows = db.fetchall("SELECT command, tool, status, mistakes_detected FROM command_history WHERE user_id = ?", (user_id,))
        commands_attempted = set(r["command"].split()[0] for r in cmd_rows if r["command"])
        commands_mastered = set(r["command"].split()[0] for r in cmd_rows if r["status"] == "SUCCESS")
        commands_weak = set(r["command"].split()[0] for r in cmd_rows if r["status"] == "FAILED")
        
        all_catalog_cmds = set(c["command"].split()[0] for c in catalog.get_all_commands())
        commands_never_attempted = all_catalog_cmds - commands_attempted

        lab_rows = db.fetchall("SELECT status, score FROM lab_runs WHERE user_id = ?", (user_id,))
        total_labs = len(lab_rows)
        passed_labs = sum(1 for l in lab_rows if l["status"] in ("SUCCESS", "PASSED"))
        lab_success_rate = round((passed_labs / total_labs * 100) if total_labs > 0 else 0.0, 1)

        test_rows = db.fetchall("SELECT percentage, passed, gaps_json FROM test_results WHERE user_id = ?", (user_id,))
        avg_test_score = round(sum(t["percentage"] for t in test_rows) / len(test_rows) if test_rows else 0.0, 1)
        
        incident_rows = db.fetchall("SELECT mttr_seconds, status FROM incident_records WHERE user_id = ?", (user_id,))
        resolved_incidents = sum(1 for i in incident_rows if i["status"] == "RESOLVED")
        
        interview_rows = db.fetchall("SELECT readiness_score FROM interview_sessions WHERE user_id = ?", (user_id,))
        avg_interview_score = round(sum(i["readiness_score"] for i in interview_rows) / len(interview_rows) if interview_rows else 0.0, 1)

        knowledge = min(100.0, max(15.0, avg_test_score if test_rows else 45.0))
        hands_on = min(100.0, max(10.0, lab_success_rate if total_labs else 30.0))
        troubleshooting = min(100.0, max(10.0, (resolved_incidents / len(incident_rows) * 100) if incident_rows else 35.0))
        production = min(100.0, (knowledge * 0.4 + hands_on * 0.3 + troubleshooting * 0.3))
        interview_readiness = avg_interview_score if interview_rows else 40.0
        communication = min(100.0, interview_readiness * 0.9 + 10.0)
        portfolio_score = 50.0 + min(50.0, total_labs * 5.0)
        job_readiness = round((knowledge * 0.2 + hands_on * 0.2 + troubleshooting * 0.2 + production * 0.15 + interview_readiness * 0.15 + portfolio_score * 0.1), 1)

        if job_readiness >= 85: current_level = "Master / Principal SRE"
        elif job_readiness >= 75: current_level = "Senior DevOps Engineer"
        elif job_readiness >= 60: current_level = "Professional DevOps Engineer"
        elif job_readiness >= 45: current_level = "Intermediate DevOps Engineer"
        else: current_level = "Beginner DevOps Learner"

        weaknesses = []
        if hands_on < 60: weaknesses.append("Practical lab container orchestration & IaC deployments")
        if troubleshooting < 65: weaknesses.append("Production incident triage & root cause analysis (MTTR)")
        if len(commands_weak) > 0: weaknesses.append(f"Commands with repeated errors: {', '.join(list(commands_weak)[:5])}")

        next_action = {
            "recommended_lesson": "Module 7: Kubernetes Orchestration & Helm Packaging",
            "recommended_lab": "Canary Deployment Failure & Rollback",
            "recommended_test": "Intermediate Kubernetes & Docker Technical Assessment",
            "recommended_action": "Complete the production incident triage simulator for DB Connection Starvation."
        }

        return {
            "user_id": user_id,
            "current_level": current_level,
            "overall_job_readiness": job_readiness,
            "dimensions": {
                "knowledge": round(knowledge, 1),
                "hands_on": round(hands_on, 1),
                "troubleshooting": round(troubleshooting, 1),
                "production": round(production, 1),
                "interview": round(interview_readiness, 1),
                "communication": round(communication, 1),
                "portfolio": round(portfolio_score, 1),
                "job_readiness": job_readiness
            },
            "commands_mastered_count": len(commands_mastered),
            "commands_weak": list(commands_weak)[:10],
            "commands_never_attempted_count": len(commands_never_attempted),
            "current_weaknesses": weaknesses or ["None detected - proceed to Capstone project."],
            "next_best_action": next_action
        }

learning_twin = PersonalLearningTwin()
