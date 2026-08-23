import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LearningResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()
        os.environ['BILLINGER_DB_PATH'] = str(Path(cls.tempdir.name) / 'resource_test.db')
        spec = importlib.util.spec_from_file_location('billinger_resource_test', ROOT / 'app.py')
        cls.app = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(cls.app)
        cls.app.v2.DB_PATH = Path(os.environ['BILLINGER_DB_PATH']).resolve()
        cls.app.init_db()
        with cls.app.db_connect() as conn:
            cls.student_id = conn.execute('SELECT id FROM students ORDER BY id LIMIT 1').fetchone()[0]

    @classmethod
    def tearDownClass(cls):
        cls.tempdir.cleanup()
        os.environ.pop('BILLINGER_DB_PATH', None)

    def test_library_index_and_domain_mapping(self):
        self.assertEqual(len(self.app.RESOURCE_MAP), 69)
        linux = self.app.list_learning_resources('linux', self.student_id)
        self.assertGreaterEqual(linux['count'], 1)
        self.assertTrue(any(r['volume'] == '1' for r in linux['resources']))
        system_design = self.app.list_learning_resources('system-design', self.student_id)
        self.assertLess(system_design['count'], 20)
        self.assertFalse(any(r['id'] in {'vol-9c','vol-9d'} for r in linux['resources']))
        git = self.app.list_learning_resources('git', self.student_id)
        self.assertEqual([r['id'] for r in git['resources']], ['vol-3'])
        cicd = self.app.list_learning_resources('cicd', self.student_id)
        self.assertEqual({r['id'] for r in cicd['resources']}, {'vol-10a','vol-10f'})
        program = self.app.list_learning_resources('', self.student_id, 'program')
        self.assertEqual(program['count'], 4)

    def test_read_resource_has_pages_and_files(self):
        resource = self.app.read_learning_resource('vol-1')
        self.assertGreaterEqual(resource['page_count'], 40)
        self.assertGreaterEqual(len(resource['pages']), 40)
        self.assertTrue((ROOT / 'learning_resources' / self.app.RESOURCE_MAP['vol-1']['pdf_file']).is_file())
        self.assertTrue((ROOT / 'learning_resources' / self.app.RESOURCE_MAP['vol-1']['docx_file']).is_file())

    def test_source_grounded_question(self):
        result = self.app.answer_from_learning_resource('vol-1', 'How do companies manage Linux services and inspect logs?')
        self.assertIn(result['mode'], {'extractive', 'local_ai'})
        self.assertGreaterEqual(len(result['sources']), 1)
        self.assertIn('Page', result['answer'])

    def test_resource_progress(self):
        self.app.progress_upsert(self.student_id, 'resource', 'vol-1', 'completed', 100)
        listing = self.app.list_learning_resources('linux', self.student_id)
        item = next(r for r in listing['resources'] if r['id'] == 'vol-1')
        self.assertEqual(item['status'], 'completed')


if __name__ == '__main__':
    unittest.main(verbosity=2)
