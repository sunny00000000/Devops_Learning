import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def request(url, payload=None):
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode('utf-8'))

def main():
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / 'smoke_v2.db')
        port = 8891
        env = dict(os.environ, BILLINGER_DB_PATH=db)
        proc = subprocess.Popen([sys.executable, 'app.py', '--host', '127.0.0.1', '--port', str(port), '--no-browser'], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            base = f'http://127.0.0.1:{port}'
            for _ in range(60):
                try:
                    health = request(base + '/api/health')
                    break
                except Exception:
                    time.sleep(.1)
            else:
                raise RuntimeError('server did not start')
            students = request(base + '/api/students')['students']
            sid = students[0]['id']
            company = request(base + f'/api/v2/company?student_id={sid}')
            ticket = company['recommended_tickets'][0]
            response = ('Assess customer and business impact. Inspect logs and metrics and state a hypothesis. Use permissions and files safely. '
                        'Validate and test with evidence, least privilege security, reviewer approval, stakeholder communication, backup and rollback.')
            reviewed = request(base + '/api/v2/company/ticket/submit', {'student_id':sid,'ticket_id':ticket['id'],'response':response,'standup':'Completed, evidence attached, no blockers, awaiting approval.'})
            lab = request(base + '/api/v2/lab/run', {'student_id':sid,'mode':'simulator','command':'git status'})
            skills = request(base + f'/api/v2/skills?student_id={sid}')
            caps = request(base + '/api/v2/capstones')['capstones']
            coverage = request(base + '/api/v2/coverage')
            resources = request(base + f'/api/resources?tool=linux&student_id={sid}')
            book = request(base + '/api/resource?id=vol-1')
            book_answer = request(base + '/api/resource/ask', {'student_id':sid,'resource_id':'vol-1','question':'How should a company inspect Linux services and logs?'})
            recruit = request(base + '/api/v2/recruitment/start', {'student_id':sid,'target_role':'DevOps Engineer','track':'full-devops','difficulty':'Beginner','resume_text':'Linux Git Docker','job_description':'DevOps Linux Git Docker'})
            assert health['version'] == '2.9.0'
            assert len(company['recommended_tickets']) > 0
            assert 'rubric' in reviewed
            assert lab['exit_code'] == 0 and 'On branch main' in lab['output']
            assert len(skills['tools']) == 21
            assert len(caps) == 21
            assert coverage['summary']['domains'] == 21
            assert coverage['summary']['unique_command_examples'] >= 290
            assert coverage['summary']['learning_resources'] == 69
            assert coverage['summary']['tool_course_books'] == 65
            assert coverage['summary']['program_guides'] == 4
            assert len(coverage['tools']) == 21
            assert resources['count'] >= 1
            assert book['page_count'] >= 40 and len(book['pages']) >= 40
            assert book_answer['sources']
            assert recruit['total_questions'] == 9
            print('V2 SMOKE TEST PASSED')
            print(json.dumps({'version':health['version'],'ticket_score':reviewed['score'],'skill_domains':len(skills['tools']),'capstones':len(caps),'recruitment_rounds':recruit['total_questions']}, indent=2))
        finally:
            proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: proc.kill()

if __name__ == '__main__':
    main()
