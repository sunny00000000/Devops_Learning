"""
Unit tests for Learning Core, Catalog, Playground, Twin, and Dynamic Mastery.
"""
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from learning.catalog import catalog
from learning.playground import playground
from learning.twin import learning_twin
from learning.mastery import mastery_engine
from learning.coverage import coverage_auditor

class TestLearning(unittest.TestCase):
    def test_catalog_domains(self):
        domains = catalog.get_domains()
        self.assertEqual(len(domains), 12, "DevOps catalog must contain exactly 12 core domains")
        domain_names = [d["name"] for d in domains]
        self.assertIn("Linux SysAdmin & Kernel", domain_names)
        self.assertIn("Kubernetes Orchestration & Helm", domain_names)
        self.assertIn("Terraform & OpenTofu IaC", domain_names)
        self.assertIn("Docker & Containers", domain_names)

    def test_command_metadata_richness(self):
        cmds = catalog.get_all_commands()
        self.assertGreater(len(cmds), 30, "Catalog should have comprehensive commands")
        for cmd in cmds[:10]:
            self.assertIn("command", cmd)
            self.assertIn("purpose", cmd)
            self.assertIn("syntax", cmd)
            self.assertIn("options", cmd)
            self.assertIn("company_usage", cmd)
            self.assertIn("production_usage", cmd)

    def test_command_playground_tracking(self):
        user_id = "test_learner_1"
        res = playground.practice_command(user_id, "ls -la", execute_in_sandbox=True)
        self.assertIn(res["status"], ["SUCCESS", "SIMULATED"])
        
        stats = playground.get_command_stats(user_id)
        self.assertGreaterEqual(stats["total_attempted"], 1)

    def test_learning_twin_dimensions(self):
        user_id = "test_learner_twin"
        profile = learning_twin.get_learner_profile(user_id)
        self.assertIn("current_level", profile)
        self.assertIn("overall_job_readiness", profile)
        self.assertIn("dimensions", profile)
        
        dims = profile["dimensions"]
        for d in ["knowledge", "hands_on", "troubleshooting", "production", "interview", "communication", "portfolio", "job_readiness"]:
            self.assertIn(d, dims)
            self.assertGreaterEqual(dims[d], 0.0)
            self.assertLessEqual(dims[d], 100.0)

    def test_dynamic_mastery_gates(self):
        user_id = "test_learner_mastery"
        res = mastery_engine.evaluate_mastery(user_id, "linux")
        self.assertIn("status", res)
        self.assertIn("is_mastered", res)
        self.assertIn("evaluated_metrics", res)

    def test_coverage_auditor(self):
        cov = coverage_auditor.audit_coverage()
        self.assertGreater(cov["total_tools_audited"], 0)
        self.assertGreaterEqual(cov["average_system_coverage"], 80.0)
