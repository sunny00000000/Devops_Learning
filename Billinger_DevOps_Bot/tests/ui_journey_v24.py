"""Browser-rendered UI user journey using mocked localhost APIs.

The sandbox Chromium policy blocks navigation to localhost, so backend HTTP is
validated separately by smoke/security tests. This test renders the real HTML,
CSS and JavaScript in Chromium and drives the user workflows against a strict
in-browser API mock.
"""
from __future__ import annotations

import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

MOCK_SCRIPT = r"""
window.__mockData = {
 profile:{full_name:'',email:'',phone:'',location:'',headline:'',summary:'',skills:[],experience:[],education:[],certifications:[],preferences:{minimum_match:75,target_roles:[],locations:[]},links:{},master_resume_text:'',verified:false},
 jobs:[],projects:[],portfolio_builds:[],resume_variants:[],email_drafts:[],applications:[],sources:[]
};
window.open = () => ({close(){}});
window.URL.createObjectURL = () => 'blob:mock';
window.URL.revokeObjectURL = () => {};
const response = (data,status=200,type='application/json') => new Response(type.includes('json')?JSON.stringify(data):data,{status,headers:{'Content-Type':type}});
window.fetch = async (input, options={}) => {
 const url=String(input), method=(options.method||'GET').toUpperCase(), body=options.body?JSON.parse(options.body):{};
 const d=window.__mockData;
 if(url==='/api/catalog') return response({tools:[{slug:'linux',name:'Linux Administration',icon:'🐧',category:'Foundation',description:'Linux systems and operations',levels:[]} ]});
 if(url.startsWith('/api/tool?')) return response({slug:'linux',name:'Linux Administration',levels:[{name:'Beginner',labs:[{id:'lab1',title:'Linux lab',scenario:'Inspect a service safely',difficulty:'Beginner',deliverables:['Evidence'],acceptance_criteria:['Validate']}]}]});
 if(url==='/api/students') return response({students:[{id:1,name:'Student 1',email:'',pin_protected:false}]});
 if(url==='/api/v4/student/session') return response({token:'student-token'});
 if(url.startsWith('/api/progress?')) return response({progress:[],stats:{completed_lessons:0,total_lessons:336,passed_labs:0,total_labs:84,average_score:0,passed_interviews:0,passed_tests:0,resumes:0,lesson_percent:0}});
 if(url==='/api/v3/status') return response({admin:{configured:false,admin_name:'Admin',institute_name:'Billinger'},requirements:{}});
 if(url.startsWith('/api/v4/career/dashboard?')) return response({profile:d.profile,jobs:d.jobs,projects:d.projects,portfolio_builds:d.portfolio_builds,resume_variants:d.resume_variants,email_drafts:d.email_drafts,applications:d.applications,sources:d.sources,gmail:{connected:false,client_configured:false},summary:{jobs:d.jobs.length,recommended:d.jobs.filter(x=>x.match_score>=75).length,applications:d.applications.length}});
 if(url==='/api/v4/profile/save') {d.profile={...body,preferences:body.preferences||{},links:body.links||{}};return response(d.profile)}
 if(url==='/api/v4/job/analyze') {const j={id:'job1',company:body.company,title:body.title,location:body.location,url:body.url||'',status:'recommended',match_score:92,description:body.description,match:{recommendation:'Apply — strong fit',matched:['linux','docker','jenkins','aws','git','ci/cd'],missing:['kubernetes'],required_skills:['linux','docker','jenkins','aws'],components:{skills:95,experience:80,role:95},truth_notice:'Missing skills are not added to the resume.'}};d.jobs=[j];return response(j)}
 if(url==='/api/v4/portfolio/project/save') {const p={...body,id:'proj1',score:88,status:'portfolio_ready',report:{secret_findings:[],dimensions:{technical_correctness:90}},repository_url:body.repository_url||''};d.projects=[p];return response(p)}
 if(url==='/api/v4/portfolio/build') {const b={id:'portfolio1',title:'Browser Test Portfolio',created_at:new Date().toISOString(),selected_projects:['proj1'],links:{website:'/api/v4/portfolio/file?id=portfolio1&format=html',pdf:'/api/v4/portfolio/file?id=portfolio1&format=pdf',zip:'/api/v4/portfolio/file?id=portfolio1&format=zip'}};d.portfolio_builds=[b];return response(b)}
 if(url==='/api/v4/resume/generate') {const r={id:'resume1',title:'Browser Test — Junior DevOps Engineer',created_at:new Date().toISOString(),match_score:91,included_keywords:['linux','docker','jenkins','aws'],missing_keywords:['kubernetes'],links:{pdf:'/api/v4/resume/file?id=resume1&format=pdf',docx:'/api/v4/resume/file?id=resume1&format=docx'}};d.resume_variants=[r];return response(r)}
 if(url==='/api/v4/email/draft') {const e={id:'draft1',recipient:body.recipient,subject:body.subject,body:body.body,status:'draft',attachments:['resume.pdf','portfolio.pdf'],download:'/api/v4/email/file?id=draft1'};d.email_drafts=[e];return response(e)}
 if(url==='/api/v4/research') return response({warning:'Preparation is inferred from verified sources.',evidence_basis:['job description','verified resume','portfolio'],likely_rounds:['Screening','HR','Linux','DevOps','Troubleshooting','Scripting','System design','Managerial','Final HR'],questions:['Explain your pipeline','How do you rollback?'],recruitment_payload:{target_role:'Junior DevOps Engineer',track:'full-devops',difficulty:'Intermediate',resume_text:'verified resume',job_description:'job'}});
 if(url.startsWith('/api/v4/portfolio/file')) return response('<!doctype html><h1>Portfolio</h1>',200,'text/html');
 if(url.startsWith('/api/v4/resume/file')) return response('%PDF-mock',200,'application/pdf');
 if(url.startsWith('/api/v4/email/file')) return response('Subject: mock',200,'message/rfc822');
 return response({error:'Unhandled mock endpoint: '+method+' '+url},404);
};
"""


