"""HTTP end-to-end test for Billinger Bot v2.4 Career & Portfolio Command Centre."""
from __future__ import annotations
import json, os, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def request(url,payload=None,token="",expect_json=True):
    data=None if payload is None else json.dumps(payload).encode()
    headers={"Content-Type":"application/json"}
    if token: headers["X-Student-Token"]=token
    req=urllib.request.Request(url,data=data,headers=headers)
    with urllib.request.urlopen(req,timeout=20) as r:
        raw=r.read(); return json.loads(raw.decode()) if expect_json else (raw,r.headers.get_content_type())

def main():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp); port=8894
        env=dict(os.environ,BILLINGER_DB_PATH=str(root/'db.sqlite'),BILLINGER_CAREER_DIR=str(root/'career'),BILLINGER_PORTFOLIO_DIR=str(root/'portfolios'),BILLINGER_OUTBOX_DIR=str(root/'outbox'),BILLINGER_TOKEN_DIR=str(root/'tokens'),BILLINGER_WORKSPACE_DIR=str(root/'workspaces'),BILLINGER_CERT_DIR=str(root/'certs'),BILLINGER_BACKUP_DIR=str(root/'backups'),BILLINGER_IMPORT_DIR=str(root/'imports'),BILLINGER_UPDATE_DIR=str(root/'updates'))
        proc=subprocess.Popen([sys.executable,'app.py','--host','127.0.0.1','--port',str(port),'--no-browser'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            base=f'http://127.0.0.1:{port}'
            for _ in range(80):
                try: health=request(base+'/api/health');break
                except Exception: time.sleep(.1)
            else: raise RuntimeError('server did not start')
            sid=request(base+'/api/students')['students'][0]['id']
            session=request(base+'/api/v4/student/session',{'student_id':sid,'pin':''});token=session['token']
            profile=request(base+'/api/v4/profile/save',{'student_id':sid,'full_name':'Test Candidate','email':'candidate@example.com','headline':'Junior DevOps Engineer','summary':'DevOps trainee with Linux Docker Jenkins AWS and Git practice.','skills':['Linux','Docker','Jenkins','AWS','Git'],'experience':[{'role':'Trainee','company':'Training Lab','years':'1','details':'Built CI/CD and container labs.'}],'education':[{'qualification':'BSc','institution':'Example','year':'2025'}],'certifications':[{'name':'AWS training'}],'preferences':{'target_roles':['Junior DevOps Engineer'],'locations':['Remote'],'minimum_match':70},'links':{},'master_resume_text':'Linux Docker Jenkins AWS Git CI/CD Bash','verified':True},token)
            job=request(base+'/api/v4/job/analyze',{'student_id':sid,'company':'Acme','title':'Junior DevOps Engineer','location':'Remote','description':'We need Linux Docker Jenkins AWS Git CI/CD Bash skills with 1 year experience. Kubernetes is preferred. Validate deployments, monitor services and document rollback.'},token)
            project=request(base+'/api/v4/portfolio/project/save',{'student_id':sid,'title':'Docker CI Pipeline','origin':'Independent project','level':'Intermediate','tools':['Docker','Jenkins','Git'],'problem_statement':'Manual deployments were inconsistent.','business_requirement':'Automate safe delivery.','architecture':'Git to Jenkins to Docker.','responsibilities':'Designed the workflow.','implementation':'Created Jenkinsfile Dockerfile tests immutable tags and deployment gates.','security_controls':'Least privilege and image scanning with no embedded secrets.','testing':'Unit tests health checks pipeline validation and smoke tests.','monitoring':'Health endpoints and deployment status.','troubleshooting':'Fixed invalid image tags from logs.','rollback':'Redeployed previous immutable image.','outcome':'Repeatable validated delivery.','evidence':['Pipeline output','Image digest','Health output'],'status':'approved'},token)
            portfolio=request(base+'/api/v4/portfolio/build',{'student_id':sid,'job_id':job['id'],'template':'DevOps Command Centre'},token)
            resume=request(base+'/api/v4/resume/generate',{'student_id':sid,'job_id':job['id'],'portfolio_build_id':portfolio['id']},token)
            draft=request(base+'/api/v4/email/draft',{'student_id':sid,'job_id':job['id'],'resume_variant_id':resume['id'],'portfolio_build_id':portfolio['id'],'recipient':'hr@example.com','subject':'Application for Junior DevOps Engineer','body':'Dear Hiring Manager,\n\nPlease find my verified application documents attached.\n\nRegards,\nTest Candidate'},token)
            research=request(base+'/api/v4/research',{'student_id':sid,'job_id':job['id'],'company_url':''},token)
            dashboard=request(base+f'/api/v4/career/dashboard?student_id={sid}',token=token)
            pdf,_=request(base+f"{resume['links']['pdf']}&student_id={sid}",token=token,expect_json=False)
            site,_=request(base+f"{portfolio['links']['website']}&student_id={sid}",token=token,expect_json=False)
            eml,_=request(base+f"{draft['download']}&student_id={sid}",token=token,expect_json=False)
            assert health['version']=='2.9.0';assert profile['verified'];assert job['match_score']>=70;assert project['status']=='portfolio_ready';assert len(draft['attachments'])==2;assert len(research['likely_rounds'])==9;assert dashboard['summary']['recommended']==1;assert pdf.startswith(b'%PDF');assert b'<!doctype html>' in site.lower();assert b'Subject:' in eml
            print('V4 CAREER & PORTFOLIO HTTP SMOKE TEST PASSED')
            print(json.dumps({'version':health['version'],'job_match':job['match_score'],'portfolio_score':project['score'],'resume':resume['id'],'draft':draft['id'],'interview_rounds':len(research['likely_rounds'])},indent=2))
        finally:
            proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: proc.kill()
if __name__=='__main__':main()
