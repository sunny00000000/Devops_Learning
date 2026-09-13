"""
Billinger v2.4 Features Layer: Career Intelligence, Job Matcher & ATS Resume Studio
Directly integrates with career.matcher, resume.engine, and portfolio.engine.
"""
from career.matcher import job_matcher, JobMatcher
from resume.engine import resume_engine, ResumeEngine
from portfolio.engine import portfolio_engine, PortfolioEngine

class CareerDashboard:
    """Matches candidate skills with real-world DevOps job roles"""
    @classmethod
    def match_skills(cls, candidate_skills):
        return job_matcher.match_skills(candidate_skills)

class ATSResumeEngine:
    """Analyzes resumes for ATS optimization and honest evidence tailoring"""
    @staticmethod
    def calculate_ats_score(resume_text, target_role="DevOps Engineer"):
        return resume_engine.analyze_ats_score(resume_text, target_role)

career_dashboard = CareerDashboard()
