"""HTTP smoke test for Billinger Bot v2.6 adaptive AI orchestration.
No external provider is contacted; provider calls are covered by mocked unit tests.
"""
from __future__ import annotations
import json, os, subprocess, sys, tempfile, time, urllib.error, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def request(url,payload=None,admin='',student='',expected=200):
    data=None if payload is None else json.dumps(payload).encode()
    headers={'Content-Type':'application/json'}
    if admin: headers['X-Admin-Token']=admin
    if student: headers['X-Student-Token']=student
    req=urllib.request.Request(url,data=data,headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            assert r.status==expected,(r.status,expected);return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code!=expected: raise
        return json.loads(e.read().decode())

def main():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);port=8896
        env=dict(os.environ,BILLINGER_DB_PATH=str(root/'db.sqlite'),BILLINGER_WORKSPACE_DIR=str(root/'workspaces'),BILLINGER_CERT_DIR=str(root/'certs'),BILLINGER_BACKUP_DIR=str(root/'backups'),BILLINGER_IMPORT_DIR=str(root/'imports'),BILLINGER_UPDATE_DIR=str(root/'updates'),BILLINGER_CAREER_DIR=str(root/'career'),BILLINGER_PORTFOLIO_DIR=str(root/'portfolios'),BILLINGER_OUTBOX_DIR=str(root/'outbox'),BILLINGER_TOKEN_DIR=str(root/'tokens'))
        proc=subprocess.Popen([sys.executable,'app.py','--host','127.0.0.1','--port',str(port),'--no-browser'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            base=f'http://127.0.0.1:{port}'
            for _ in range(100):
                try: health=request(base+'/api/health');break
                except Exception: time.sleep(.1)
            else: raise RuntimeError('server did not start')
            sid=request(base+'/api/students')['students'][0]['id']
            st=request(base+'/api/v4/student/session',{'student_id':sid,'pin':''})['token']
            admin=request(base+'/api/v3/admin/setup',{'pin':'2468','admin_name':'AI Admin','institute_name':'Billinger AI Test'})['token']
            denied=request(base+'/api/v6/ai/dashboard',expected=403)
            saved=request(base+'/api/v6/ai/provider/save',{'provider':'gemini','enabled':True,'api_key':'AIzaSmokeTestKey123456789012345','model':'gemini-3.6-flash','daily_limit':7},admin=admin)
            route=request(base+'/api/v6/ai/route/save',{'task':'lesson_tutor','providers':['gemini','openai','openrouter','groq']},admin=admin)
            settings=request(base+'/api/v6/ai/settings/save',{'online_ai_enabled':True,'auto_failover':True,'redact_personal_data':True,'global_daily_request_limit':25},admin=admin)
            dashboard=request(base+'/api/v6/ai/dashboard',admin=admin)
            status=request(base+'/api/v6/ai/status')
            generated=request(base+'/api/v6/ai/questions/generate',{'student_id':sid,'mode':'commands','tool':'linux','difficulty':'Intermediate','count':4},student=st)
            answers=[{'id':q['id'],'answer':'Use logs evidence validation least privilege and rollback before changing production.'} for q in generated['questions']]
            graded=request(base+'/api/v6/ai/questions/submit',{'student_id':sid,'session_id':generated['session_id'],'answers':answers},student=st)
            backup_raw=urllib.request.urlopen(base+'/api/backup').read().decode()
            assert health['version']=='2.9.0'
            assert denied['error']
            assert saved['configured'] and 'AIzaSmoke' not in json.dumps(saved)
            assert route['providers'][0]=='gemini' and settings['auto_failover']
            assert dashboard['secret_storage'] and dashboard['providers'][0].get('key_hint')
            assert 'AIzaSmokeTestKey' not in json.dumps(dashboard)
            assert 'gemini' in status['configured_providers']
            assert len(generated['questions'])==4 and generated['provider']=='local_fallback'
            assert 'ai_providers' not in json.loads(backup_raw)['tables']
            assert graded['score']>=0
            print('V6 ADAPTIVE AI HTTP SMOKE TEST PASSED')
            print(json.dumps({'version':health['version'],'configured':status['configured_providers'],'route':route['providers'],'question_provider':generated['provider'],'score':graded['score']},indent=2))
        finally:
            proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: proc.kill()

if __name__=='__main__': main()
