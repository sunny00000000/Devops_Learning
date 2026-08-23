from __future__ import annotations
import base64, datetime as dt, io, json, pathlib, tempfile, unittest, zipfile
from unittest import mock
import app
import v24_features as v24

PROFILE = {
    "full_name":"Test Candidate","email":"candidate@example.com","phone":"9999999999","location":"Remote",
    "headline":"Junior DevOps Engineer","summary":"DevOps trainee with Linux, Git, Docker, Jenkins, AWS and automation practice.",
    "skills":["Linux","Git","Docker","Jenkins","AWS","Shell scripting"],
    "experience":[{"role":"DevOps Trainee","company":"Training Lab","years":"1","details":"Built CI/CD pipelines and containerized sample applications."}],
    "education":[{"qualification":"BSc","institution":"Example University","year":"2025"}],
    "certifications":[{"name":"AWS Cloud Practitioner Training"}],
    "preferences":{"target_roles":["Junior DevOps Engineer"],"locations":["Remote"],"minimum_match":70},
    "links":{},"master_resume_text":"Linux Git Docker Jenkins AWS Bash CI/CD monitoring", "verified":True,
}
PROJECT = {
    "title":"Docker CI Pipeline","origin":"Independent project","level":"Intermediate","tools":["Docker","Jenkins","Git"],
    "problem_statement":"Manual deployments were slow and inconsistent.","business_requirement":"Automate safe application delivery.",
    "architecture":"Git to Jenkins to Docker deployment.","responsibilities":"Designed and implemented the workflow.",
    "implementation":"Created a Jenkinsfile, Dockerfile, validation stages, immutable image tags and deployment gates.",
    "security_controls":"Used least privilege, no embedded secrets, and image scanning.",
    "testing":"Ran unit tests, container health checks, pipeline validation and deployment smoke tests.",
    "monitoring":"Monitored deployment status and application health endpoints.",
    "troubleshooting":"Reviewed logs and corrected an invalid image tag.","rollback":"Redeployed the last known-good immutable tag.",
    "outcome":"Created repeatable validated delivery with a documented rollback.","evidence":["Pipeline output","Docker digest","Health check output"],"status":"approved",
}
JOB = {"company":"Acme","title":"Junior DevOps Engineer","location":"Remote","description":"We need Linux Docker Jenkins AWS Git CI/CD and Bash skills with 1 year experience. Kubernetes is preferred. The engineer will validate deployments, monitor services and prepare rollback procedures."}

