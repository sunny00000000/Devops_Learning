import base64
import importlib
import io
import os
import tempfile
import unittest
import zipfile
from pathlib import Path


class V23FeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        os.environ['BILLINGER_DB_PATH'] = str(Path(cls.tmp.name) / 'v23_test.db')
        import app
        import v23_features
        cls.app = importlib.reload(app)
        cls.v23 = importlib.reload(v23_features)
        root = Path(cls.tmp.name)
        cls.v23.WORKSPACE_DIR = root / 'workspaces'
        cls.v23.CERT_DIR = root / 'certificates'
        cls.v23.BACKUP_DIR = root / 'backups'
        cls.v23.IMPORT_DIR = root / 'imports'
        cls.v23.UPDATE_DIR = root / 'updates'
        cls.app.init_db()
        with cls.app.db_connect() as conn:
            cls.student_id = conn.execute('SELECT id FROM students ORDER BY id LIMIT 1').fetchone()[0]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()
        os.environ.pop('BILLINGER_DB_PATH', None)

    def test_admin_batch_assignment_and_student_hub(self):
        auth = self.v23.admin_setup('2468', 'Trainer', 'Billinger Test Academy')
        self.assertTrue(auth['authenticated'])
        batch = self.v23.save_batch({'name':'Batch A','description':'DevOps beginners','target_role':'Junior DevOps Engineer','level':'Beginner'})
        self.v23.assign_batch_member(batch['id'], self.student_id, True)
        self.v23.create_assignment({'batch_id':batch['id'],'title':'Linux permissions lab','item_type':'practice','due_date':'2026-08-10','instructions':'Submit evidence and rollback.'})
        self.v23.create_announcement({'batch_id':batch['id'],'title':'Welcome','message':'Complete the daily learning plan.'})
        hub = self.v23.student_hub(self.student_id)
        self.assertEqual(len(hub['batches']), 1)
        self.assertEqual(len(hub['assignments']), 1)
        self.assertEqual(len(hub['announcements']), 1)
        self.assertEqual(len(hub['roadmap']['items']), 21)
        self.assertEqual(len(hub['today']['items']), 5)

    def test_practical_exam_workspace_certificate_and_backup(self):
        templates = self.v23.practical_exam_templates('linux','Beginner')
        self.assertEqual(len(templates), 1)
        run = self.v23.start_practical_exam(self.student_id, templates[0]['exam_code'])
        response = ('I inspect logs and permissions, form a root cause hypothesis, and capture evidence. '
                    'I implement the command safely, validate with test output and health checks, apply least privilege security, '
                    'prepare backup and rollback steps, and send a stakeholder status update. ') * 3
        result = self.v23.submit_practical_exam(run['run_id'], self.student_id, response)
        self.assertGreater(result['score'], 60)
        saved = self.v23.save_workspace_file(self.student_id, 'linux/evidence.md', response, 'linux')
        self.assertTrue(saved['saved'])
        self.assertEqual(len(self.v23.list_workspace(self.student_id)['files']), 1)
        cert = self.v23.issue_certificate(self.student_id, 'Practical Excellence', 'Linux Beginner', result['score'])
        self.assertTrue(self.v23.verify_certificate(cert['verification_code'])['valid'])
        backup = self.v23.create_backup()
        self.assertTrue((self.v23.BACKUP_DIR / backup['file_name']).is_file())

    def test_verified_import_is_staged_not_auto_published(self):
        document_xml = b'<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Ansible Playbook Inventory Roles and Automation</w:t></w:r></w:p></w:body></w:document>'
        docx = io.BytesIO()
        with zipfile.ZipFile(docx, 'w') as zf:
            zf.writestr('word/document.xml', document_xml)
        outer = io.BytesIO()
        with zipfile.ZipFile(outer, 'w') as zf:
            zf.writestr('Ansible_Enterprise.docx', docx.getvalue())
            zf.writestr('Ansible_Enterprise.pdf', b'%PDF-1.4\n% test')
        staged = self.v23.stage_content_import('learning.zip', base64.b64encode(outer.getvalue()).decode())
        self.assertEqual(len(staged['documents']), 1)
        self.assertEqual(staged['documents'][0]['status'], 'awaiting_admin_approval')
        self.assertEqual(staged['documents'][0]['recommended_tool'], 'ansible')

    def test_update_package_validation(self):
        package = io.BytesIO()
        with zipfile.ZipFile(package, 'w') as zf:
            zf.writestr('Billinger_DevOps_Bot/VERSION.txt', '9.9.9')
            zf.writestr('Billinger_DevOps_Bot/app.py', '# test')
            zf.writestr('Billinger_DevOps_Bot/static/index.html', '<html></html>')
        staged = self.v23.stage_offline_update('update.zip', base64.b64encode(package.getvalue()).decode())
        self.assertEqual(staged['detected_version'], '9.9.9')
        self.assertTrue(staged['staged'])


if __name__ == '__main__':
    unittest.main()
