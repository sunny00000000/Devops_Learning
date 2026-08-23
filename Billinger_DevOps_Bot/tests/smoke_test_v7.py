"""HTTP smoke and authorization test for Billinger Bot v2.7 final readiness."""
from __future__ import annotations
import json, os, subprocess, sys, tempfile, time, urllib.error, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def request(url,payload=None,admin='',student='',expected=200):
    data=None if payload is None else json.dumps(payload).encode()
    headers={'Content-Type':'application/json','Origin':url.split('/api/')[0]}
    if admin: headers['X-Admin-Token']=admin
    if student: headers['X-Student-Token']=student
    req=urllib.request.Request(url,data=data,headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            assert r.status==expected,(r.status,expected); return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code!=expected: raise
        return json.loads(e.read().decode())

def main():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);port=8897
        env=dict(os.environ,BILLINGER_DB_PATH=str(root/'db.sqlite'),BILLINGER_WORKSPACE_DIR=str(root/'workspaces'),BILLINGER_CERT_DIR=str(root/'certs'),BILLINGER_BACKUP_DIR=str(root/'backups'),BILLINGER_IMPORT_DIR=str(root/'imports'),BILLINGER_UPDATE_DIR=str(root/'updates'),BILLINGER_CAREER_DIR=str(root/'career'),BILLINGER_PORTFOLIO_DIR=str(root/'portfolios'),BILLINGER_OUTBOX_DIR=str(root/'outbox'),BILLINGER_TOKEN_DIR=str(root/'tokens'))
        proc=subprocess.Popen([sys.executable,'app.py','--host','127.0.0.1','--port',str(port),'--no-browser'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            base=f'http://127.0.0.1:{port}'
            for _ in range(100):
                try: health=request(base+'/api/health');break
                except Exception: time.sleep(.1)
            else: raise RuntimeError('server did not start')
            assert health['version']=='2.9.0'
            sid=request(base+'/api/students')['students'][0]['id']
            st=request(base+'/api/v4/student/session',{'student_id':sid,'pin':''})['token']
            denied=request(base+f'/api/v7/readiness?student_id={sid}',expected=403)
            admin=request(base+'/api/v3/admin/setup',{'pin':'2468','admin_name':'Readiness Admin','institute_name':'Billinger Test'})['token']
            initial=request(base+f'/api/v7/readiness?student_id={sid}',student=st)
            baseline=request(base+'/api/v7/baseline/start',{'student_id':sid},student=st)
            assert baseline['count']==20
            # Wrong answers are acceptable for a baseline; completion, not score, is the setup gate.
            result=request(base+'/api/v7/baseline/submit',{'student_id':sid,'session_id':baseline['session_id'],'answers':[{'id':q['id'],'answer':-1} for q in baseline['questions']]},student=st)
            replay=request(base+'/api/v7/baseline/submit',{'student_id':sid,'session_id':baseline['session_id'],'answers':[]},student=st,expected=400)
            environment=request(base+'/api/v7/environment/check',{'student_id':sid},student=st)
            mastery=request(base+f'/api/v7/mastery?student_id={sid}',student=st)
            fresh=request(base+'/api/v7/freshness')
            backup_denied=request(base+'/api/v7/backup/health',expected=403)
            backup=request(base+'/api/v7/backup/health',admin=admin)
            models_denied=request(base+'/api/v7/ai/models',expected=403)
            fallback=request(base+'/api/v7/ai/fallback/dry-run',{'task':'lesson_tutor','simulated_failures':['gemini']},admin=admin)
            bad_url=request(base+'/api/v7/freshness/save',{'tool':'linux','official_doc_url':'http://invalid.example'},admin=admin,expected=400)
            assert denied['error'] and backup_denied['error'] and models_denied['error']
            assert initial['version']=='2.9.0' and not initial['ready_to_learn']
            assert result['classification'] and replay['error']
            assert environment['tools'] and len(environment['modes'])==5
            assert mastery['total_tools']==21 and len(mastery['tools'][0]['requirements'])==9
            assert len(fresh['items'])==21 and bad_url['error']
            assert backup['status'] in {'missing','healthy','unhealthy'}
            assert fallback['credits_used']==0
            print('V7 FINAL READINESS HTTP SMOKE TEST PASSED')
            print(json.dumps({'version':health['version'],'baseline':result['classification'],'environment_tools':len(environment['tools']),'mastery_tools':mastery['total_tools'],'freshness_tools':len(fresh['items']),'fallback_credit_used':fallback['credits_used']},indent=2))
        finally:
            proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: proc.kill()

if __name__=='__main__': main()
