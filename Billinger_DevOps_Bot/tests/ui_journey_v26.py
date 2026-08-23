"""Browser-rendered v2.6 AI Control Center journey using strict in-page API mocks."""
from __future__ import annotations
import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

MOCK=r'''
const providers=[
 {provider:'gemini',label:'Google Gemini',purpose:'Lesson tutor and curriculum-gap review',enabled:false,configured:false,key_hint:'',model:'gemini-3.6-flash',daily_limit:100,used_today:0,last_status:'not_configured',last_error:'',last_success_at:'',cooldown_active:false},
 {provider:'openai',label:'OpenAI API (ChatGPT models)',purpose:'Test and interview answer analysis',enabled:false,configured:false,key_hint:'',model:'gpt-5.6-terra',daily_limit:100,used_today:0,last_status:'not_configured',last_error:'',last_success_at:'',cooldown_active:false},
 {provider:'groq',label:'Groq',purpose:'Fast adaptive question and revision generation',enabled:false,configured:false,key_hint:'',model:'openai/gpt-oss-20b',daily_limit:100,used_today:0,last_status:'not_configured',last_error:'',last_success_at:'',cooldown_active:false},
 {provider:'openrouter',label:'OpenRouter',purpose:'Company-role interview packs and broad fallback',enabled:false,configured:false,key_hint:'',model:'openrouter/auto',daily_limit:100,used_today:0,last_status:'not_configured',last_error:'',last_success_at:'',cooldown_active:false}
];
const tasks=['lesson_tutor','test_analysis','interview_analysis','question_generation','curriculum_audit','company_interview','resume_review'].map((task,i)=>({task,label:task.replaceAll('_',' '),providers:i===0?['gemini','groq','openai','openrouter']:['openai','gemini','openrouter','groq']}));
let lastEnvironment=null;let mockWizardSeen=!window.v27FirstRun;
window.mockDashboard={version:'2.9.0',settings:{online_ai_enabled:true,auto_failover:true,redact_personal_data:true,allow_student_content:true,global_daily_request_limit:250,request_timeout_seconds:120,max_output_tokens:1400},providers,tasks,recent_usage:[],today_totals:[],curriculum_proposals:[],secret_storage:'Windows DPAPI — tied to this Windows account',notice:'OpenAI API billing is separate.'};
const response=(x,status=200)=>new Response(JSON.stringify(x),{status,headers:{'Content-Type':'application/json'}});
window.fetch=async(input,options={})=>{const url=String(input),body=options.body?JSON.parse(options.body):{};
 if(url==='/api/catalog')return response({tools:[{slug:'linux',name:'Linux Administration',icon:'🐧',category:'Foundation',description:'Linux',levels:[{name:'Beginner',lessons:[],labs:[{id:'lab1',title:'Safe lab',scenario:'Safe lab scenario',difficulty:'Beginner',deliverables:['Evidence'],acceptance_criteria:['Validation']}]}]}]});
 if(url.startsWith('/api/tool?slug='))return response({slug:'linux',name:'Linux Administration',icon:'🐧',category:'Foundation',description:'Linux',levels:[{name:'Beginner',lessons:[],labs:[{id:'lab1',title:'Safe lab',scenario:'Safe lab scenario',difficulty:'Beginner',deliverables:['Evidence'],acceptance_criteria:['Validation']}],company_workflow:'Company workflow',mastery_gate:'Evidence'}]});
 if(url.startsWith('/api/resources?'))return response({resources:[]});
 if(url==='/api/students')return response({students:[{id:1,name:'Student 1',pin_protected:false}]});
 if(url==='/api/v4/student/session')return response({token:'student-token'});
 if(url.startsWith('/api/progress?'))return response({progress:[],stats:{completed_lessons:0,total_lessons:336,passed_labs:0,total_labs:84,average_score:0,passed_interviews:0,passed_tests:0,resumes:0,lesson_percent:0}});
 if(url==='/api/v3/status')return response({admin:{configured:true,admin_name:'AI Admin',institute_name:'Billinger AI Studio'},requirements:{},roles:['Junior DevOps Engineer','DevOps Engineer']});
 if(url==='/api/v2/readiness')return response({core:{ready:true,detail:'Ready'},git:{ready:true,detail:'Ready'},wsl:{ready:false,detail:'Optional'},docker:{ready:false,detail:'Optional'},kubectl:{ready:false,detail:'Optional'},terraform:{ready:false,detail:'Optional'},local_ai:{ready:false,detail:'Optional'},settings:{lab_mode:'simulator',wsl_distribution:'',ai_enabled:false,ai_endpoint:'http://127.0.0.1:8080/v1/chat/completions',ai_model:'local-model'}});
 if(url==='/api/v6/ai/status')return response({enabled:true,auto_failover:true,configured_providers:providers.filter(p=>p.configured).map(p=>p.provider),routes:Object.fromEntries(tasks.map(t=>[t.task,t.providers]))});
 if(url.startsWith('/api/v7/readiness?'))return response({version:'2.9.0',ready_to_learn:false,readiness_percent:50,notice:'Online AI and real-tool installations are optional.',wizard_seen:mockWizardSeen,wizard_completed:false,profile:{target_role:'Junior DevOps Engineer',study_minutes:90},baseline:null,environment:lastEnvironment,backup:{status:'missing',summary:'No verified backup has been created yet.'},steps:[
  {id:'admin',label:'Administrator configured',required:true,complete:true,detail:'Protected'},
  {id:'profile',label:'Learner goal and study time',required:true,complete:true,detail:'Junior DevOps Engineer · 90 minutes/day'},
  {id:'baseline',label:'Baseline assessment',required:true,complete:false,detail:'Not completed'},
  {id:'library',label:'Verified learning library',required:true,complete:true,detail:'69 classified resources available'},
  {id:'environment',label:'Local lab environment checked',required:false,complete:false,detail:'Run a safe read-only scan'},
  {id:'ai',label:'At least one AI provider tested',required:false,complete:false,detail:'AI optional'},
  {id:'backup',label:'Verified backup created',required:true,complete:false,detail:'No verified backup'},
  {id:'plan',label:'First daily plan generated',required:true,complete:false,detail:'Not generated'}]});
 if(url==='/api/v7/readiness/seen')return response({saved:true});
 if(url==='/api/v7/baseline/start'){const qs=Array.from({length:20},(_,i)=>({id:'b'+i,tool:['linux','networking','git','shell','docker','kubernetes','terraform','devsecops','sre','system-design'][Math.floor(i/2)],difficulty:i%2?'Intermediate':'Beginner',prompt:'Baseline question '+(i+1),choices:['A','B','C','D']}));return response({session_id:'BASE-browser',questions:qs,count:20})}
 if(url==='/api/v7/baseline/submit')return response({session_id:'BASE-browser',score:80,classification:'Intermediate learner',domain_scores:{linux:100,networking:50,git:100,shell:50,docker:100,kubernetes:50,terraform:100,devsecops:50,sre:100,'system-design':50},recommended_start:'networking',recommended_start_name:'Networking, DNS and HTTP',details:[],message:'Baseline recommendation only.'});
 const envTools=['python','git','wsl','docker','kubectl','terraform','ansible','aws','az','gcloud'].map((name,i)=>({name,installed:i<2,path:i<2?'/safe/'+name:'',version:i<2?'version ok':'Not installed',purpose:'Safe '+name+' check',required_for_core:name==='python'}));
 if(url==='/api/v7/environment/check'){const result={id:'ENV-browser',checked_at:'2026-08-06T00:00:00Z',core_ready:true,tools:envTools,modes:[{id:'guided',label:'Guided learning'},{id:'simulation',label:'Safe simulation'},{id:'local',label:'Real local execution'},{id:'cloud',label:'External cloud lab'},{id:'company',label:'Simulated company scenario'}]};lastEnvironment={id:result.id,checked_at:result.checked_at,results:result};return response(result)}
 if(url.startsWith('/api/v7/mastery?'))return response({student_id:1,mastered_count:0,total_tools:21,policy:'Evidence gates',tools:Array.from({length:21},(_,i)=>({tool:'tool-'+i,name:'DevOps Tool '+(i+1),icon:'◆',percent:i,mastered:false,requirements:['lessons','labs','test','practical','tickets','incident','capstone','interview','portfolio'].map(id=>({id,label:id,current:0,target:id==='practical'?4:1,complete:false}))}))});
 if(url==='/api/v7/freshness')return response({pending_ai_proposals:2,summary:{current:3,review_due:18,deprecated:0},notice:'Admin review required',items:Array.from({length:21},(_,i)=>({tool:'tool-'+i,name:'DevOps Tool '+(i+1),icon:'◆',course_version:'Billinger curriculum 2.7',tool_version_covered:'Verified volumes',official_doc_url:'https://example.com/docs',last_reviewed:'',review_status:'review_required',deprecated_notes:'',reviewer:'',effective_status:'review_required'}))});
 if(url==='/api/v7/backup/health')return response({status:'healthy',summary:'Latest backup passed checksum and ZIP integrity.'});
 if(url==='/api/v7/ai/models')return response({items:[]});
 if(url==='/api/v7/ai/fallback/dry-run')return response({task:body.task,label:'Lesson tutor',route:['gemini','groq'],trace:[{provider:'gemini',status:'simulated_failure'},{provider:'groq',status:'selected'}],selected_provider:'groq',would_succeed:true,credits_used:0,notice:'Dry-run only.'});
 if(url==='/api/v3/admin/auth')return response({token:'admin-token',admin_name:'AI Admin',institute_name:'Billinger AI Studio'});
 if(url==='/api/v6/ai/dashboard')return response(window.mockDashboard);
 if(url==='/api/v6/ai/provider/save'){const p=providers.find(x=>x.provider===body.provider);p.enabled=!!body.enabled;p.configured=!!body.api_key;p.key_hint=p.configured?'AIz••••2345':'';p.model=body.model;p.daily_limit=body.daily_limit;p.last_status=p.configured?'ready':'not_configured';return response(p)}
 if(url==='/api/v6/ai/route/save')return response({task:body.task,providers:body.providers});
 if(url==='/api/v6/ai/settings/save')return response(body);
 return response({error:'Unhandled '+url},404);
};
'''

