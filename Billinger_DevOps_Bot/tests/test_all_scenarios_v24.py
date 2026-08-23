from __future__ import annotations

import pathlib
import tempfile
import unittest

import app
import v2_features as v2
import v23_features as v23
import v24_features as v24


class AllScenarioCoverageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); root=pathlib.Path(self.tmp.name); db=root/'db.sqlite'
        app.DB_PATH=db;app.v2.DB_PATH=db;app.v23.DB_PATH=db;app.v24.DB_PATH=db
        v2.DB_PATH=db;v2.LAB_DIR=root/'labs';v23.DB_PATH=db;v24.DB_PATH=db
        v23.WORKSPACE_DIR=root/'workspaces';v23.CERT_DIR=root/'certs';v23.BACKUP_DIR=root/'backups';v23.IMPORT_DIR=root/'imports';v23.UPDATE_DIR=root/'updates'
        v24.BASE_DIR=root;v24.DATA_DIR=root/'data';v24.CAREER_DIR=root/'career';v24.PORTFOLIO_DIR=root/'portfolios';v24.OUTBOX_DIR=root/'outbox';v24.TOKEN_DIR=root/'tokens'
        app.init_db();self.sid=1
    def tearDown(self):self.tmp.cleanup()

    def test_every_learning_domain_and_company_scenario_is_executable(self):
        tools=app.CATALOG['tools'];self.assertEqual(len(tools),21)
        tool_slugs={t['slug'] for t in tools}
        for tool in tools:
            self.assertEqual(len(tool['levels']),4,tool['slug'])
            self.assertEqual(sum(len(level['lessons']) for level in tool['levels']),16,tool['slug'])
            self.assertEqual(sum(len(level['labs']) for level in tool['levels']),4,tool['slug'])
            for level in tool['levels']:
                self.assertTrue(level['company_workflow']);self.assertTrue(level['mastery_gate'])
                for lesson in level['lessons']:
                    self.assertTrue(lesson['title']);self.assertTrue(lesson['company_use']);self.assertTrue(lesson['example'])
                for lab in level['labs']:
                    self.assertTrue(lab['scenario']);self.assertTrue(lab['deliverables']);self.assertTrue(lab['acceptance_criteria'])
        self.assertEqual({x['tool'] for x in v2.COMPANY['tickets']},tool_slugs)
        self.assertEqual({x['tool'] for x in v2.COMPANY['incidents']},tool_slugs)
        self.assertEqual({x['tool'] for x in v2.COMPANY['capstones']},tool_slugs)

        for ticket in v2.COMPANY['tickets']:
            response=("Business impact assessment. Inspect logs metrics configuration and evidence. State a hypothesis. "
                      + " ".join(ticket['keywords'])
                      + " Validate safely with tests, least privilege security, approval, communication, backup, rollback, recovery and reviewer handoff.")
            result=v2.submit_ticket(self.sid,ticket['id'],response,"Completed with evidence; validation passed; rollback ready; reviewer approval requested.")
            self.assertIn('rubric',result,ticket['id']);self.assertGreater(result['score'],0,ticket['id'])

        for incident in v2.COMPANY['incidents']:
            response=("Acknowledge severity and customer impact. Preserve timeline and collect logs metrics traces and evidence. "
                      + " ".join(incident['keywords'])
                      + " Form and test a hypothesis, mitigate safely, validate service health and SLO, communicate status, rollback if needed, and complete a postmortem.")
            result=v2.submit_incident(self.sid,incident['id'],response)
            self.assertIn('rubric',result,incident['id']);self.assertGreater(result['score'],0,incident['id'])

        for capstone in v2.COMPANY['capstones']:
            submission=("Architecture assumptions trade-offs business outcomes and implementation plan. " + " ".join(capstone['keywords']) + " "
                        "Automation infrastructure as code CI/CD security least privilege compliance policy testing unit integration smoke evidence. "
                        "Observability metrics logs traces alerts SLO error budget. Rollback backup restore disaster recovery cost governance documentation and operational handover. ")*3
            result=v2.submit_capstone(self.sid,capstone['id'],submission)
            self.assertIn('rubric',result,capstone['id']);self.assertGreater(result['score'],0,capstone['id'])

        with app.db_connect() as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM company_ticket_runs').fetchone()[0],84)
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM incident_runs').fetchone()[0],21)
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM capstone_runs').fetchone()[0],21)


if __name__=='__main__':unittest.main()
