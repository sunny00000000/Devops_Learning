import importlib
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

class V2FeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        os.environ['BILLINGER_DB_PATH'] = str(Path(cls.tmp.name) / 'v2_test.db')
        import app
        import v2_features
        cls.app = importlib.reload(app)
        cls.v2 = importlib.reload(v2_features)
        cls.app.init_db()
        with cls.app.db_connect() as conn:
            cls.student_id = conn.execute('SELECT id FROM students ORDER BY id LIMIT 1').fetchone()[0]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_company_catalog_counts(self):
        self.assertEqual(len(self.v2.COMPANY['tickets']), 84)
        self.assertEqual(len(self.v2.COMPANY['incidents']), 21)
        self.assertEqual(len(self.v2.COMPANY['capstones']), 21)

    def test_company_ticket_scoring(self):
        ticket = self.v2.COMPANY['tickets'][0]
        response = ('I will assess business impact, inspect logs and metrics, state a hypothesis, use terminal navigation, files, directories, permissions and ownership. '
                    'I will validate and test the result, collect evidence, use least privilege security, communicate a status update and approval, and define rollback and backup steps for customer safety.')
        result = self.v2.submit_ticket(self.student_id, ticket['id'], response, 'Completed safely; next is reviewer approval; evidence attached; no blocker.')
        self.assertIn('rubric', result)
        self.assertGreater(result['score'], 50)

    def test_incident_scoring(self):
        incident = self.v2.COMPANY['incidents'][0]
        response = ('I acknowledge the incident, assess customer and business impact, preserve a timeline, inspect logs and metrics, and form a hypothesis. '
                    'I validate the hypothesis in staging, apply mitigation with security controls, define rollback and restore triggers, verify the SLO and health checks, communicate status to stakeholders, and write a postmortem with preventive actions and evidence.')
        result = self.v2.submit_incident(self.student_id, incident['id'], response)
        self.assertIn('rubric', result)
        self.assertGreater(result['score'], 60)

    def test_safe_terminal(self):
        result = self.v2.run_lab_command(self.student_id, 'git status', 'simulator')
        self.assertEqual(result['exit_code'], 0)
        self.assertIn('On branch main', result['output'])
        blocked = ['rm -rf .', 'git clean -fdx', 'docker rm abc', 'kubectl delete pod x', 'kubectl get secrets', 'cat /etc/passwd', 'mkdir ../../outside', 'find . -delete', 'python -c print(1)']
        for command in blocked:
            with self.assertRaises(ValueError, msg=command):
                self.v2.run_lab_command(self.student_id, command, 'simulator')

    def test_skill_matrix(self):
        result = self.v2.skill_matrix(self.student_id)
        self.assertEqual(len(result['tools']), 21)
        self.assertIn('overall', result['tools'][0])

    def test_recruitment_journey(self):
        start = self.v2.start_recruitment(self.student_id, 'DevOps Engineer', 'full-devops', 'Beginner', 'Linux Git Docker', 'DevOps role Linux Git Docker')
        session_id = start['session_id']
        result = None
        answer = ('Situation: a service failed. Task: restore it safely. Action: I inspected logs and metrics, validated a hypothesis, used least privilege, tested the change, prepared rollback, communicated customer impact, and recorded evidence. Result: service health and SLO recovered.')
        for _ in range(9):
            result = self.v2.answer_recruitment(session_id, self.student_id, answer)
        self.assertTrue(result['completed'])
        self.assertEqual(len(result['round_scores']), 9)

    def test_capstone_review(self):
        cap = self.v2.COMPANY['capstones'][0]
        submission = ('Architecture: layered platform design with documented assumptions and trade-offs. ' * 4 +
                      'Implementation uses automation, pipeline validation, infrastructure as code, least privilege security, policy and audit governance. ' * 4 +
                      'Testing includes unit, integration, health checks and evidence. Observability includes metrics, logs, traces, SLO and alerts. ' * 4 +
                      'Recovery includes rollback, backup, restore and disaster recovery. Cost controls, documentation, approval and operational handover are included. ' * 4)
        result = self.v2.submit_capstone(self.student_id, cap['id'], submission)
        self.assertIn('architecture', result['rubric'])
        self.assertGreater(result['score'], 60)


    def test_coverage_catalog_and_sidebar_scroll(self):
        coverage = self.app.build_coverage_catalog()
        self.assertEqual(coverage['summary']['domains'], 21)
        self.assertEqual(coverage['summary']['lessons'], 336)
        self.assertGreaterEqual(coverage['summary']['unique_command_examples'], 290)
        self.assertEqual(len(coverage['tools']), 21)
        css = (Path(self.app.STATIC_DIR) / 'styles.css').read_text(encoding='utf-8')
        html = (Path(self.app.STATIC_DIR) / 'index.html').read_text(encoding='utf-8')
        self.assertIn('overflow-y:auto', css)
        self.assertIn('page-coverage', html)

    def test_settings_reject_external_ai(self):
        with self.assertRaises(ValueError):
            self.v2.save_settings({'ai_endpoint': 'https://example.com/v1/chat/completions'})

if __name__ == '__main__':
    unittest.main()