def main():
    html=(ROOT/'static/index.html').read_text(encoding='utf-8')
    html=re.sub(r'<link rel="stylesheet" href="/styles\.css\?v=[^"]+">','',html)
    html=re.sub(r'<script src="/app\.js\?v=[^"]+"></script>','',html)
    css=(ROOT/'static/styles.css').read_text(encoding='utf-8');js=(ROOT/'static/app.js').read_text(encoding='utf-8')
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1440,'height':900})
        page.on('pageerror',lambda e:errors.append('pageerror:'+str(e)))
        page.on('console',lambda m:errors.append('console:'+m.text) if m.type=='error' else None)
        page.set_content(html,wait_until='domcontentloaded');page.add_style_tag(content=css);page.add_script_tag(content=MOCK);page.add_script_tag(content=js);page.evaluate('init()')
        page.wait_for_selector('#page-dashboard.active');assert '4k precision build 2.9.0' in page.locator('.studio-build-badge').inner_text().lower()
        page.click('#menuButton');page.locator('.nav-item[data-page="system"]').click();page.wait_for_selector('#page-system.active')
        page.evaluate("renderAiDashboard(window.mockDashboard); document.querySelector('#aiAdminLocked').classList.add('hidden'); document.querySelector('#aiAdminDashboard').classList.remove('hidden')");page.wait_for_selector('#aiAdminDashboard:not(.hidden)')
        page.wait_for_function("document.querySelectorAll('[data-ai-provider-form]').length===4");assert page.locator('[data-provider-jump]').count()==4
        # All four providers must be visually presented in one row at a normal laptop/desktop width.
        boxes=[page.locator('[data-ai-provider-form]').nth(i).bounding_box() for i in range(4)]
        assert all(boxes), boxes
        assert max(abs(boxes[i]['y']-boxes[0]['y']) for i in range(1,4)) < 30, boxes
        assert boxes[-1]['x']+boxes[-1]['width'] <= 1440, boxes
        # High-contrast copy: helper text is clearly readable on the dark precision card surface.
        contrast=page.locator('[data-ai-provider-form="gemini"] .ai-provider-head small').evaluate("el=>({color:getComputedStyle(el).color,bg:getComputedStyle(el.closest('.ai-provider-card')).backgroundColor})")
        assert contrast['color'] in {'rgb(198, 209, 220)','rgb(203, 213, 223)','rgb(213, 221, 229)'}, contrast
        gemini=page.locator('[data-ai-provider-form="gemini"]');page.evaluate("const f=document.querySelector('[data-ai-provider-form=\"gemini\"]');f.querySelector('input[name=\"api_key\"]').value='AIzaBrowserSmokeKey123456789012345';f.querySelector('input[name=\"enabled\"]').checked=true")
        assert gemini.locator('input[name="api_key"]').input_value().startswith('AIza');assert page.locator('.ai-route-row').count()==7
        page.screenshot(path=str(ROOT/'docs/v26_ai_control_center.png'),full_page=True)
        page.set_viewport_size({'width':390,'height':780});page.click('#menuButton');page.wait_for_selector('#sidebar.open');sidebar=page.locator('#sidebar');m=sidebar.evaluate("el=>({clientHeight:el.clientHeight,scrollHeight:el.scrollHeight,overflow:getComputedStyle(el).overflowY})");sidebar.evaluate('el=>el.scrollTop=el.scrollHeight');assert sidebar.evaluate('el=>el.scrollTop')>0;page.screenshot(path=str(ROOT/'docs/v26_ai_mobile_navigation.png'))
        browser.close()
    assert not errors,errors
    print('V2.6 ADAPTIVE AI BROWSER-RENDERED JOURNEY PASSED');print(json.dumps({'providers':4,'provider_layout':'single_row_desktop','high_contrast':contrast,'routes':7,'mobile_sidebar':m,'console_errors':0},indent=2))
if __name__=='__main__':main()