def main() -> None:
    html_text=(ROOT/'static/index.html').read_text(encoding='utf-8')
    html_text=html_text.replace('<link rel="stylesheet" href="/styles.css">','').replace('<link rel="stylesheet" href="/studio.css">','').replace('<script src="/app.js"></script>','')
    css=(ROOT/'static/styles.css').read_text(encoding='utf-8')+'\n'+(ROOT/'static/studio.css').read_text(encoding='utf-8')
    js=(ROOT/'static/app.js').read_text(encoding='utf-8')
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={"width":1366,"height":768})
        page.on('pageerror',lambda e:errors.append(f'pageerror:{e}'))
        page.on('console',lambda m:errors.append(f'console:{m.type}:{m.text}') if m.type=='error' else None)
        page.set_content(html_text,wait_until='domcontentloaded')
        page.add_style_tag(content=css)
        page.add_script_tag(content=MOCK_SCRIPT)
        page.add_script_tag(content=js)
        page.evaluate('init()')
        page.wait_for_selector('#page-dashboard.active')
        page.wait_for_timeout(300)

        sidebar=page.locator('#sidebar')
        metrics=sidebar.evaluate("el=>({clientHeight:el.clientHeight,scrollHeight:el.scrollHeight,overflow:getComputedStyle(el).overflowY})")
        assert metrics['scrollHeight']>metrics['clientHeight'] and metrics['overflow'] in {'auto','scroll'},metrics
        sidebar.evaluate('el=>el.scrollTop=el.scrollHeight')
        assert sidebar.evaluate('el=>el.scrollTop')>0

        page.evaluate("document.querySelector('.nav-item[data-page=\"career\"]').click()");page.wait_for_selector('#page-career.active')
        fills={
          '#candidateName':'Browser Test Candidate','#candidateEmail':'browser@example.com','#candidateLocation':'Remote',
          '#candidateHeadline':'Junior DevOps Engineer','#candidateSummary':'Verified DevOps trainee with Linux Git Docker Jenkins AWS CI/CD and monitoring practice.',
          '#candidateSkills':'Linux, Git, Docker, Jenkins, AWS, Bash, CI/CD, Monitoring',
          '#candidateExperience':'DevOps Trainee | Training Lab | 1 | Built CI/CD pipelines and container labs with validation and rollback',
          '#candidateEducation':'BSc | Example University | 2025','#candidateCertifications':'AWS Cloud Practitioner Training',
          '#candidateRoles':'Junior DevOps Engineer','#candidateLocations':'Remote',
          '#candidateResumeText':'Linux Git Docker Jenkins AWS Bash CI/CD monitoring incident response rollback'}
        for selector,value in fills.items():page.fill(selector,value)
        page.check('#candidateVerified');page.locator('#candidateProfileForm button[type=submit]').click()
        page.wait_for_function("document.querySelector('#toast').textContent.includes('profile saved')")

        page.locator('[data-career-tab="discover"]').click();page.fill('#manualJobCompany','Acme Platform');page.fill('#manualJobTitle','Junior DevOps Engineer');page.fill('#manualJobLocation','Remote');page.fill('#manualJobDescription','Linux Docker Jenkins AWS Git CI/CD Bash with one year experience. Kubernetes preferred. Validate deployments, monitor services, handle incidents, apply security controls, and document rollback procedures.');page.locator('#manualJobForm button[type=submit]').click()
        page.wait_for_function("document.querySelector('#toast').textContent.includes('Job analyzed')");page.wait_for_selector('#career-tab-apply.active');assert page.locator('#careerApplyJob option').count()>=2

        page.evaluate("document.querySelector('.nav-item[data-page=\"portfolio\"]').click()");page.wait_for_selector('#page-portfolio.active')
        portfolio={
          '#portfolioTitle':'Production-ready Docker CI Pipeline','#portfolioTools':'Docker, Jenkins, Git, Linux',
          '#portfolioProblem':'Manual deployments were inconsistent and difficult to validate.','#portfolioBusiness':'Create repeatable safe delivery with evidence and rollback.',
          '#portfolioArchitecture':'Git to Jenkins validation, immutable Docker image, staged deployment and health verification.',
          '#portfolioImplementation':'Created Jenkinsfile, Dockerfile, tests, immutable tags, approvals, health checks, evidence, and operational handover.',
          '#portfolioSecurity':'Least privilege, protected credentials, image scanning, dependency checks, no embedded secrets.',
          '#portfolioTesting':'Unit, integration, container health, pipeline, deployment smoke and rollback tests.',
          '#portfolioMonitoring':'Pipeline state, deployment health, metrics, logs and alerts.','#portfolioTroubleshooting':'Reviewed logs, corrected invalid image tag and retested.',
          '#portfolioRollback':'Redeployed last known-good immutable image and verified health.','#portfolioOutcome':'Repeatable validated release with documented recovery.',
          '#portfolioEvidence':'Pipeline output\nImage digest\nHealth output\nRollback verification\nArchitecture diagram'}
        for selector,value in portfolio.items():page.fill(selector,value)
        page.check('#portfolioApprove');page.locator('#portfolioProjectForm button[type=submit]').click();page.wait_for_function("document.querySelector('#toast').textContent.includes('Project scored')");page.wait_for_function("Number(document.querySelector('#portfolioReadyCount').textContent)>=1")
        page.locator('#buildPortfolio').click();page.wait_for_function("document.querySelector('#toast').textContent.includes('Portfolio website')");page.wait_for_function("Number(document.querySelector('#portfolioBuildCount').textContent)>=1")

        page.evaluate("document.querySelector('.nav-item[data-page=\"career\"]').click()");page.locator('[data-career-tab="apply"]').click();page.locator('#generateCareerResume').click();page.wait_for_function("document.querySelector('#toast').textContent.includes('resume generated')");page.wait_for_selector('#careerResumeResult h3')
        page.fill('#careerEmailTo','hr@example.com');page.fill('#careerEmailSubject','Application for Junior DevOps Engineer — Browser Test Candidate');page.fill('#careerEmailBody','Dear Hiring Manager,\n\nPlease find my verified job-specific resume and portfolio attached. I would welcome an interview.\n\nRegards,\nBrowser Test Candidate');page.locator('#careerEmailForm button[type=submit]').click();page.wait_for_selector('#careerEmailPreview h3');assert 'hr@example.com' in page.locator('#careerEmailPreview').inner_text()

        page.locator('[data-career-tab="track"]').click();page.locator('#prepareCareerInterview').click();page.wait_for_function("document.querySelector('#toast').textContent.includes('interview pack prepared')");assert 'Screening' in page.locator('#careerResearchResult').inner_text()
        page.screenshot(path=str(ROOT/'docs/v25_studio_dashboard_desktop.png'),full_page=False)

        page.set_viewport_size({'width':360,'height':740});page.wait_for_timeout(150);assert page.locator('#menuButton').is_visible();page.locator('#menuButton').click();page.wait_for_selector('#sidebar.open');mobile=sidebar.evaluate("el=>({clientHeight:el.clientHeight,scrollHeight:el.scrollHeight,overflow:getComputedStyle(el).overflowY})");sidebar.evaluate('el=>el.scrollTop=el.scrollHeight');assert sidebar.evaluate('el=>el.scrollTop')>0
        screenshot=ROOT/'docs/v25_studio_mobile_sidebar.png';page.screenshot(path=str(screenshot),full_page=False)
        browser.close()
    assert not errors,errors
    print('V2.5 STUDIO BROWSER-RENDERED USER JOURNEY PASSED')
    print(json.dumps({'desktop_sidebar':metrics,'candidate_profile':'passed','job_analysis':'passed','portfolio':'passed','resume_email':'passed','interview_pack':'passed','mobile_sidebar':mobile,'console_errors':0},indent=2))


if __name__=='__main__':main()
