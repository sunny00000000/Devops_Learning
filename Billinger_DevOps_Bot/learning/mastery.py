from storage.db import db
from learning.twin import learning_twin

class DynamicMasteryEngine:
    GATES = {
        "knowledge_min": 85.0,
        "practical_min": 80.0,
        "capstone_min": 82.0,
        "interview_min": 80.0,
        "scenario_status": "PASS",
        "incident_status": "PASS"
    }

    @classmethod
    def evaluate_mastery(cls, user_id: str, tool_id: str) -> dict:
        twin = learning_twin.get_learner_profile(user_id)
        dims = twin["dimensions"]

        passed_knowledge = dims["knowledge"] >= cls.GATES["knowledge_min"]
        passed_practical = dims["hands_on"] >= cls.GATES["practical_min"]
        passed_interview = dims["interview"] >= cls.GATES["interview_min"]
        
        lab_record = db.fetchone(
            "SELECT status, score FROM lab_runs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1",
            (user_id,)
        )
        passed_scenario = lab_record and lab_record["status"] in ("SUCCESS", "PASSED")

        is_mastered = passed_knowledge and passed_practical and passed_interview and passed_scenario

        gaps = []
        remediation_steps = []
        if not passed_knowledge:
            gaps.append(f"Knowledge score {dims['knowledge']}% is below required threshold ({cls.GATES['knowledge_min']}%)")
            remediation_steps.append("Review deep concept reference and retake module assessment.")
        if not passed_practical:
            gaps.append(f"Practical lab score {dims['hands_on']}% is below required threshold ({cls.GATES['practical_min']}%)")
            remediation_steps.append("Practice execution in Command Playground and complete lab sandbox.")
        if not passed_interview:
            gaps.append(f"Interview readiness {dims['interview']}% is below target ({cls.GATES['interview_min']}%)")
            remediation_steps.append("Engage in a targeted Technical Mock Interview round.")

        return {
            "user_id": user_id,
            "tool_id": tool_id,
            "status": "MASTERED" if is_mastered else "GAP_DETECTED",
            "is_mastered": is_mastered,
            "evaluated_metrics": {
                "knowledge": dims["knowledge"],
                "practical": dims["hands_on"],
                "interview": dims["interview"],
                "scenario_passed": bool(passed_scenario)
            },
            "gaps": gaps,
            "remediation_plan": remediation_steps if not is_mastered else ["Mastery criteria satisfied. Eligible for verified Certificate."]
        }

mastery_engine = DynamicMasteryEngine()