class V24Test(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); root=pathlib.Path(self.tmp.name); db=root/"billinger.db"
        app.DB_PATH=db; app.v2.DB_PATH=db; app.v23.DB_PATH=db; app.v24.DB_PATH=db
        v24.BASE_DIR=root; v24.DATA_DIR=root/"data"; v24.CAREER_DIR=root/"career_data"; v24.PORTFOLIO_DIR=root/"portfolios"; v24.OUTBOX_DIR=root/"mail_outbox"; v24.TOKEN_DIR=root/"tokens"; v24.DB_PATH=db
        v24.STUDENT_SESSIONS.clear(); v24.AUTH_FAILURES.clear(); v24.SEND_EVENTS.clear(); v24.OAUTH_STATES.clear()
        app.init_db(); self.sid=1
        v24.save_candidate_profile(self.sid, PROFILE)
    def tearDown(self): self.tmp.cleanup()
    def job(self): return v24.analyze_manual_job(self.sid, JOB)
    def project(self): return v24.save_portfolio_project(self.sid, PROJECT)

    def test_profile_round_trip_and_truth_flag(self):
        p=v24.get_candidate_profile(self.sid); self.assertTrue(p["verified"]); self.assertIn("Docker",p["skills"])
    def test_job_matching_is_explainable(self):
        j=self.job(); self.assertGreaterEqual(j["match_score"],75); self.assertIn("docker",j["match"]["matched"]); self.assertIn("kubernetes",j["match"]["missing"])
    def test_job_duplicate_prevention(self):
        a=self.job(); b=self.job(); self.assertEqual(a["id"],b["id"]); self.assertEqual(len(v24.list_jobs(self.sid)),1)
    def test_portfolio_scoring_and_secret_block(self):
        good=self.project(); self.assertEqual(good["status"],"portfolio_ready")
        bad=dict(PROJECT); bad["title"]="Leaked Secret Project"; bad["implementation"]="token=supersecretvalue123456"
        result=v24.save_portfolio_project(self.sid,bad); self.assertEqual(result["status"],"needs_correction"); self.assertTrue(result["report"]["secret_findings"])
    def test_portfolio_resume_email_end_to_end(self):
        job=self.job(); self.project(); portfolio=v24.generate_portfolio(self.sid,{"job_id":job["id"]}); resume=v24.generate_tailored_resume(self.sid,job["id"],portfolio["id"])
        draft=v24.create_email_draft(self.sid,{"job_id":job["id"],"resume_variant_id":resume["id"],"portfolio_build_id":portfolio["id"],"recipient":"hr@example.com","subject":"Application for Junior DevOps Engineer","body":"Dear Hiring Manager,\n\nPlease find my verified application documents attached.\n\nRegards,\nTest Candidate"})
        self.assertEqual(len(draft["attachments"]),2); self.assertTrue((v24.BASE_DIR/draft["eml_file"]).is_file())
    def test_resume_does_not_claim_missing_skill(self):
        job=self.job(); self.project(); r=v24.generate_tailored_resume(self.sid,job["id"])
        self.assertIn("kubernetes",r["missing_keywords"]); text=(v24.BASE_DIR/r["text_file"]).read_text().lower(); self.assertNotIn("kubernetes",text)
    def test_email_header_injection_blocked(self):
        with self.assertRaises(ValueError): v24.create_email_draft(self.sid,{"recipient":"hr@example.com\nBcc:evil@example.com","subject":"Hello","body":"A sufficiently long safe email body for testing."})
    def test_send_requires_explicit_confirmation_and_is_idempotent(self):
        job=self.job(); self.project(); resume=v24.generate_tailored_resume(self.sid,job["id"]); draft=v24.create_email_draft(self.sid,{"job_id":job["id"],"resume_variant_id":resume["id"],"recipient":"hr@example.com","subject":"Application for Junior DevOps Engineer","body":"Dear Hiring Manager, this is a verified application. Regards."})
        folder=v24.TOKEN_DIR/f"student_{self.sid}"; folder.mkdir(parents=True); (folder/"gmail_token.bin").write_bytes(v24._protect_bytes(json.dumps({"access_token":"test","expires_at_epoch":9999999999}).encode()))
        with self.assertRaises(PermissionError): v24.send_email_draft(self.sid,draft["id"],"YES",lambda a,b:{"id":"m1"})
        sent=v24.send_email_draft(self.sid,draft["id"],"SEND",lambda a,b:{"id":"m1"}); self.assertTrue(sent["sent"])
        with self.assertRaises(ValueError): v24.send_email_draft(self.sid,draft["id"],"SEND",lambda a,b:{"id":"m2"})
    def test_student_session_prevents_idor(self):
        with app.db_connect() as c:
            ts=app.now_iso(); c.execute("INSERT INTO students(name,email,pin_hash,created_at,last_active) VALUES(?,?,?,?,?)",("Other","",app.hash_pin("1234"),ts,ts)); other=c.execute("SELECT max(id) FROM students").fetchone()[0]
        t1=v24.create_student_session(self.sid,"",app.verify_pin)["token"]; v24.require_student(t1,self.sid)
        with self.assertRaises(PermissionError): v24.require_student(t1,other)
    def test_auth_rate_limit(self):
        with app.db_connect() as c: c.execute("UPDATE students SET pin_hash=? WHERE id=?",(app.hash_pin("9999"),self.sid))
        for _ in range(8):
            with self.assertRaises(PermissionError): v24.create_student_session(self.sid,"bad",app.verify_pin)
        with self.assertRaises(PermissionError): v24.create_student_session(self.sid,"9999",app.verify_pin)
    def test_ssrf_private_addresses_blocked(self):
        for url in ("http://127.0.0.1/x","https://127.0.0.1/x","https://localhost/x","file:///etc/passwd"):
            with self.assertRaises(ValueError): v24._validate_public_url(url)
    def test_job_source_greenhouse_mock(self):
        source=v24.add_job_source(self.sid,"greenhouse","Acme Careers","acme")
        payload={"jobs":[{"id":1,"title":"DevOps Engineer","absolute_url":"","location":{"name":"Remote"},"content":"Linux Docker Jenkins AWS role with monitoring, deployment validation, incident response, security controls and documented rollback responsibilities for production-style services."}]}
        def fetch(url,*args): return json.dumps(payload).encode(),"application/json",url
        out=v24.scan_job_sources(self.sid,source["id"],fetch); self.assertEqual(out["imported"],1)
    def test_job_source_robots_denial(self):
        with mock.patch("v24_features.socket.getaddrinfo", return_value=[(2,1,6,"",("93.184.216.34",443))]):
            source=v24.add_job_source(self.sid,"career_url","Blocked Careers","https://example.com/careers")
        def fetch(url,*args):
            if url.endswith('/robots.txt'): return b"User-agent: *\nDisallow: /careers", "text/plain", url
            return b"<a href='/jobs/1'>DevOps</a>","text/html",url
        out=v24.scan_job_sources(self.sid,source["id"],fetch); self.assertTrue(out["errors"])
    def test_oauth_state_and_token_storage_mock(self):
        client={"installed":{"client_id":"abc.apps.googleusercontent.com","client_secret":"secret-value","auth_uri":"https://accounts.google.com/o/oauth2/v2/auth","token_uri":"https://oauth2.googleapis.com/token"}}
        v24.save_gmail_client(self.sid,"client.json",base64.b64encode(json.dumps(client).encode()).decode())
        start=v24.gmail_auth_start(self.sid,"http://127.0.0.1:8765/oauth/gmail/callback")
        result=v24.gmail_oauth_callback("code",start["state"],lambda u,d:{"access_token":"a","refresh_token":"r","expires_in":3600,"scope":"gmail.send"})
        self.assertTrue(result["connected"]); self.assertTrue(v24.gmail_status(self.sid)["connected"])
        with self.assertRaises(PermissionError): v24.gmail_oauth_callback("code",start["state"],lambda u,d:{})
    def test_research_pack_uses_job_profile_and_portfolio(self):
        job=self.job(); self.project(); r=v24.research_and_prepare_interview(self.sid,job["id"]); self.assertEqual(len(r["likely_rounds"]),9); self.assertGreater(len(r["questions"]),8); self.assertIn("job description", " ".join(r["evidence_basis"]).lower())
    def test_simple_pdf_and_docx_are_valid_signatures(self):
        path=v24.BASE_DIR/"a.pdf"; v24.make_simple_pdf(["Hello"],path); self.assertTrue(path.read_bytes().startswith(b"%PDF"))
        doc=v24.BASE_DIR/"a.docx"; v24.make_docx(["Hello"],doc); self.assertTrue(zipfile.is_zipfile(doc))

if __name__=='__main__': unittest.main()
