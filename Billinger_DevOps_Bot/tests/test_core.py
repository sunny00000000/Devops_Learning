import base64
import importlib.util
import io
import zipfile
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()
        os.environ['BILLINGER_DB_PATH'] = str(Path(cls.tempdir.name) / 'test.db')
        spec = importlib.util.spec_from_file_location('billinger_app_test', ROOT / 'app.py')
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

    def test_content_counts(self):
        self.assertEqual(len(self.app.CATALOG['tools']), 21)
        self.assertEqual(len(self.app.LESSON_MAP), 336)
        self.assertEqual(len(self.app.LAB_MAP), 84)
        self.assertGreaterEqual(len(self.app.QUESTION_DATA['questions']), 250)
        self.assertGreaterEqual(len(self.app.INTERVIEW_DATA['questions']), 340)
        self.assertEqual(len(self.app.RESOURCE_MAP), 69)

    def test_open_answer_scoring(self):
        score, matched, missing = self.app.score_open_answer(
            'I will validate with evidence, test safely, monitor the result, and rollback or restore if it fails.',
            ['validate', 'evidence', 'monitor', 'rollback', 'security']
        )
        self.assertGreaterEqual(score, 70)
        self.assertIn('validate', matched)
        self.assertIn('security', missing)

    def test_requested_test_size_is_filled(self):
        session = self.app.build_test(self.student_id, 'linux', 'Beginner', 8, False)
        self.assertEqual(len(session['questions']), 8)
        self.assertEqual(session['pass_mark'], 70)

    def test_progress_and_stats(self):
        lesson_id = next(iter(self.app.LESSON_MAP))
        self.app.progress_upsert(self.student_id, 'lesson', lesson_id, 'completed', 100)
        stats = self.app.student_stats(self.student_id)
        self.assertGreaterEqual(stats['completed_lessons'], 1)


    def test_resume_import_txt_and_docx(self):
        raw = b"Test Candidate\nDevOps Engineer\nLinux Docker Git Terraform"
        txt = self.app.import_resume_file("resume.txt", base64.b64encode(raw).decode())
        self.assertIn("Linux Docker", txt["text"])

        document_xml = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>DOCX Candidate</w:t></w:r></w:p><w:p><w:r><w:t>Kubernetes and CI/CD experience</w:t></w:r></w:p></w:body></w:document>'
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            zf.writestr("word/document.xml", document_xml)
        docx = self.app.import_resume_file("resume.docx", base64.b64encode(buffer.getvalue()).decode())
        self.assertIn("Kubernetes", docx["text"])

    def test_resume_generation(self):
        result = self.app.build_resume(self.student_id, {
            'name': 'Test Candidate',
            'target_title': 'DevOps Engineer',
            'contact': 'test@example.com',
            'summary': 'DevOps learner with Linux automation projects.',
            'skills': 'Linux Git Docker Terraform monitoring',
            'education': 'BSc Computer Science',
            'projects': 'Built a Docker CI pipeline.',
            'job_description': 'Linux Docker Terraform Git monitoring automation',
            'experience': []
        })
        self.assertIn('Test Candidate', result['text'])
        self.assertGreater(result['match_score'], 50)
        self.assertTrue(result['id'].startswith('resume_'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
