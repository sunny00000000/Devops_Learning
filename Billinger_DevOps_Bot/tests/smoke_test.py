"""Starts the local server on a test port and validates critical HTTP workflows."""
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = 8876
BASE = f'http://127.0.0.1:{PORT}'


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=8) as response:
        return json.load(response)


def post(path, data):
    request = urllib.request.Request(
        BASE + path,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        return json.load(response)


def main():
    with tempfile.TemporaryDirectory() as temp:
        env = dict(os.environ)
        env['BILLINGER_DB_PATH'] = str(Path(temp) / 'smoke.db')
        process = subprocess.Popen(
            [sys.executable, 'app.py', '--no-browser', '--port', str(PORT)],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            for _ in range(40):
                try:
                    if get('/api/health')['status'] == 'ok':
                        break
                except Exception:
                    time.sleep(0.2)
            else:
                raise RuntimeError('Server did not start')

            students = get('/api/students')['students']
            assert students, 'No default student created'
            sid = students[0]['id']
            catalog = get('/api/catalog')
            assert len(catalog['tools']) == 21

            test = post('/api/test/start', {
                'student_id': sid, 'tool': 'linux', 'difficulty': 'Beginner', 'count': 5, 'include_online': False
            })
            assert len(test['questions']) == 5
            answers = []
            for q in test['questions']:
                answer = 0 if q['type'] == 'mcq' else 'Validate evidence test risk rollback recovery permissions processes logs.'
                answers.append({'id': q['id'], 'answer': answer})
            result = post('/api/test/submit', {'student_id': sid, 'session_id': test['session_id'], 'answers': answers})
            assert 'score' in result and 'passed' in result

            imported = post('/api/resume/import', {
                'filename': 'existing_resume.txt',
                'content_base64': base64.b64encode(b'DevOps Candidate\nLinux Docker Git automation').decode('ascii')
            })
            assert 'Linux Docker' in imported['text']

            resume = post('/api/resume/generate', {
                'student_id': sid, 'name': 'Smoke Test', 'target_title': 'DevOps Engineer',
                'contact': 'smoke@example.com', 'summary': 'Linux and Docker learner',
                'skills': 'Linux Docker Git', 'education': 'Degree', 'projects': 'CI project',
                'job_description': 'Linux Docker Git CI', 'experience': []
            })
            assert resume['id'].startswith('resume_')
            print('SMOKE TEST PASSED')
            print(json.dumps({'tools': len(catalog['tools']), 'test_score': result['score'], 'resume_match': resume['match_score']}, indent=2))
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == '__main__':
    main()
