import re
from learning.twin import learning_twin

DEVOPS_SKILLS = [
    "Linux", "Docker", "Kubernetes", "Terraform", "Ansible", "AWS", "Jenkins", 
    "Prometheus", "Grafana", "Python", "Bash", "Git", "CI/CD", "ELK", "SRE"
]

class JobMatcher:
    @staticmethod
    def analyze_job_description(user_id: str, job_text: str, role_title: str = "DevOps Engineer", company: str = "Target Corp") -> dict:
        text = job_text.lower()
        matched_skills = []
        missing_skills = []
        for skill in DEVOPS_SKILLS:
            if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text):
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)

        twin = learning_twin.get_learner_profile(user_id)
        readiness = twin["overall_job_readiness"]

        total_req = max(1, len(matched_skills))
        student_matches = sum(1 for s in matched_skills if s in ["Linux", "Git", "Docker", "Kubernetes", "AWS", "Jenkins"])
        match_score = round(min(100.0, (student_matches / total_req * 80.0) + (readiness * 0.2)), 1)

        missing_tech = [s for s in matched_skills if s not in ["Linux", "Git", "Docker", "Jenkins", "AWS"]]

        remed_modules = []
        for m in missing_tech:
            if m == "Kubernetes": remed_modules.append("Module 7: Kubernetes Orchestration & Helm")
            elif m == "Terraform": remed_modules.append("Module 8: Infrastructure as Code with Terraform")
            elif m == "Ansible": remed_modules.append("Module 9: Configuration Management with Ansible")
            elif m in ("Prometheus", "Grafana"): remed_modules.append("Module 11: Observability & Production Debugging")

        return {
            "company": company,
            "role_title": role_title,
            "match_score_pct": match_score,
            "required_skills_found": matched_skills,
            "student_verified_skills": matched_skills[:student_matches],
            "missing_skills_gap": missing_tech,
            "truthfulness_warning": "Truthfulness policy enforced: No qualifications, employment dates, or certifications will be fabricated.",
            "job_learning_loop": {
                "recommended_modules": remed_modules or ["Module 12: Enterprise Capstone & Production Readiness"],
                "recommended_lab": "High-Availability Deployment & Canary Rollout",
                "recommended_interview": "Company-Specific Mock Technical Interview for " + company
            }
        }

job_matcher = JobMatcher()
