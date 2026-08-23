'use strict';

const state = {
  students: [], currentStudent: null, catalog: [], progress: new Map(),
  selectedLab: null, activeTest: null, testSeconds: 0, timerId: null,
  interview: null, pendingStudent: null, activeResource: null, resourcePageIndex: 0, programResource: null, programPageIndex: 0,
  v23Status: null, practicalTemplates: [], selectedPractical: null, practicalRun: null, practicalTimerId: null, adminOverview: null, stagedImport: null, workspacePath: null,
  studentToken: null, career: null, selectedCareerJob: null, selectedCareerResume: null, selectedEmailDraft: null,
  aiDashboard: null, aiTest: null, lastTestResult: null, pendingAiAdmin: false, finalReadiness: null, baselineSession: null, mastery: null
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const escapeHtml = (value='') => String(value).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const storageGet = key => { try { return window.localStorage.getItem(key); } catch (_) { return null; } };
const storageSet = (key, value) => { try { window.localStorage.setItem(key, value); } catch (_) {} };

async function api(path, options={}) {
  const headers = {'Content-Type':'application/json', ...(options.headers || {})};
  if (state.studentToken) headers['X-Student-Token'] = state.studentToken;
  const config = {...options, headers};
  const response = await fetch(path, config);
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) throw new Error(payload.error || payload || `Request failed (${response.status})`);
  return payload;
}

let toastTimer;
function toast(message, error=false) {
  const el = $('#toast'); el.textContent = message; el.className = `toast show${error?' error':''}`;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => el.className='toast', 3400);
}

function showPage(page) {
  $$('.page').forEach(p => p.classList.toggle('active', p.id === `page-${page}`));
  $$('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.page === page));
  $('#sidebar').classList.remove('open');
  document.body.classList.remove('nav-open');
  $('#menuButton')?.setAttribute('aria-expanded','false');
  if (page === 'history') loadHistory();
  if (page === 'roadmap') renderToolGrid();
  if (page === 'company') loadCompany();
  if (page === 'skills') loadSkills();
  if (page === 'system') { loadReadiness(); loadAiControl(); loadCourseFreshness(); }
  if (page === 'capstone') loadCapstones();
  if (page === 'coverage') loadCoverage();
  if (page === 'library') loadProgramLibrary();
  if (page === 'myday') loadMyDay();
  if (page === 'practical') loadPracticalTemplates();
  if (page === 'projects') loadWorkspace();
  if (page === 'certificates') loadCertificates();
  if (page === 'admin') openAdminPage();
  if (page === 'career') loadCareer();
  if (page === 'portfolio') loadPortfolio();
  if (page === 'readiness') { loadFinalReadiness(); loadMasteryGates(); }
  window.scrollTo({top:0, behavior:'smooth'});
}

function populateToolSelect(select, includeFull=false) {
  select.innerHTML = '';
  if (includeFull) select.add(new Option('Full DevOps Track', 'full-devops'));
  state.catalog.forEach(t => select.add(new Option(`${t.icon} ${t.name}`, t.slug)));
}

async function loadStudents() {
  const data = await api('/api/students');
  state.students = data.students;
  const select = $('#studentSelect'); select.innerHTML='';
  state.students.forEach(s => select.add(new Option(`${s.name}${s.pin_protected?' 🔒':''}`, s.id)));
  const saved = Number(storageGet('billingerStudent'));
  const selected = state.students.find(s => s.id === saved) || state.students[0];
  if (selected) {
    select.value = String(selected.id);
    await activateStudent(selected, true);
  }
}

async function activateStudent(student, initial=false) {
  if (student.pin_protected && !student._sessionToken) {
    state.pendingStudent = student;
    $('#pinInput').value=''; $('#pinError').textContent=''; $('#pinDialog').showModal(); return;
  }
  try {
    if (student._sessionToken) state.studentToken = student._sessionToken;
    else {
      const session = await api('/api/v4/student/session',{method:'POST',body:JSON.stringify({student_id:student.id,pin:''})});
      state.studentToken = session.token;
    }
  } catch (e) {
    if (student.pin_protected) { state.pendingStudent=student; $('#pinDialog').showModal(); return; }
    throw e;
  }
  state.currentStudent = student;
  state.career = null;
  storageSet('billingerStudent', student.id);
  $('#studentSelect').value=String(student.id);
  await loadProgress();
  await loadFinalReadiness();
  if(initial && state.finalReadiness && !state.finalReadiness.wizard_seen){
    showPage('readiness');
  }
  const activePage=document.querySelector('.page.active')?.id?.replace('page-','');
  if(activePage==='myday') loadMyDay(); if(activePage==='projects') loadWorkspace(); if(activePage==='certificates') loadCertificates(); if(activePage==='career') loadCareer(); if(activePage==='portfolio') loadPortfolio(); if(activePage==='readiness') { loadFinalReadiness(); loadMasteryGates(); }
}

async function loadProgress() {
  if (!state.currentStudent) return;
  const data = await api(`/api/progress?student_id=${state.currentStudent.id}`);
  state.progress = new Map(data.progress.map(p => [`${p.item_type}:${p.item_id}`, p]));
  updateStats(data.stats);
}

function updateStats(stats) {
  $('#statLessons').textContent = `${stats.completed_lessons} / ${stats.total_lessons}`;
  $('#statLabs').textContent = `${stats.passed_labs} / ${stats.total_labs}`;
  $('#statAverage').textContent = `${stats.average_score}%`;
  $('#statInterviews').textContent = stats.passed_interviews;
  $('#statTests').textContent = stats.passed_tests;
  $('#statResumes').textContent = stats.resumes;
  $('#lessonMeter').style.width = `${stats.lesson_percent}%`;
  $('#labMeter').style.width = `${Math.min(100, stats.passed_labs/Math.max(1,stats.total_labs)*100)}%`;
  $('#scoreMeter').style.width = `${stats.average_score}%`;
  const readiness = Math.round(stats.lesson_percent*.55 + Math.min(100,stats.passed_labs/Math.max(1,stats.total_labs)*100)*.2 + Math.min(100,stats.passed_tests*5)*.15 + Math.min(100,stats.passed_interviews*20)*.1);
  $('#readinessPercent').textContent=`${readiness}%`;
  $('.readiness-ring').style.background=`conic-gradient(var(--cyan) ${readiness*3.6}deg,rgba(255,255,255,.06) 0)`;
}

async function loadCatalog() {
  const data = await api('/api/catalog'); state.catalog = data.tools;
  ['practiceTool','testTool','interviewTool','onlineTool','recruitmentTrack','aiTestTool'].forEach(id => { const el=$('#'+id); if(el) populateToolSelect(el, ['testTool','interviewTool','recruitmentTrack','aiTestTool'].includes(id)); });
  if($('#practicalTool')) state.catalog.forEach(t=>$('#practicalTool').add(new Option(`${t.icon} ${t.name}`,t.slug)));
  if($('#workspaceTool')) populateToolSelect($('#workspaceTool'));
  renderToolGrid(); await refreshPracticeLabs();
}

function renderToolGrid() {
  const query = ($('#toolSearch')?.value || '').toLowerCase();
  const filtered = state.catalog.filter(t => `${t.name} ${t.category} ${t.description}`.toLowerCase().includes(query));
  $('#toolGrid').innerHTML = filtered.map(t => `<article class="tool-card panel" data-slug="${t.slug}" tabindex="0">
    <div class="tool-card-header"><div class="tool-icon">${t.icon}</div><span class="category">${escapeHtml(t.category)}</span></div>
    <h2>${escapeHtml(t.name)}</h2><p>${escapeHtml(t.description)}</p>
    <div class="level-strip" title="Beginner, Intermediate, Advanced, Master"><span></span><span></span><span></span><span></span></div>
  </article>`).join('') || '<div class="panel empty-state"><h2>No matching domain</h2></div>';
  $$('.tool-card').forEach(card => {
    card.addEventListener('click', () => openTool(card.dataset.slug));
    card.addEventListener('keydown', e => { if(e.key==='Enter') openTool(card.dataset.slug); });
  });
}

async function openTool(slug) {
  try {
    const [tool, library] = await Promise.all([
      api(`/api/tool?slug=${encodeURIComponent(slug)}`),
      api(`/api/resources?tool=${encodeURIComponent(slug)}&student_id=${state.currentStudent?.id || 0}`)
    ]);
    const levels = tool.levels.map(level => `<section class="level-card">
      <div class="level-head"><div><span class="pill">${escapeHtml(level.name)}</span> <strong>${level.lessons.length} lessons · ${level.labs.length} lab</strong></div><span>⌄</span></div>
      <div class="level-body">
        <div class="company-flow"><b>How companies use this level</b><br>${escapeHtml(level.company_workflow)}</div>
        <p style="margin:12px 0 0"><b>Mastery gate:</b> ${escapeHtml(level.mastery_gate)}</p>
        <div class="lesson-list">${level.lessons.map(lesson => {
          const done = state.progress.get(`lesson:${lesson.id}`)?.status === 'completed';
          return `<article class="lesson"><h4>${escapeHtml(lesson.title)}</h4><p>${escapeHtml(lesson.explanation)}</p><p><b>Company example:</b> ${escapeHtml(lesson.company_use)}</p><code>${escapeHtml(lesson.example.replace('Worked example: ',''))}</code><div class="lesson-actions"><small>${lesson.estimated_minutes} min</small><button class="lesson-complete" data-id="${lesson.id}" ${done?'disabled':''}>${done?'✓ Completed':'Mark complete'}</button></div></article>`;
        }).join('')}</div>
        <div class="result-card"><b>Practice lab:</b> ${escapeHtml(level.labs[0].scenario)}</div>
      </div>
    </section>`).join('');

    const resourceCards = library.resources.map(resource => `<article class="learning-resource-card" data-resource-card="${resource.id}" data-resource-search="${escapeHtml((resource.title+' '+resource.summary+' '+resource.volume+' '+resource.primary_tool_name).toLowerCase())}">
      <div class="resource-card-top"><span class="resource-volume">${escapeHtml(resource.library_label || `Volume ${resource.volume}`)}</span><span class="resource-status ${resource.status==='completed'?'complete':''}">${resource.status==='completed'?'✓ Reviewed':'Verified placement'}</span></div>
      <h3>${escapeHtml(resource.title)}</h3>
      <p>${escapeHtml(resource.summary || 'Structured DevOps course material with company workflows, hands-on practice, troubleshooting, projects, and interview preparation.')}</p>
      <div class="placement-proof"><b>Assigned only to:</b> ${escapeHtml(resource.primary_tool_name)}</div><div class="resource-meta"><span>${resource.page_count} PDF pages</span><span>${Number(resource.word_count || 0).toLocaleString()} words</span><span>PDF + DOCX</span></div>
      <div class="resource-actions"><button class="button primary resource-open" data-resource="${resource.id}">Read & ask</button><a class="button secondary" href="${resource.links.pdf}" target="_blank" rel="noopener">Open PDF</a><a class="button secondary" href="${resource.links.docx}">DOCX</a></div>
    </article>`).join('');

    const resources = `<section class="tool-library">
      <div class="library-heading"><div><span class="eyebrow">VERIFIED PRIMARY-TOOL LIBRARY</span><h2>Books assigned to ${escapeHtml(tool.name)}</h2><p>Only books whose dominant subject is this tool appear here. Supporting mentions of other technologies no longer create duplicate or mixed placements.</p></div><span class="library-count">${library.count} verified resources</span></div>
      <div class="library-filter"><input id="toolResourceSearch" placeholder="Search imported books for this tool"></div><div class="learning-resource-grid">${resourceCards || '<div class="empty-state"><h3>No imported book is assigned to this domain.</h3></div>'}</div>
      <section id="resourceReader" class="resource-reader hidden" aria-live="polite">
        <div class="resource-reader-head"><div><span id="resourceReaderVolume" class="pill"></span><h2 id="resourceReaderTitle"></h2><p id="resourceReaderSummary"></p></div><button id="resourceClose" class="icon-button" title="Close reader">×</button></div>
        <div class="resource-reader-actions"><button id="resourcePdfTab" class="button primary" type="button">PDF view</button><button id="resourceTextTab" class="button secondary" type="button">Text view</button><button id="resourceMarkComplete" class="button secondary" type="button">Mark reviewed</button><a id="resourceOpenPdf" class="button secondary" target="_blank" rel="noopener">Open full PDF</a><a id="resourceOpenDocx" class="button secondary">Open DOCX</a></div>
        <div id="resourcePdfPane" class="resource-pane"><iframe id="resourcePdfFrame" title="Course PDF viewer"></iframe></div>
        <div id="resourceTextPane" class="resource-pane hidden">
          <div class="resource-page-controls"><button id="resourcePrevPage" class="icon-button" type="button">←</button><label>Page <select id="resourcePageSelect"></select></label><button id="resourceNextPage" class="icon-button" type="button">→</button><span id="resourcePageCount" class="muted"></span></div>
          <article id="resourcePageText" class="resource-page-text"></article>
        </div>
        <div class="resource-study-assistant"><div><span class="eyebrow">BOOK-GROUNDED STUDY ASSISTANT</span><h3>Ask this book</h3><p>Without a local AI model, the bot returns the most relevant source passages. With Local AI enabled, it produces a page-cited answer using only those passages.</p></div><form id="resourceAskForm"><textarea id="resourceQuestion" rows="3" placeholder="Example: How should a company validate a Kubernetes rollout and prepare rollback evidence?"></textarea><button class="button primary" type="submit">Ask document</button></form><div id="resourceAnswer" class="resource-answer hidden"></div></div>
      </section>
    </section>`;

    $('#toolDetail').innerHTML = `<div class="tool-hero"><div class="tool-icon">${tool.icon}</div><div><span class="category">${escapeHtml(tool.category)}</span><h1>${escapeHtml(tool.name)}</h1><p>${escapeHtml(tool.description)}</p><p><b>Company importance:</b> ${escapeHtml(tool.why_company)}</p></div></div>
      ${resources}
      <div class="two-columns"><div><h3>Prerequisites</h3><ul>${tool.prerequisites.map(x=>`<li>${escapeHtml(x)}</li>`).join('')}</ul></div><div><h3>Mastery outcomes</h3><ul>${tool.outcomes.map(x=>`<li>${escapeHtml(x)}</li>`).join('')}</ul></div></div><div class="tool-levels">${levels}</div>`;

    $$('.level-head', $('#toolDetail')).forEach(head => head.addEventListener('click',()=>head.nextElementSibling.classList.toggle('hidden')));
    $$('.lesson-complete', $('#toolDetail')).forEach(btn => btn.addEventListener('click', async()=>{
      try { await api('/api/progress/lesson',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,lesson_id:btn.dataset.id,completed:true})}); btn.textContent='✓ Completed'; btn.disabled=true; await loadProgress(); toast('Lesson completed'); }
      catch(e){toast(e.message,true)}
    }));
    $$('.resource-open', $('#toolDetail')).forEach(btn => btn.addEventListener('click',()=>openLearningResource(btn.dataset.resource)));
    $('#toolResourceSearch')?.addEventListener('input',e=>{const q=e.target.value.trim().toLowerCase();$$('[data-resource-card]', $('#toolDetail')).forEach(card=>card.classList.toggle('hidden',q && !card.dataset.resourceSearch.includes(q)))});
    $('#resourceClose')?.addEventListener('click',()=>{$('#resourceReader').classList.add('hidden');state.activeResource=null;$('#resourcePdfFrame').src='about:blank'});
    $('#resourcePdfTab')?.addEventListener('click',()=>showResourcePane('pdf'));
    $('#resourceTextTab')?.addEventListener('click',()=>showResourcePane('text'));
    $('#resourcePrevPage')?.addEventListener('click',()=>changeResourcePage(-1));
    $('#resourceNextPage')?.addEventListener('click',()=>changeResourcePage(1));
    $('#resourcePageSelect')?.addEventListener('change',e=>{state.resourcePageIndex=Number(e.target.value);renderResourcePage()});
    $('#resourceAskForm')?.addEventListener('submit',askLearningResource);
    $('#resourceMarkComplete')?.addEventListener('click',markLearningResourceReviewed);
    $('#toolDialog').showModal();
  } catch(e) { toast(e.message,true); }
}

async function openLearningResource(resourceId) {
  try {
    const resource = await api(`/api/resource?id=${encodeURIComponent(resourceId)}`);
    state.activeResource = resource;
    state.resourcePageIndex = 0;
    $('#resourceReaderVolume').textContent = resource.library_label || `Volume ${resource.volume}`;
    $('#resourceReaderTitle').textContent = resource.title;
    $('#resourceReaderSummary').textContent = resource.summary || '';
    $('#resourceOpenPdf').href = resource.links.pdf;
    $('#resourceOpenDocx').href = resource.links.docx;
    $('#resourcePdfFrame').src = resource.links.pdf;
    $('#resourcePageSelect').innerHTML = resource.pages.map((page,index)=>`<option value="${index}">${page.page}</option>`).join('');
    $('#resourcePageCount').textContent = `${resource.pages.length} extracted pages`;
    $('#resourceAnswer').classList.add('hidden');
    $('#resourceAnswer').innerHTML = '';
    $('#resourceQuestion').value = '';
    $('#resourceReader').classList.remove('hidden');
    showResourcePane('pdf');
    renderResourcePage();
    $('#resourceReader').scrollIntoView({behavior:'smooth',block:'start'});
  } catch(e) { toast(e.message,true); }
}

function showResourcePane(mode) {
  const pdf = mode === 'pdf';
  $('#resourcePdfPane')?.classList.toggle('hidden', !pdf);
  $('#resourceTextPane')?.classList.toggle('hidden', pdf);
  $('#resourcePdfTab')?.classList.toggle('primary', pdf);
  $('#resourcePdfTab')?.classList.toggle('secondary', !pdf);
  $('#resourceTextTab')?.classList.toggle('primary', !pdf);
  $('#resourceTextTab')?.classList.toggle('secondary', pdf);
}

function renderResourcePage() {
  const resource = state.activeResource;
  if (!resource?.pages?.length) return;
  state.resourcePageIndex = Math.max(0, Math.min(state.resourcePageIndex, resource.pages.length-1));
  const page = resource.pages[state.resourcePageIndex];
  $('#resourcePageSelect').value = String(state.resourcePageIndex);
  $('#resourcePageText').innerHTML = `<div class="resource-page-label">Page ${page.page}</div><p>${escapeHtml(page.text).replace(/\n\n+/g,'</p><p>').replace(/\n/g,'<br>')}</p>`;
  $('#resourcePrevPage').disabled = state.resourcePageIndex === 0;
  $('#resourceNextPage').disabled = state.resourcePageIndex === resource.pages.length-1;
}

function changeResourcePage(direction) {
  if (!state.activeResource) return;
  state.resourcePageIndex += direction;
  renderResourcePage();
}

async function askLearningResource(event) {
  event.preventDefault();
  if (!state.activeResource) return;
  const question = $('#resourceQuestion').value.trim();
  if (!question) return;
  const box = $('#resourceAnswer');
  box.className = 'resource-answer';
  box.innerHTML = '<div class="resource-thinking">Searching the selected book…</div>';
  try {
    const result = await api('/api/resource/ask',{method:'POST',body:JSON.stringify({student_id:state.currentStudent?.id || 0,resource_id:state.activeResource.id,question})});
    const sourceHtml = result.sources?.length ? `<details><summary>Source passages (${result.sources.length})</summary>${result.sources.map(src=>`<blockquote><b>Page ${src.page}</b><br>${escapeHtml(src.excerpt)}</blockquote>`).join('')}</details>` : '';
    const mode = result.mode === 'local_ai' ? 'Local AI answer grounded in this book' : result.mode === 'extractive' ? 'Extractive answer grounded in this book' : 'No matching passage';
    box.innerHTML = `<span class="pill">${escapeHtml(mode)}</span><div class="resource-answer-text">${escapeHtml(result.answer).replace(/\n/g,'<br>')}</div>${sourceHtml}`;
  } catch(e) { box.className='resource-answer error';box.textContent=e.message;toast(e.message,true); }
}

async function markLearningResourceReviewed() {
  if (!state.activeResource || !state.currentStudent) return;
  try {
    await api('/api/resource/progress',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,resource_id:state.activeResource.id,completed:true})});
    const badge = $(`[data-resource-card="${CSS.escape(state.activeResource.id)}"] .resource-status`);
    if (badge) { badge.textContent='✓ Reviewed';badge.classList.add('complete'); }
    $('#resourceMarkComplete').textContent='✓ Reviewed';
    await loadProgress();
    toast('Course book marked reviewed');
  } catch(e) { toast(e.message,true); }
}

async function refreshPracticeLabs() {
  if (!state.catalog.length) return;
  const slug = $('#practiceTool').value || state.catalog[0].slug;
  const levelName = $('#practiceLevel').value;
  const tool = await api(`/api/tool?slug=${encodeURIComponent(slug)}`);
  const level = tool.levels.find(l=>l.name===levelName) || tool.levels[0];
  $('#practiceLabList').innerHTML = level.labs.map(l=>`<button class="lab-button" data-id="${l.id}">${escapeHtml(l.title)}<small>${escapeHtml(l.scenario.slice(0,90))}...</small></button>`).join('');
  $$('.lab-button').forEach(b=>b.addEventListener('click',()=>selectPracticeLab(level.labs.find(l=>l.id===b.dataset.id), b)));
  if (level.labs[0]) selectPracticeLab(level.labs[0], $('.lab-button'));
}

function selectPracticeLab(lab, button) {
  state.selectedLab = lab; $$('.lab-button').forEach(b=>b.classList.toggle('active',b===button));
  $('#practiceEmpty').classList.add('hidden'); $('#practiceWorkspace').classList.remove('hidden');
  $('#practiceDifficulty').textContent=lab.difficulty; $('#practiceTitle').textContent=lab.title; $('#practiceScenario').textContent=lab.scenario;
  $('#practiceDeliverables').innerHTML=lab.deliverables.map(x=>`<li>${escapeHtml(x)}</li>`).join('');
  $('#practiceCriteria').innerHTML=lab.acceptance_criteria.map(x=>`<li>${escapeHtml(x)}</li>`).join('');
  $('#practiceResponse').value=''; $('#practiceResult').classList.add('hidden');
}

async function submitPractice() {
  if (!state.selectedLab) return;
  try {
    const result=await api('/api/practice/submit',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,lab_id:state.selectedLab.id,response:$('#practiceResponse').value})});
    const box=$('#practiceResult'); box.className=`result-card ${result.passed?'pass':'fail'}`;
    box.innerHTML=`<h3>${result.passed?'✓ Lab passed':'↻ Review required'} · ${result.score}%</h3><p>${escapeHtml(result.feedback)}</p>`;
    await loadProgress(); toast(result.passed?'Practice lab passed':'Practice feedback generated');
  } catch(e){toast(e.message,true)}
}

function renderTest(data) {
  state.activeTest={...data, questions:data.questions}; state.testSeconds=0; clearInterval(state.timerId);
  $('#testSetup').classList.add('hidden'); $('#testResult').classList.add('hidden'); $('#testRunner').classList.remove('hidden');
  $('#testForm').innerHTML=data.questions.map((q,i)=>`<article class="question-card panel"><div class="question-meta"><span>Question ${i+1} · ${q.difficulty}</span><span>${q.type==='mcq'?'Multiple choice':'Written scenario'}</span></div><h3>${escapeHtml(q.prompt).replace(/\n/g,'<br>')}</h3>${q.choices?q.choices.map((c,ci)=>`<label class="choice"><input type="radio" name="q_${q.id}" value="${ci}"><span>${escapeHtml(c)}</span></label>`).join(''):`<textarea name="q_${q.id}" rows="7" placeholder="Give a structured, company-level answer..."></textarea>`}${q.source_url?`<p class="legal-note">${escapeHtml(q.attribution)} <a href="${escapeHtml(q.source_url)}" target="_blank" rel="noreferrer">Open source</a></p>`:''}</article>`).join('');
  $('#testProgressText').textContent=`${data.questions.length} questions · pass mark ${data.pass_mark}%`;
  $('#testProgressMeter').style.width='0%';
  state.timerId=setInterval(()=>{state.testSeconds++; const m=String(Math.floor(state.testSeconds/60)).padStart(2,'0'),s=String(state.testSeconds%60).padStart(2,'0');$('#testTimer').textContent=`${m}:${s}`;},1000);
  $('#testForm').addEventListener('input',()=>{const answered=data.questions.filter(q=>{const el=$(`[name="q_${CSS.escape(q.id)}"]`); if(q.type==='mcq') return !!$(`[name="q_${CSS.escape(q.id)}"]:checked`); return !!el?.value.trim();}).length;$('#testProgressMeter').style.width=`${answered/data.questions.length*100}%`;},{once:false});
}

async function startTest() {
  try { const data=await api('/api/test/start',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,tool:$('#testTool').value,difficulty:$('#testDifficulty').value,count:Number($('#testCount').value),include_online:$('#includeOnline').checked})}); renderTest(data); }
  catch(e){toast(e.message,true)}
}

async function submitTest(){
  if(!state.activeTest)return;
  const answers=state.activeTest.questions.map(q=>({id:q.id,answer:q.type==='mcq'?($(`[name="q_${CSS.escape(q.id)}"]:checked`)?.value ?? ''):($(`[name="q_${CSS.escape(q.id)}"]`)?.value ?? '')}));
  try{
    const result=await api('/api/test/submit',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,session_id:state.activeTest.session_id,answers})});state.lastTestResult={result,answers,session_id:state.activeTest.session_id,tool:$('#testTool').value,difficulty:$('#testDifficulty').value};
    clearInterval(state.timerId);$('#testRunner').classList.add('hidden');const out=$('#testResult');out.classList.remove('hidden');
    out.innerHTML=`<div class="score-hero ${result.passed?'pass':'fail'}"><strong>${result.score}%</strong><h2>${result.passed?'Mastery gate passed':'Mastery gate not passed'}</h2><p>Required score: ${result.pass_mark}%</p></div><div class="detail-list">${result.details.map((d,i)=>`<div class="detail-item"><b>Question ${i+1}: ${d.score}%</b><br>${escapeHtml(d.explanation||'Review the relevant lesson and company workflow.')}${d.missing?.length?`<br><small>Missing concepts: ${escapeHtml(d.missing.join(', '))}</small>`:''}</div>`).join('')}</div><div class="actions"><button id="analyzeTestAi" class="button primary">Analyze weaknesses with AI</button><button id="newTest" class="button secondary">Take another test</button></div><div id="testAiAnalysis" class="ai-analysis-box hidden"></div>`;
    $('#newTest').onclick=()=>{out.classList.add('hidden');$('#testSetup').classList.remove('hidden')};$('#analyzeTestAi').onclick=analyzeLastTestWithAi;await loadProgress();
  }catch(e){toast(e.message,true)}
}

function setInterviewQuestion(data) {
  state.interview={...state.interview,...data}; $('#interviewIdle').classList.add('hidden'); $('#interviewComplete').classList.add('hidden'); $('#interviewActive').classList.remove('hidden');
  $('#interviewRound').textContent=data.round; $('#interviewCounter').textContent=`Question ${data.question_number} of ${data.total_questions} · ${data.difficulty}`; $('#interviewQuestion').textContent=data.question.prompt; $('#interviewAnswer').value='';
}

async function startInterview() {
  try { const data=await api('/api/interview/start',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,tool:$('#interviewTool').value,difficulty:$('#interviewDifficulty').value})}); state.interview={session_id:data.session_id}; setInterviewQuestion(data); speakCurrentQuestion(); }
  catch(e){toast(e.message,true)}
}

function speakCurrentQuestion(){ if(!state.interview?.question||!('speechSynthesis'in window))return; speechSynthesis.cancel(); const u=new SpeechSynthesisUtterance(state.interview.question.prompt);u.rate=.94;u.pitch=1;speechSynthesis.speak(u); }

async function submitInterviewAnswer(){
  const answer=$('#interviewAnswer').value;const question=state.interview?.question?.prompt||'';
  try{
    const result=await api('/api/interview/answer',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,session_id:state.interview.session_id,answer})});
    if(result.completed){$('#interviewActive').classList.add('hidden');const box=$('#interviewComplete');box.classList.remove('hidden');box.innerHTML=`<div class="score-hero ${result.passed?'pass':'fail'}"><strong>${result.score}%</strong><h2>${result.passed?'Interview passed':'More preparation required'}</h2><p>${result.passed?'You demonstrated sufficient overall interview readiness.':'Review weak answers, strengthen evidence, and retry.'}</p></div><button id="restartInterview" class="button secondary wide">Start another interview</button>`;$('#restartInterview').onclick=()=>{box.classList.add('hidden');$('#interviewIdle').classList.remove('hidden')};await loadProgress();return;}
    const feedback=$('#interviewFeedback');feedback.classList.remove('hidden');feedback.innerHTML=`<b>Deterministic score: ${result.answer_score}%</b><p>${escapeHtml(result.feedback)}</p><p class="muted">AI analysis is routing…</p>`;
    try{const ai=await api('/api/v6/ai/interview/analyze',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,session_id:state.interview.session_id,question,answer,deterministic_score:result.answer_score,deterministic_feedback:result.feedback})});feedback.innerHTML=`<b>Deterministic score: ${result.answer_score}%</b><p>${escapeHtml(result.feedback)}</p>${renderAiAnalysis(ai.analysis)}<small class="ai-route-note">Advisory analysis: ${escapeHtml(ai.provider_label)} · ${escapeHtml(ai.model)}</small>`;}catch(aiErr){feedback.insertAdjacentHTML('beforeend',`<small class="muted">Online AI unavailable: ${escapeHtml(aiErr.message)}. Deterministic interview continues.</small>`)}
    setTimeout(()=>{feedback.classList.add('hidden');setInterviewQuestion(result);speakCurrentQuestion()},5200);
  }catch(e){toast(e.message,true)}
}

function dictateAnswer(){const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;if(!Recognition){toast('Speech recognition is not supported by this browser.',true);return}const r=new Recognition();r.lang='en-IN';r.continuous=true;r.interimResults=true;let final='';$('#micButton').textContent='⏹ Listening...';r.onresult=e=>{let interim='';for(let i=e.resultIndex;i<e.results.length;i++){if(e.results[i].isFinal)final+=e.results[i][0].transcript+' ';else interim+=e.results[i][0].transcript}$('#interviewAnswer').value=final+interim};r.onerror=()=>toast('Microphone recognition stopped.',true);r.onend=()=>$('#micButton').textContent='🎙 Dictate';r.start();setTimeout(()=>r.stop(),60000)}

async function importResumeFile() {
  const file = $('#resumeFile').files[0];
  if (!file) { toast('Choose a supported resume file first.', true); return; }
  if (file.size > 3 * 1024 * 1024) { toast('Resume file exceeds the 3 MB import limit.', true); return; }
  $('#importResumeButton').disabled=true; $('#importResumeButton').textContent='Extracting...';
  try {
    const bytes = new Uint8Array(await file.arrayBuffer());
    let binary=''; const chunk=0x8000;
    for(let i=0;i<bytes.length;i+=chunk) binary += String.fromCharCode(...bytes.subarray(i,i+chunk));
    const result = await api('/api/resume/import',{method:'POST',body:JSON.stringify({filename:file.name,content_base64:btoa(binary)})});
    $('#existingResume').value=result.text; toast(`Imported ${result.filename} (${result.characters} characters)`);
  } catch(e) { toast(e.message,true); }
  finally { $('#importResumeButton').disabled=false; $('#importResumeButton').textContent='Extract resume text'; }
}

async function generateResume(event) {
  event.preventDefault(); const f=new FormData(event.target); const experience=[1,2].map(i=>({role:f.get(`role${i}`),company:f.get(`company${i}`),dates:f.get(`dates${i}`),details:f.get(`details${i}`)})).filter(x=>Object.values(x).some(Boolean));
  const payload={student_id:state.currentStudent.id,existing_resume:f.get('existing_resume'),name:f.get('name'),target_title:f.get('target_title'),contact:f.get('contact'),summary:f.get('summary'),skills:f.get('skills'),education:f.get('education'),certifications:f.get('certifications'),projects:f.get('projects'),job_description:f.get('job_description'),experience};
  try { const result=await api('/api/resume/generate',{method:'POST',body:JSON.stringify(payload)});$('#resumeEmpty').classList.add('hidden');$('#resumeOutput').classList.remove('hidden');$('#resumeMatch').textContent=`${result.match_score}%`;$('#resumeNotice').textContent=result.notice;$('#resumeKeywords').innerHTML=`<b>Missing or underrepresented job keywords:</b> ${escapeHtml(result.missing_keywords.join(', ')||'No job description supplied or no significant gap detected.')}`;$('#resumePreview').srcdoc=result.html;$('#downloadHtml').href=`/api/resume/download?id=${encodeURIComponent(result.id)}&format=html`;$('#downloadDoc').href=`/api/resume/download?id=${encodeURIComponent(result.id)}&format=doc`;$('#downloadTxt').href=`/api/resume/download?id=${encodeURIComponent(result.id)}&format=txt`;await loadProgress();toast('ATS resume generated'); }
  catch(e){toast(e.message,true)}
}

async function syncOnline() {
  $('#syncOnline').disabled=true;$('#syncOnline').textContent='Syncing...';
  try {const result=await api('/api/online/sync',{method:'POST',body:JSON.stringify({tool:$('#onlineTool').value,tag:$('#onlineTag').value,limit:Number($('#onlineCount').value)})});const box=$('#onlineResult');box.classList.remove('hidden');box.innerHTML=`<h2>✓ Sync complete</h2><p>${escapeHtml(result.message)}</p><p>Tag: <b>${escapeHtml(result.tag||'')}</b>. Enable “include internet-synced questions” in the Test Center.</p>`;toast(result.message)}catch(e){toast(e.message,true)}finally{$('#syncOnline').disabled=false;$('#syncOnline').textContent='Sync attributed questions'}
}

async function loadHistory(){if(!state.currentStudent)return;try{const data=await api(`/api/history?student_id=${state.currentStudent.id}`);$('#historyList').innerHTML=data.history.length?data.history.map(x=>`<div class="history-item"><strong>${escapeHtml(x.action.replaceAll('_',' '))}</strong><span>${escapeHtml(x.detail)}</span><time>${new Date(x.created_at).toLocaleString()}</time></div>`).join(''):'<div class="empty-state"><h2>No activity yet</h2></div>'}catch(e){toast(e.message,true)}}

function bindEvents() {
  $$('.nav-item,.go-page').forEach(b=>b.addEventListener('click',()=>showPage(b.dataset.page)));
  $('#menuButton').addEventListener('click',()=>{
    const open=$('#sidebar').classList.toggle('open');
    document.body.classList.toggle('nav-open',open);
    $('#menuButton').setAttribute('aria-expanded',String(open));
  });
  $('#menuClose')?.addEventListener('click',closeStudioNav);
  $('#navScrim')?.addEventListener('click',closeStudioNav);
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&$('#sidebar')?.classList.contains('open'))closeStudioNav()});
  $$('.scroll-cue').forEach(b=>b.addEventListener('click',()=>document.getElementById(b.dataset.scrollTarget)?.scrollIntoView({behavior:'smooth'})));
  $('#toolSearch').addEventListener('input',renderToolGrid);
  $('#addStudentButton').addEventListener('click',()=>$('#studentDialog').showModal());
  $('#closeToolDialog').addEventListener('click',()=>$('#toolDialog').close());
  $('#studentSelect').addEventListener('change',async e=>{const student=state.students.find(s=>s.id===Number(e.target.value));if(student)await activateStudent(student)});
  $('#studentForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target);try{await api('/api/students',{method:'POST',body:JSON.stringify({name:f.get('name'),email:f.get('email'),pin:f.get('pin')})});$('#studentDialog').close();e.target.reset();await loadStudents();toast('Student profile created')}catch(err){toast(err.message,true)}});
  $('#pinForm').addEventListener('submit',async e=>{e.preventDefault();try{const d=await api('/api/v4/student/session',{method:'POST',body:JSON.stringify({student_id:state.pendingStudent.id,pin:$('#pinInput').value})});$('#pinDialog').close();const s=state.pendingStudent;state.pendingStudent=null;await activateStudent({...s,pin_protected:false,_sessionToken:d.token});}catch(err){$('#pinError').textContent=err.message}});
  $('#practiceTool').addEventListener('change',refreshPracticeLabs);$('#practiceLevel').addEventListener('change',refreshPracticeLabs);$('#submitPractice').addEventListener('click',submitPractice);
  $('#startTest').addEventListener('click',startTest);$('#submitTest').addEventListener('click',submitTest);
  $('#startInterview').addEventListener('click',startInterview);$('#submitInterviewAnswer').addEventListener('click',submitInterviewAnswer);$('#speakQuestion').addEventListener('click',speakCurrentQuestion);$('#micButton').addEventListener('click',dictateAnswer);
  $('#resumeForm').addEventListener('submit',generateResume);$('#importResumeButton').addEventListener('click',importResumeFile);$('#syncOnline').addEventListener('click',syncOnline);
}

async function init() {
  bindEvents(); bindV2Events(); bindV3Events(); bindV4Events(); bindV26Events(); bindV27Events(); bindV28DisplayEvents();
  try { await loadCatalog(); await loadStudents(); await loadV23Status(); initVfxTilt(); initStudioExperience(); }
  catch(e){toast(`Startup failed: ${e.message}`,true)}
}

document.addEventListener('DOMContentLoaded',init);

// ---------------- Billinger v2: Real Company Edition ----------------
function rubricMarkup(rubric={}) {
  return `<div class="rubric-grid">${Object.entries(rubric).map(([k,v])=>`<div><span>${escapeHtml(k.replaceAll('_',' '))}</span><b>${Math.round(v)}%</b><i><em style="width:${Math.min(100,v)}%"></em></i></div>`).join('')}</div>`;
}

async function loadCompany() {
  if (!state.currentStudent) return;
  try {
    const data=await api(`/api/v2/company?student_id=${state.currentStudent.id}`); state.companyData=data;
    $('#managerMessage').textContent=data.manager_message;
    $('#companyTicketsPassed').textContent=data.performance.tickets_passed;
    $('#companyAttempts').textContent=`${data.performance.attempts} attempts`;
    $('#companyAverage').textContent=`${data.performance.average_score}%`;
    $('#serviceHealth').innerHTML=data.service_health.map(s=>`<div><span class="health-dot ${s.status}"></span><b>${escapeHtml(s.name)}</b><small>${escapeHtml(s.status)} · ${escapeHtml(s.latency)} · SLO ${escapeHtml(s.slo)}</small></div>`).join('');
    $('#companyTicketList').innerHTML=data.recommended_tickets.map(t=>`<button class="ticket-button" data-ticket="${t.id}"><span><b>${escapeHtml(t.id)}</b> ${escapeHtml(t.title)}</span><small>${escapeHtml(t.level)} · ${escapeHtml(t.priority)} · ${t.sla_minutes} min SLA</small></button>`).join('');
    $('#incidentList').innerHTML=data.active_incidents.map(i=>`<button class="ticket-button incident" data-incident="${i.id}"><span><b>${escapeHtml(i.severity)}</b> ${escapeHtml(i.title)}</span><small>${escapeHtml(i.customer_impact)}</small></button>`).join('');
    $$('[data-ticket]').forEach(b=>b.onclick=()=>selectCompanyTicket(data.recommended_tickets.find(t=>t.id===b.dataset.ticket),b));
    $$('[data-incident]').forEach(b=>b.onclick=()=>selectIncident(data.active_incidents.find(i=>i.id===b.dataset.incident),b));
  } catch(e){toast(e.message,true)}
}

function clearCompanySelection(button) { $$('.ticket-button').forEach(b=>b.classList.toggle('active',b===button)); $('#companyEmpty').classList.add('hidden'); $('#companyResult').classList.add('hidden'); $('#incidentResult').classList.add('hidden'); }
function selectCompanyTicket(ticket,button) {
  state.companyTicket=ticket; state.companyIncident=null; clearCompanySelection(button);
  $('#incidentWorkspace').classList.add('hidden'); $('#companyTicketWorkspace').classList.remove('hidden');
  $('#companyTicketId').textContent=ticket.id; $('#companyPriority').textContent=ticket.priority; $('#companyTicketTitle').textContent=ticket.title;
  $('#companyScenario').textContent=ticket.scenario; $('#companyImpact').textContent=ticket.business_impact; $('#companyWorkflow').textContent=ticket.company_workflow;
  $('#companyCriteria').innerHTML=ticket.acceptance_criteria.map(x=>`<li>${escapeHtml(x)}</li>`).join(''); $('#companyResponse').value=''; $('#companyStandup').value='';
}
function selectIncident(incident,button) {
  state.companyIncident=incident; state.companyTicket=null; clearCompanySelection(button);
  $('#companyTicketWorkspace').classList.add('hidden'); $('#incidentWorkspace').classList.remove('hidden');
  $('#incidentSeverity').textContent=incident.severity; $('#incidentTitle').textContent=incident.title; $('#incidentSymptoms').textContent=`${incident.symptoms} ${incident.recent_change}`;
  $('#incidentSignals').innerHTML=incident.signals.map(x=>`<span>${escapeHtml(x)}</span>`).join(''); $('#incidentResponse').value='';
}
async function submitCompanyTicket() {
  if(!state.companyTicket)return;
  try {const r=await api('/api/v2/company/ticket/submit',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,ticket_id:state.companyTicket.id,response:$('#companyResponse').value,standup:$('#companyStandup').value})});const box=$('#companyResult');box.className=`result-card ${r.passed?'pass':'fail'}`;box.innerHTML=`<h3>${r.passed?'✓ Senior review passed':'↻ Changes requested'} · ${r.score}%</h3><p>${escapeHtml(r.feedback)}</p>${rubricMarkup(r.rubric)}`;await loadCompany();toast(r.passed?'Company ticket passed':'Reviewer feedback generated');}catch(e){toast(e.message,true)}
}
async function submitIncident() {
  if(!state.companyIncident)return;
  try {const r=await api('/api/v2/company/incident/submit',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,incident_id:state.companyIncident.id,response:$('#incidentResponse').value})});const box=$('#incidentResult');box.className=`result-card ${r.passed?'pass':'fail'}`;box.innerHTML=`<h3>${r.passed?'✓ Incident review passed':'⚠ Operational gaps found'} · ${r.score}%</h3><p>${escapeHtml(r.feedback)}</p>${rubricMarkup(r.rubric)}`;toast('Incident review completed');}catch(e){toast(e.message,true)}
}

async function runTerminal(event) {
  event.preventDefault(); const command=$('#terminalCommand').value.trim(); if(!command)return;
  const out=$('#terminalOutput'); out.textContent += `\n$ ${command}\n`;
  try {const r=await api('/api/v2/lab/run',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,command,mode:$('#labMode').value})});out.textContent+=`${r.output}\n[exit ${r.exit_code}]\n`;$('#terminalSafety').textContent=`${r.safety} · ${r.workspace}`;}catch(e){out.textContent+=`BLOCKED: ${e.message}\n`;toast(e.message,true)}
  out.scrollTop=out.scrollHeight; $('#terminalCommand').value='';
}

async function loadSkills() {
  if(!state.currentStudent)return;
  try {const data=await api(`/api/v2/skills?student_id=${state.currentStudent.id}`);$('#skillRecommendation').textContent=data.recommendation;$('#skillTableBody').innerHTML=data.tools.map(t=>`<tr><td><b>${t.icon} ${escapeHtml(t.name)}</b></td>${['knowledge','practice','test','interview','company','overall'].map(k=>`<td><span class="score-cell"><i style="width:${t[k]}%"></i><b>${Math.round(t[k])}</b></span></td>`).join('')}<td><span class="pill">${escapeHtml(t.level)}</span></td></tr>`).join('');}catch(e){toast(e.message,true)}
}

function setRecruitmentQuestion(data) {
  state.recruitment={...state.recruitment,...data}; $('#recruitmentIdle').classList.add('hidden');$('#recruitmentComplete').classList.add('hidden');$('#recruitmentActive').classList.remove('hidden');$('#recruitmentRound').textContent=data.round;$('#recruitmentCounter').textContent=`Round ${data.question_number} of ${data.total_questions} · ${data.target_role||state.recruitment.target_role||''}`;$('#recruitmentQuestion').textContent=data.question.prompt;$('#recruitmentAnswer').value='';
}
async function startRecruitment() {
  try {const data=await api('/api/v2/recruitment/start',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,target_role:$('#recruitmentRole').value,track:$('#recruitmentTrack').value,difficulty:$('#recruitmentDifficulty').value,resume_text:$('#recruitmentResume').value,job_description:$('#recruitmentJob').value})});state.recruitment={session_id:data.session_id,target_role:data.target_role};setRecruitmentQuestion(data);speakRecruitment();}catch(e){toast(e.message,true)}
}
async function submitRecruitment() {
  const answer=$('#recruitmentAnswer').value;
  const currentQuestion=state.recruitment?.question?.prompt||'';
  try {
    const r=await api('/api/v2/recruitment/answer',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,session_id:state.recruitment.session_id,answer})});
    let advisory='';
    try{
      const ai=await api('/api/v6/ai/interview/analyze',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,session_id:state.recruitment.session_id,question:currentQuestion,answer,deterministic_score:r.answer_score||r.score||0,deterministic_feedback:r.feedback||r.recommendation||'',context:{target_role:state.recruitment.target_role||'',round:r.round||'',job_description:$('#recruitmentJob').value,resume_text:$('#recruitmentResume').value}})});
      advisory=`<div class="ai-analysis-box"><div class="ai-result-head"><span class="pill">AI panel advisory</span><b>${escapeHtml(ai.provider_label)} · ${escapeHtml(ai.model)}</b></div>${renderAiAnalysis(ai.analysis)}</div>`;
    }catch(aiErr){advisory=`<p class="muted">Online AI advisory unavailable: ${escapeHtml(aiErr.message)}. Fixed-rubric scoring remains authoritative.</p>`}
    if(r.completed){
      $('#recruitmentActive').classList.add('hidden');
      const box=$('#recruitmentComplete');box.classList.remove('hidden');
      box.innerHTML=`<div class="score-hero ${r.passed?'pass':'fail'}"><strong>${r.score}%</strong><h2>${r.passed?'Recruitment journey passed':'Further preparation required'}</h2><p>${escapeHtml(r.recommendation)}</p></div>${advisory}<div class="round-report">${r.round_scores.map(x=>`<div><span>${escapeHtml(x.round)}</span><b>${x.score}%</b></div>`).join('')}</div><h3>Weakest rounds</h3>${r.weak_rounds.map(x=>`<p><b>${escapeHtml(x.round)} · ${x.score}%</b><br><small>${escapeHtml((x.missing||[]).join(', ')||'Add more specific evidence and outcomes.')}</small></p>`).join('')}`;
      return;
    }
    const f=$('#recruitmentFeedback');f.classList.remove('hidden');
    f.innerHTML=`<b>Fixed-rubric round score: ${r.answer_score}%</b><p>${escapeHtml(r.feedback)}</p>${rubricMarkup(r.rubric)}${advisory}`;
    setTimeout(()=>{f.classList.add('hidden');setRecruitmentQuestion(r);speakRecruitment()},5200);
  }catch(e){toast(e.message,true)}
}
function speakRecruitment(){if(!state.recruitment?.question||!('speechSynthesis'in window))return;speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(state.recruitment.question.prompt);u.rate=.94;speechSynthesis.speak(u)}
function dictateInto(selector,buttonSelector){const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;if(!Recognition){toast('Speech recognition is not supported by this browser.',true);return}const r=new Recognition();r.lang='en-IN';r.continuous=true;r.interimResults=true;let final='';const btn=$(buttonSelector);btn.textContent='⏹ Listening...';r.onresult=e=>{let interim='';for(let i=e.resultIndex;i<e.results.length;i++){if(e.results[i].isFinal)final+=e.results[i][0].transcript+' ';else interim+=e.results[i][0].transcript}$(selector).value=final+interim};r.onend=()=>btn.textContent='🎙 Dictate';r.start();setTimeout(()=>r.stop(),60000)}

async function loadReadiness() {
  try {const r=await api('/api/v2/readiness');const items=[['Core',r.core],['Git',r.git],['WSL',r.wsl],['Docker',r.docker],['kubectl',r.kubectl],['Terraform',r.terraform],['Local AI',r.local_ai]];$('#readinessCards').innerHTML=items.map(([name,x])=>`<article class="panel readiness-item ${x.ready?'ready':'optional'}"><span>${x.ready?'✓':'○'}</span><div><b>${name}</b><small>${escapeHtml(x.detail)}</small></div></article>`).join('');const s=r.settings;$('#settingsLabMode').value=s.lab_mode||'simulator';$('#labMode').value=s.lab_mode||'simulator';$('#wslDistribution').value=s.wsl_distribution||'';$('#aiEnabled').checked=!!s.ai_enabled;$('#aiEndpoint').value=s.ai_endpoint||'';$('#aiModel').value=s.ai_model||'local-model';}catch(e){toast(e.message,true)}
}
async function saveV2Settings(event){event.preventDefault();try{const r=await api('/api/v2/settings',{method:'POST',body:JSON.stringify({lab_mode:$('#settingsLabMode').value,wsl_distribution:$('#wslDistribution').value,ai_enabled:$('#aiEnabled').checked,ai_endpoint:$('#aiEndpoint').value,ai_model:$('#aiModel').value})});$('#labMode').value=r.lab_mode;toast('Local settings saved');await loadReadiness();}catch(e){toast(e.message,true)}}
async function askLocalAI(event){event.preventDefault();const prompt=$('#aiPrompt').value.trim();if(!prompt||!state.currentStudent)return;$('#aiChat').insertAdjacentHTML('beforeend',`<div class="chat-bubble user">${escapeHtml(prompt)}</div>`);$('#aiPrompt').value='';const pending=document.createElement('div');pending.className='chat-bubble bot';pending.textContent='Routing to the best available AI…';$('#aiChat').appendChild(pending);try{const r=await api('/api/v6/ai/chat',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,messages:[{role:'user',content:prompt}]})});pending.innerHTML=`${escapeHtml(r.content).replace(/\n/g,'<br>')}<small class="ai-route-note">${escapeHtml(r.provider_label)} · ${escapeHtml(r.model)}${r.fallback_trace?.length?` · ${r.fallback_trace.length} fallback step(s)`:''}</small>`;}catch(e){pending.className='chat-bubble error';pending.textContent=e.message;toast(e.message,true)}$('#aiChat').scrollTop=$('#aiChat').scrollHeight}

async function loadProgramLibrary() {
  try {
    const data = await api(`/api/resources?collection=program&student_id=${state.currentStudent?.id||0}`);
    state.programLibrary = data.resources;
    $('#programLibraryCount').textContent = `${data.count} program resources`;
    $('#programLibraryGrid').innerHTML = data.resources.map(programResourceCard).join('') || '<div class="panel empty-state"><h2>No program guides found</h2></div>';
    $$('.program-resource-open').forEach(btn=>btn.addEventListener('click',()=>openProgramResource(btn.dataset.resource)));
    filterProgramLibrary();
  } catch(e) { toast(e.message,true); }
}
function filterProgramLibrary(){const q=($('#programLibrarySearch')?.value||'').trim().toLowerCase();$$('[data-program-card]').forEach(card=>card.classList.toggle('hidden',q&&!card.dataset.programSearch.includes(q)))}
async function openProgramResource(resourceId){
  try{
    const resource=await api(`/api/resource?id=${encodeURIComponent(resourceId)}`);state.programResource=resource;state.programPageIndex=0;
    $('#programReaderLabel').textContent=resource.library_label||resource.volume;$('#programReaderTitle').textContent=resource.title;$('#programReaderSummary').textContent=resource.summary||'';$('#programReaderRationale').textContent=resource.classification_rationale||'';
    $('#programOpenPdf').href=resource.links.pdf;$('#programOpenDocx').href=resource.links.docx;$('#programPdfFrame').src=resource.links.pdf;
    $('#programPageSelect').innerHTML=resource.pages.map((page,index)=>`<option value="${index}">${page.page}</option>`).join('');$('#programPageCount').textContent=`${resource.pages.length} extracted pages`;
    $('#programAnswer').classList.add('hidden');$('#programAnswer').innerHTML='';$('#programQuestion').value='';showProgramPane('pdf');renderProgramPage();$('#programReaderDialog').showModal();
  }catch(e){toast(e.message,true)}
}
function showProgramPane(mode){const pdf=mode==='pdf';$('#programPdfPane').classList.toggle('hidden',!pdf);$('#programTextPane').classList.toggle('hidden',pdf);$('#programPdfTab').classList.toggle('primary',pdf);$('#programPdfTab').classList.toggle('secondary',!pdf);$('#programTextTab').classList.toggle('primary',!pdf);$('#programTextTab').classList.toggle('secondary',pdf)}
function renderProgramPage(){const r=state.programResource;if(!r?.pages?.length)return;state.programPageIndex=Math.max(0,Math.min(state.programPageIndex,r.pages.length-1));const p=r.pages[state.programPageIndex];$('#programPageSelect').value=String(state.programPageIndex);$('#programPageText').innerHTML=`<div class="resource-page-label">Page ${p.page}</div><p>${escapeHtml(p.text).replace(/\n\n+/g,'</p><p>').replace(/\n/g,'<br>')}</p>`;$('#programPrevPage').disabled=state.programPageIndex===0;$('#programNextPage').disabled=state.programPageIndex===r.pages.length-1}
async function askProgramResource(event){event.preventDefault();const q=$('#programQuestion').value.trim();if(!q||!state.programResource)return;const box=$('#programAnswer');box.className='resource-answer';box.innerHTML='<div class="resource-thinking">Searching the selected document…</div>';try{const result=await api('/api/resource/ask',{method:'POST',body:JSON.stringify({student_id:state.currentStudent?.id||0,resource_id:state.programResource.id,question:q})});const sources=(result.sources||[]).map(s=>`<blockquote><b>Page ${s.page}</b><br>${escapeHtml(s.text)}</blockquote>`).join('');box.innerHTML=`<span class="pill">${escapeHtml(result.mode==='local_ai'?'Local AI + sources':'Source retrieval')}</span><div class="resource-answer-text">${escapeHtml(result.answer).replace(/\n/g,'<br>')}</div>${sources?`<details open><summary>Supporting passages</summary>${sources}</details>`:''}`;}catch(e){box.className='resource-answer error';box.textContent=e.message}}
async function markProgramReviewed(){if(!state.currentStudent||!state.programResource)return;try{await api('/api/resource/progress',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,resource_id:state.programResource.id,completed:true})});$('#programMarkComplete').textContent='✓ Reviewed';toast('Program document marked reviewed');loadProgramLibrary()}catch(e){toast(e.message,true)}}

async function loadCoverage(force=false) {
  try {
    if (!state.coverage || force) state.coverage = await api('/api/v2/coverage');
    const data = state.coverage;
    $('#coverageNotice').innerHTML = `<strong>Coverage statement</strong><p>${escapeHtml(data.scope_notice)}</p>`;
    const labels = {domains:'Domains',levels:'Level tracks',lessons:'Lessons',practice_labs:'Practice labs',command_examples:'Command examples',unique_command_examples:'Unique examples',test_questions:'Test questions',interview_questions:'Interview questions',company_tickets:'Company tickets',incidents:'Incidents',capstones:'Capstones'};
    $('#coverageStats').innerHTML = Object.entries(data.summary).map(([key,value])=>`<article class="panel coverage-stat"><small>${escapeHtml(labels[key]||key.replaceAll('_',' '))}</small><strong>${value}</strong></article>`).join('');
    const filter = $('#coverageToolFilter');
    if (filter.options.length <= 1) data.tools.forEach(t=>filter.add(new Option(`${t.icon} ${t.name}`,t.slug)));
    const subcommands = Object.entries(data.safe_lab.restricted_subcommands).map(([cmd,subs])=>`<div><b>${escapeHtml(cmd)}</b><code>${escapeHtml(subs.join(', '))}</code></div>`).join('');
    $('#safeLabCoverage').innerHTML = `<div><span class="eyebrow">EXECUTABLE SAFETY BOUNDARY</span><h2>Safe Real Lab allowlist</h2><p>${escapeHtml(data.safe_lab.notice)}</p></div><details><summary>${data.safe_lab.executables.length} allowed executable names</summary><div class="command-cloud">${data.safe_lab.executables.map(x=>`<code>${escapeHtml(x)}</code>`).join('')}</div></details><div class="subcommand-grid">${subcommands}</div>`;
    renderCoverage();
  } catch(e) { toast(e.message,true); }
}

function renderCoverage() {
  if (!state.coverage) return;
  const query = ($('#coverageSearch').value || '').trim().toLowerCase();
  const selected = $('#coverageToolFilter').value || 'all';
  const results = state.coverage.tools.filter(t => {
    if (selected !== 'all' && t.slug !== selected) return false;
    const searchable = JSON.stringify(t).toLowerCase();
    return !query || searchable.includes(query);
  });
  $('#coverageResults').innerHTML = results.map(t=>`<details class="panel coverage-tool" ${selected===t.slug?'open':''}>
    <summary><span class="coverage-tool-title"><b>${t.icon} ${escapeHtml(t.name)}</b><small>${escapeHtml(t.category)}</small></span><span class="coverage-counts">${t.lesson_count} lessons · ${t.lab_count} labs · ${t.unique_command_count} command/example snippets · ${t.tickets.length} tickets · ${t.incidents.length} incident · ${t.test_question_count} tests · ${t.interview_question_count} interviews · ${(t.learning_resources||[]).length} verified books</span></summary>
    <div class="coverage-body"><p>${escapeHtml(t.description)}</p><p><b>Why companies use it:</b> ${escapeHtml(t.why_company)}</p>
      <h3>Verified primary-tool PDF/DOCX books</h3><div class="coverage-scenario">${(t.learning_resources||[]).map(x=>`<div><b>${escapeHtml(x.volume)} · ${escapeHtml(x.title)}</b><small>${x.page_count} PDF pages</small></div>`).join('') || '<span class="muted">No imported book assigned.</span>'}</div><h3>Included command and configuration examples</h3><div class="command-cloud">${t.command_examples.map(x=>`<code>${escapeHtml(x)}</code>`).join('') || '<span class="muted">No command examples.</span>'}</div>
      <h3>Learning and practice by level</h3>${t.levels.map(l=>`<details class="coverage-level"><summary><b>${escapeHtml(l.name)}</b><span>${l.lesson_titles.length} lessons · ${l.labs.length} lab</span></summary><p><b>Company workflow:</b> ${escapeHtml(l.company_workflow)}</p><p><b>Lessons:</b> ${escapeHtml(l.lesson_titles.join(' · '))}</p>${l.labs.map(x=>`<div class="coverage-scenario"><b>${escapeHtml(x.title)}</b><p>${escapeHtml(x.scenario)}</p></div>`).join('')}</details>`).join('')}
      <div class="coverage-columns"><section><h3>Company tickets</h3>${t.tickets.map(x=>`<div class="coverage-scenario"><b>${escapeHtml(x.id)} · ${escapeHtml(x.level)} · ${escapeHtml(x.title)}</b><p>${escapeHtml(x.scenario)}</p><small>${escapeHtml(x.business_impact)}</small></div>`).join('')}</section><section><h3>Production incident</h3>${t.incidents.map(x=>`<div class="coverage-scenario danger-outline"><b>${escapeHtml(x.severity)} · ${escapeHtml(x.title)}</b><p>${escapeHtml(x.symptoms)}</p><small>${escapeHtml(x.customer_impact)}</small></div>`).join('')}<h3>Enterprise capstone</h3>${t.capstones.map(x=>`<div class="coverage-scenario"><b>${escapeHtml(x.title)}</b><p>${escapeHtml(x.brief)}</p></div>`).join('')}</section></div>
    </div></details>`).join('') || '<div class="panel empty-state"><h2>No coverage item matches this search</h2><p>Try a command name, technology, incident, or company workflow term.</p></div>';
}

function bindV2Events(){
  $('#refreshCompany')?.addEventListener('click',loadCompany);$('#submitCompanyTicket')?.addEventListener('click',submitCompanyTicket);$('#submitIncident')?.addEventListener('click',submitIncident);
  $('#terminalForm')?.addEventListener('submit',runTerminal);$$('.command-example').forEach(b=>b.addEventListener('click',()=>{$('#terminalCommand').value=b.dataset.command;$('#terminalCommand').focus()}));
  $('#refreshSkills')?.addEventListener('click',loadSkills);$('#startRecruitment')?.addEventListener('click',startRecruitment);$('#submitRecruitment')?.addEventListener('click',submitRecruitment);$('#speakRecruitment')?.addEventListener('click',speakRecruitment);$('#recruitmentMic')?.addEventListener('click',()=>dictateInto('#recruitmentAnswer','#recruitmentMic'));
  $('#submitCapstone')?.addEventListener('click',submitCapstone);
  $('#refreshReadiness')?.addEventListener('click',loadReadiness);$('#settingsForm')?.addEventListener('submit',saveV2Settings);$('#aiChatForm')?.addEventListener('submit',askLocalAI);
  $('#refreshCoverage')?.addEventListener('click',()=>loadCoverage(true));$('#coverageSearch')?.addEventListener('input',renderCoverage);$('#coverageToolFilter')?.addEventListener('change',renderCoverage);
  $('#programLibrarySearch')?.addEventListener('input',filterProgramLibrary);$('#programReaderClose')?.addEventListener('click',()=>{$('#programReaderDialog').close();$('#programPdfFrame').src='about:blank'});$('#programPdfTab')?.addEventListener('click',()=>showProgramPane('pdf'));$('#programTextTab')?.addEventListener('click',()=>showProgramPane('text'));$('#programPrevPage')?.addEventListener('click',()=>{state.programPageIndex--;renderProgramPage()});$('#programNextPage')?.addEventListener('click',()=>{state.programPageIndex++;renderProgramPage()});$('#programPageSelect')?.addEventListener('change',e=>{state.programPageIndex=Number(e.target.value);renderProgramPage()});$('#programAskForm')?.addEventListener('submit',askProgramResource);$('#programMarkComplete')?.addEventListener('click',markProgramReviewed);
}

async function loadCapstones(){
  try{const data=await api('/api/v2/capstones');state.capstones=data.capstones;$('#capstoneList').innerHTML=data.capstones.map(c=>`<button class="lab-button" data-capstone="${c.id}">${escapeHtml(c.title)}<small>${escapeHtml(c.brief.slice(0,90))}...</small></button>`).join('');$$('[data-capstone]').forEach(b=>b.onclick=()=>selectCapstone(data.capstones.find(c=>c.id===b.dataset.capstone),b));}catch(e){toast(e.message,true)}
}
function selectCapstone(c,b){state.capstone=c;$$('[data-capstone]').forEach(x=>x.classList.toggle('active',x===b));$('#capstoneEmpty').classList.add('hidden');$('#capstoneWorkspace').classList.remove('hidden');$('#capstoneId').textContent=c.id;$('#capstoneTitle').textContent=c.title;$('#capstoneBrief').textContent=c.brief;$('#capstoneMilestones').innerHTML=c.milestones.map(x=>`<li>${escapeHtml(x)}</li>`).join('');$('#capstoneOutcomes').innerHTML=c.outcomes.map(x=>`<li>${escapeHtml(x)}</li>`).join('');$('#capstoneSubmission').value='';$('#capstoneResult').classList.add('hidden')}
async function submitCapstone(){if(!state.capstone)return;try{const r=await api('/api/v2/capstone/submit',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,capstone_id:state.capstone.id,submission:$('#capstoneSubmission').value})});const box=$('#capstoneResult');box.className=`result-card ${r.passed?'pass':'fail'}`;box.innerHTML=`<h3>${r.passed?'✓ Enterprise review passed':'↻ Capstone changes required'} · ${r.score}%</h3><p>${escapeHtml(r.feedback)}</p>${rubricMarkup(r.rubric)}`;toast('Capstone reviewed')}catch(e){toast(e.message,true)}}

// ---------------- Billinger v2.3: Training Institute 3D Edition ----------------
const adminToken = () => storageGet('billingerAdminToken') || '';
async function adminApi(path, options={}) {
  const headers = {'Content-Type':'application/json','X-Admin-Token':adminToken(), ...(options.headers||{})};
  return api(path,{...options,headers});
}
function bytesLabel(n=0){if(n<1024)return `${n} B`;if(n<1048576)return `${(n/1024).toFixed(1)} KB`;if(n<1073741824)return `${(n/1048576).toFixed(1)} MB`;return `${(n/1073741824).toFixed(2)} GB`}
async function fileBase64(file,maxMB=75){if(!file)throw new Error('Choose a file first.');if(file.size>maxMB*1024*1024)throw new Error(`File exceeds the ${maxMB} MB limit.`);const bytes=new Uint8Array(await file.arrayBuffer());let binary='';const chunk=0x8000;for(let i=0;i<bytes.length;i+=chunk)binary+=String.fromCharCode(...bytes.subarray(i,i+chunk));return btoa(binary)}

async function loadV23Status(){
  try{state.v23Status=await api('/api/v3/status');const setup=!state.v23Status.admin.configured;$('#adminDialogTitle').textContent=setup?'Configure Administrator':'Unlock Admin Control';$('#adminSetupFields').classList.toggle('hidden',!setup);$('#adminAuthSubmit').textContent=setup?'Create administrator':'Unlock';}
  catch(e){console.warn(e)}
}

async function loadMyDay(){
  if(!state.currentStudent)return;
  try{
    const d=await api(`/api/v3/student/hub?student_id=${state.currentStudent.id}`);state.studentHub=d;
    $('#myDayInitial').textContent=(state.currentStudent.name||'S').trim().charAt(0).toUpperCase();$('#myDayStudent').textContent=state.currentStudent.name;$('#myDayRole').textContent=d.profile.target_role||'DevOps Engineer';
    const role=$('#myDayRoleSelect');if(!role.options.length)d.role_tracks.forEach(x=>role.add(new Option(x,x)));role.value=d.profile.target_role||'DevOps Engineer';$('#myDayMinutes').value=d.profile.study_minutes||90;$('#myDayInterviewDate').value=d.profile.interview_date||'';
    $('#myDayDate').textContent=new Date(`${d.today.date}T00:00:00`).toLocaleDateString(undefined,{weekday:'long',day:'numeric',month:'long'});$('#myDayTotal').textContent=d.today.study_minutes;
    $('#dailyPlanList').innerHTML=d.today.items.map(x=>`<div class="daily-plan-item"><span>${String(x.order).padStart(2,'0')}</span><div><h3>${escapeHtml(x.title)}</h3><p>${escapeHtml(x.tool_name)} · ${escapeHtml(x.type)}</p></div><time>${x.minutes} min</time></div>`).join('');
    $('#dependencyRoadmap').innerHTML=d.roadmap.items.map(x=>`<article class="dependency-node ${x.status}"><span>${x.icon}</span><strong>${escapeHtml(x.name)}</strong><small>${x.status==='locked'?`Needs: ${x.missing_prerequisites.map(p=>state.catalog.find(t=>t.slug===p)?.name||p).join(', ')}`:x.status==='completed'?'Mastery path completed':'Available now'}</small><div class="node-meter"><i style="width:${x.completion}%"></i></div><small>${x.completion}% complete</small></article>`).join('');
    $('#myAssignments').innerHTML=d.assignments.length?d.assignments.map(x=>`<div class="assignment-card"><b>${escapeHtml(x.title)}</b><small>${escapeHtml(x.item_type)}${x.due_date?` · Due ${escapeHtml(x.due_date)}`:''}</small><p>${escapeHtml(x.instructions||'')}</p></div>`).join(''):'<div class="empty-state compact"><p>No batch assignments yet.</p></div>';
    $('#myAnnouncements').innerHTML=d.announcements.length?d.announcements.map(x=>`<div class="announcement-card"><b>${escapeHtml(x.title)}</b><small>${new Date(x.created_at).toLocaleString()}</small><p>${escapeHtml(x.message)}</p></div>`).join(''):'<div class="empty-state compact"><p>No institute announcements yet.</p></div>';
  }catch(e){toast(e.message,true)}
}
async function saveMyProfile(){if(!state.currentStudent)return;try{await api('/api/v3/profile/save',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,target_role:$('#myDayRoleSelect').value,study_minutes:Number($('#myDayMinutes').value),interview_date:$('#myDayInterviewDate').value,active_track:'Full DevOps Track'})});toast('Learning profile saved');await loadMyDay()}catch(e){toast(e.message,true)}}
async function regeneratePlan(){if(!state.currentStudent)return;try{await api('/api/v3/plan/generate',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id})});await loadMyDay();toast('Today’s plan regenerated')}catch(e){toast(e.message,true)}}

async function loadPracticalTemplates(){
  if(!state.catalog.length)return;try{const qs=new URLSearchParams({tool:$('#practicalTool').value,level:$('#practicalLevel').value});const d=await api(`/api/v3/practical/templates?${qs}`);state.practicalTemplates=d.templates;$('#practicalTemplateList').innerHTML=d.templates.map(x=>`<button class="practical-card" data-exam-code="${escapeHtml(x.exam_code)}"><b>${x.icon} ${escapeHtml(x.title)}</b><small>${x.duration_minutes} min · ${escapeHtml(x.exam_code)}</small></button>`).join('');$$('[data-exam-code]').forEach(b=>b.onclick=()=>selectPractical(d.templates.find(x=>x.exam_code===b.dataset.examCode),b));}catch(e){toast(e.message,true)}}
function selectPractical(x,b){state.selectedPractical=x;$$('[data-exam-code]').forEach(n=>n.classList.toggle('active',n===b));$('#practicalIdle').classList.add('hidden');$('#practicalRunner').classList.add('hidden');$('#practicalPreview').classList.remove('hidden');$('#practicalCode').textContent=x.exam_code;$('#practicalTitle').textContent=x.title;$('#practicalScenario').textContent=x.scenario;$('#practicalRequirements').innerHTML=x.requirements.map(r=>`<li>${escapeHtml(r)}</li>`).join('')}
async function startPractical(){if(!state.selectedPractical||!state.currentStudent)return;try{const r=await api('/api/v3/practical/start',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,exam_code:state.selectedPractical.exam_code})});state.practicalRun=r;$('#practicalPreview').classList.add('hidden');$('#practicalRunner').classList.remove('hidden');$('#practicalActiveCode').textContent=r.exam_code;$('#practicalActiveTitle').textContent=r.title;$('#practicalActiveScenario').textContent=r.scenario;$('#practicalResponse').value='';$('#practicalResult').classList.add('hidden');startPracticalClock(r.expires_at)}catch(e){toast(e.message,true)}}
function startPracticalClock(expires){clearInterval(state.practicalTimerId);const tick=()=>{const seconds=Math.max(0,Math.floor((new Date(expires)-Date.now())/1000));$('#practicalTimer').textContent=`${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}`;if(seconds<=0)clearInterval(state.practicalTimerId)};tick();state.practicalTimerId=setInterval(tick,1000)}
async function submitPractical(){if(!state.practicalRun)return;try{const r=await api('/api/v3/practical/submit',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,run_id:state.practicalRun.run_id,response:$('#practicalResponse').value})});clearInterval(state.practicalTimerId);const box=$('#practicalResult');box.className=`result-card ${r.passed?'pass':'fail'}`;box.innerHTML=`<h2>${r.passed?'✓ Practical passed':'↻ Evidence needs improvement'} · ${r.score}%</h2>${rubricMarkup(r.rubric)}<p><b>Missing hidden checks:</b> ${escapeHtml((r.missing_checks||[]).join(', ')||'None')}</p>`;toast('Practical examination evaluated');await loadProgress()}catch(e){toast(e.message,true)}}

async function loadWorkspace(){if(!state.currentStudent)return;try{const d=await api(`/api/v3/workspace?student_id=${state.currentStudent.id}`);state.workspaceFiles=d.files;$('#workspaceSize').textContent=bytesLabel(d.total_bytes);$('#workspaceFileList').innerHTML=d.files.length?d.files.map(x=>`<button class="workspace-file" data-workspace-path="${escapeHtml(x.path)}">${x.text_editable?'⌘':'▧'} ${escapeHtml(x.path)}</button>`).join(''):'<div class="empty-state compact"><p>No project files yet.</p></div>';$$('[data-workspace-path]').forEach(b=>b.onclick=()=>openWorkspaceFile(b.dataset.workspacePath,b));}catch(e){toast(e.message,true)}}
async function openWorkspaceFile(path,b){$$('[data-workspace-path]').forEach(x=>x.classList.toggle('active',x===b));state.workspacePath=path;$('#workspacePath').value=path;$('#downloadWorkspaceFile').href=`/api/v3/workspace/file?student_id=${state.currentStudent.id}&path=${encodeURIComponent(path)}`;try{const r=await fetch($('#downloadWorkspaceFile').href);const blob=await r.blob();if(blob.size>2*1024*1024){$('#workspaceEditor').value='Binary or large file selected. Use Download selected to open it.';return}$('#workspaceEditor').value=await blob.text();$('#workspaceStatus').textContent=`Opened ${path}`}catch(e){toast(e.message,true)}}
async function saveWorkspaceFile(){if(!state.currentStudent)return;const path=$('#workspacePath').value.trim();if(!path){toast('Enter a workspace path.',true);return}try{const r=await api('/api/v3/workspace/save',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,path,tool:$('#workspaceTool').value,content:$('#workspaceEditor').value})});state.workspacePath=r.path;$('#downloadWorkspaceFile').href=`/api/v3/workspace/file?student_id=${state.currentStudent.id}&path=${encodeURIComponent(r.path)}`;$('#workspaceStatus').textContent=`Saved ${r.path} · ${bytesLabel(r.size_bytes)}`;toast('Project file saved');await loadWorkspace()}catch(e){toast(e.message,true)}}
function newWorkspaceFile(){$('#workspacePath').value='projects/new-task.md';$('#workspaceEditor').value='# Company task\n\n## Ticket\n\n## Diagnosis\n\n## Implementation\n\n## Validation evidence\n\n## Security\n\n## Rollback\n';$('#workspaceEditor').focus()}
async function uploadWorkspace(){const file=$('#workspaceUpload').files[0];if(!file)return;try{const content=await fileBase64(file,8);const path=`evidence/${file.name}`;await api('/api/v3/workspace/upload',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,path,tool:$('#workspaceTool').value,content_base64:content})});toast('Evidence uploaded');await loadWorkspace()}catch(e){toast(e.message,true)}finally{$('#workspaceUpload').value=''}}

async function loadCertificates(){if(!state.currentStudent)return;try{const d=await api(`/api/v3/certificates?student_id=${state.currentStudent.id}`);$('#certificateList').innerHTML=d.certificates.length?d.certificates.map(x=>`<div class="certificate-card"><div><b>${escapeHtml(x.subject)}</b><small>${escapeHtml(x.certificate_type)} · ${x.score}% · ${escapeHtml(x.verification_code)}</small></div><a class="button secondary" href="/api/v3/certificate/file?id=${encodeURIComponent(x.id)}">Download</a></div>`).join(''):'<div class="empty-state"><h2>No certificates issued</h2><p>Complete assessed work, then ask the administrator to verify and issue a certificate.</p></div>'}catch(e){toast(e.message,true)}}
async function issueCertificate(){if(!adminToken()){toast('Administrator unlock is required to issue certificates.',true);openAdminDialog();return}try{await adminApi('/api/v3/certificate/issue',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,certificate_type:$('#certificateType').value,subject:$('#certificateSubject').value,score:Number($('#certificateScore').value)})});toast('Certificate generated');await loadCertificates()}catch(e){toast(e.message,true)}}
async function verifyCertificate(){try{const d=await api(`/api/v3/certificate/verify?code=${encodeURIComponent($('#verifyCertificateCode').value)}`);$('#verifyCertificateResult').innerHTML=d.valid?`<div class="result-card pass"><b>✓ Valid certificate</b><p>${escapeHtml(d.certificate.student_name)} · ${escapeHtml(d.certificate.subject)} · ${d.certificate.score}%</p></div>`:'<div class="result-card fail"><b>Certificate not found</b></div>'}catch(e){toast(e.message,true)}}

function openAdminDialog(){loadV23Status().then(()=>{$('#adminPinInput').value='';$('#adminAuthError').textContent='';$('#adminDialog').showModal()})}
async function openAdminPage(){if(adminToken()){await loadAdminOverview()}else{$('#adminLocked').classList.remove('hidden');$('#adminDashboard').classList.add('hidden');$('#adminSessionState').textContent='Locked'}}
async function submitAdminAuth(e){e.preventDefault();try{const setup=!state.v23Status?.admin?.configured;const path=setup?'/api/v3/admin/setup':'/api/v3/admin/auth';const payload={pin:$('#adminPinInput').value,admin_name:$('#adminNameInput').value,institute_name:$('#instituteNameInput').value};const d=await api(path,{method:'POST',body:JSON.stringify(payload)});storageSet('billingerAdminToken',d.token);$('#adminDialog').close();state.v23Status={...(state.v23Status||{}),admin:{configured:true,admin_name:d.admin_name,institute_name:d.institute_name}};toast('Administrator control unlocked');if(state.pendingAiAdmin){state.pendingAiAdmin=false;showPage('system');await loadAiControl()}else{showPage('admin');await loadAdminOverview()}}catch(err){$('#adminAuthError').textContent=err.message}}
async function loadAdminOverview(){try{const d=await adminApi('/api/v3/admin/overview');state.adminOverview=d;$('#adminLocked').classList.add('hidden');$('#adminDashboard').classList.remove('hidden');$('#adminSessionState').textContent='Unlocked';$('#adminReportLink').href='/api/v3/admin/report.csv';$('#adminReportLink').onclick=async e=>{e.preventDefault();const r=await fetch('/api/v3/admin/report.csv',{headers:{'X-Admin-Token':adminToken()}});if(!r.ok){toast('Unable to export report',true);return}const blob=await r.blob();const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='Billinger_Student_Report.csv';a.click();URL.revokeObjectURL(a.href)};renderAdminOverview(d);await loadAdminMaintenance()}catch(e){storageSet('billingerAdminToken','');$('#adminLocked').classList.remove('hidden');$('#adminDashboard').classList.add('hidden');$('#adminSessionState').textContent='Locked';toast(e.message,true)}}
function renderAdminOverview(d){const labels={active_students:'Active students',batches:'Batches',active_assignments:'Assignments',published_imports:'Published imports'};$('#adminStats').innerHTML=Object.entries(d.summary).map(([k,v])=>`<article class="panel admin-stat vfx-tilt"><small>${labels[k]||k}</small><strong>${v}</strong></article>`).join('');$('#adminStudentTable').innerHTML=`<div class="admin-row header"><span>Student</span><span>Lessons</span><span>Labs</span><span>Average</span><span>Tests</span><span>Practical</span><span>Status</span></div>`+d.students.map(s=>`<div class="admin-row"><strong>${escapeHtml(s.name)}<small>${escapeHtml(s.email||'No email')}</small></strong><span>${s.progress.lessons}</span><span>${s.progress.labs}</span><span>${s.progress.average_score}%</span><span>${s.progress.tests}</span><span>${s.progress.practical_exams}</span><button class="button ghost admin-student-toggle" data-student-id="${s.id}" data-active="${s.active?1:0}">${s.active?'Active':'Inactive'}</button></div>`).join('');$$('.admin-student-toggle').forEach(b=>b.onclick=async()=>{try{const s=d.students.find(x=>x.id===Number(b.dataset.studentId));await adminApi('/api/v3/admin/student/update',{method:'POST',body:JSON.stringify({student_id:s.id,name:s.name,email:s.email,active:!s.active,target_role:'DevOps Engineer',study_minutes:90})});await loadAdminOverview()}catch(e){toast(e.message,true)}});const batchOptions=d.batches.map(b=>`<option value="${b.id}">${escapeHtml(b.name)}</option>`).join('');$('#assignmentBatch').innerHTML=batchOptions;$('#announcementBatch').innerHTML=batchOptions;if(!$('#batchRole').options.length)d.role_tracks.forEach(x=>$('#batchRole').add(new Option(x,x)));$('#batchList').innerHTML=d.batches.length?d.batches.map(b=>`<div class="batch-card"><b>${escapeHtml(b.name)}</b><small>${escapeHtml(b.level)} · ${escapeHtml(b.target_role)} · ${b.member_count} students${b.deadline?` · Deadline ${b.deadline}`:''}</small><div class="batch-member-control"><select data-batch-student="${b.id}">${d.students.map(s=>`<option value="${s.id}">${escapeHtml(s.name)}${b.member_ids.includes(s.id)?' ✓':''}</option>`).join('')}</select><button class="button ghost batch-add-member" data-batch-id="${b.id}">Assign</button><button class="button ghost batch-remove-member" data-batch-id="${b.id}">Remove</button></div></div>`).join(''):'<p class="muted">No batches created.</p>';$$('.batch-add-member').forEach(btn=>btn.onclick=()=>changeBatchMember(btn.dataset.batchId,true));$$('.batch-remove-member').forEach(btn=>btn.onclick=()=>changeBatchMember(btn.dataset.batchId,false));$('#adminAssignmentList').innerHTML=`<h2>Recent assignments</h2>`+(d.assignments.length?d.assignments.map(a=>`<div class="assignment-card"><b>${escapeHtml(a.title)}</b><small>Batch ${a.batch_id} · ${escapeHtml(a.item_type)}${a.due_date?` · Due ${a.due_date}`:''}</small><p>${escapeHtml(a.instructions)}</p></div>`).join(''):'<p class="muted">No assignments created.</p>');initVfxTilt()}
async function changeBatchMember(batchId,assigned){const select=$(`[data-batch-student="${batchId}"]`);if(!select)return;try{await adminApi('/api/v3/admin/batch/member',{method:'POST',body:JSON.stringify({batch_id:Number(batchId),student_id:Number(select.value),assigned})});toast(assigned?'Student assigned to batch':'Student removed from batch');await loadAdminOverview()}catch(e){toast(e.message,true)}}
async function saveBatchForm(e){e.preventDefault();const f=new FormData(e.target);try{await adminApi('/api/v3/admin/batch/save',{method:'POST',body:JSON.stringify(Object.fromEntries(f.entries()))});e.target.reset();toast('Batch saved');await loadAdminOverview()}catch(err){toast(err.message,true)}}
async function createAssignmentForm(e){e.preventDefault();const f=new FormData(e.target);try{await adminApi('/api/v3/admin/assignment/create',{method:'POST',body:JSON.stringify(Object.fromEntries(f.entries()))});e.target.reset();toast('Assignment created');await loadAdminOverview()}catch(err){toast(err.message,true)}}
async function createAnnouncementForm(e){e.preventDefault();const f=new FormData(e.target);try{await adminApi('/api/v3/admin/announcement/create',{method:'POST',body:JSON.stringify(Object.fromEntries(f.entries()))});e.target.reset();toast('Announcement posted');await loadAdminOverview()}catch(err){toast(err.message,true)}}
function switchAdminTab(tab){$$('.admin-tab').forEach(b=>b.classList.toggle('active',b.dataset.adminTab===tab));$$('.admin-tab-pane').forEach(p=>p.classList.toggle('active',p.id===`admin-tab-${tab}`));if(tab==='imports')loadContentVersions();if(tab==='maintenance')loadAdminMaintenance()}
async function stageContentImport(){const file=$('#contentImportFile').files[0];if(!file)return toast('Choose a learning ZIP first.',true);$('#stageContentImport').disabled=true;$('#stageContentImport').textContent='Inspecting ZIP…';try{const content=await fileBase64(file,75);const d=await adminApi('/api/v3/admin/import/stage',{method:'POST',body:JSON.stringify({filename:file.name,content_base64:content})});state.stagedImport=d;renderContentImport(d);toast(`${d.documents.length} documents staged for approval`)}catch(e){toast(e.message,true)}finally{$('#stageContentImport').disabled=false;$('#stageContentImport').textContent='Inspect and stage ZIP'}}
function renderContentImport(d){const box=$('#contentImportEditor');box.classList.remove('hidden');box.innerHTML=`<div class="panel-heading"><div><span class="eyebrow">ADMINISTRATOR APPROVAL REQUIRED</span><h2>${escapeHtml(d.zip_name)}</h2><p>${escapeHtml(d.notice)}</p></div><button id="publishContentImport" class="button primary">Publish approved documents</button></div><div class="import-doc-card header"><b>Document</b><b>Primary tool</b><b>Level</b><b>Publish</b></div>`+d.documents.map((x,i)=>`<div class="import-doc-card" data-import-key="${escapeHtml(x.key)}"><div><b>${escapeHtml(x.title)}</b><small>${Object.keys(x.files).map(k=>k.toUpperCase()).join(' + ')} · ${x.word_count.toLocaleString()} words · <span class="confidence">${x.confidence}% recommendation confidence</span></small></div><select class="import-tool">${d.tool_options.map(t=>`<option value="${t.slug}" ${t.slug===x.recommended_tool?'selected':''}>${escapeHtml(t.name)}</option>`).join('')}</select><select class="import-level">${d.levels.map(l=>`<option ${l===x.recommended_level?'selected':''}>${l}</option>`).join('')}</select><input class="import-publish" type="checkbox" checked title="Publish"></div>`).join('');$('#publishContentImport').onclick=publishContentImport}
async function publishContentImport(){const mappings=$$('.import-doc-card[data-import-key]').map(row=>({key:row.dataset.importKey,tool:$('.import-tool',row).value,level:$('.import-level',row).value,publish:$('.import-publish',row).checked,title:$('b',row).textContent,version:'1.0',rationale:'Administrator reviewed the title, contents and recommendation before publishing.'}));try{const d=await adminApi('/api/v3/admin/import/publish',{method:'POST',body:JSON.stringify({import_id:state.stagedImport.import_id,mappings})});toast(`${d.published} verified documents published`);$('#contentImportEditor').classList.add('hidden');state.stagedImport=null;state.coverage=null;await loadCatalog();await loadContentVersions();await loadAdminOverview()}catch(e){toast(e.message,true)}}
async function loadContentVersions(){if(!adminToken())return;try{const d=await adminApi('/api/v3/admin/content/versions');$('#contentVersionList').innerHTML=d.versions.length?d.versions.map(x=>`<div class="version-item"><div><b>${escapeHtml(x.title)}</b><small>${escapeHtml(x.primary_tool)} · ${escapeHtml(x.level)} · v${escapeHtml(x.version)}</small></div><span class="pill">${escapeHtml(x.status)}</span></div>`).join(''):'<p class="muted">No administrator-imported content versions yet.</p>'}catch(e){toast(e.message,true)}}
async function loadAdminMaintenance(){if(!adminToken())return;try{const d=await adminApi('/api/v3/admin/backups');$('#backupList').innerHTML=d.backups.length?d.backups.map(x=>`<div class="backup-item"><div><b>${escapeHtml(x.file_name)}</b><small>${bytesLabel(x.size_bytes)} · ${new Date(x.created_at).toLocaleString()}</small></div><a class="button ghost admin-backup-download" data-backup-id="${x.id}" href="#">Download</a></div>`).join(''):'<p class="muted">No full backups yet.</p>';$$('.admin-backup-download').forEach(a=>a.onclick=async e=>{e.preventDefault();const r=await fetch(`/api/v3/backup/file?id=${encodeURIComponent(a.dataset.backupId)}`,{headers:{'X-Admin-Token':adminToken()}});if(!r.ok)return toast('Backup download failed',true);const blob=await r.blob();const u=URL.createObjectURL(blob);const x=document.createElement('a');x.href=u;x.download='Billinger_Backup.zip';x.click();URL.revokeObjectURL(u)});$('#updateList').innerHTML=d.updates.length?d.updates.map(x=>`<div class="update-item"><div><b>${escapeHtml(x.file_name)}</b><small>Detected ${escapeHtml(x.detected_version)} · ${escapeHtml(x.status)}</small></div><code>${escapeHtml(x.sha256.slice(0,12))}…</code></div>`).join(''):'<p class="muted">No staged updates.</p>'}catch(e){toast(e.message,true)}}
async function createFullBackup(){try{const d=await adminApi('/api/v3/admin/backup/create',{method:'POST',body:'{}'});toast(`Backup created: ${d.file_name}`);await loadAdminMaintenance()}catch(e){toast(e.message,true)}}
async function stageRestore(){const file=$('#restoreBackupFile').files[0];if(!file)return toast('Choose a backup ZIP.',true);try{const content=await fileBase64(file,2048);const d=await adminApi('/api/v3/admin/restore/stage',{method:'POST',body:JSON.stringify({filename:file.name,content_base64:content})});toast(d.message)}catch(e){toast(e.message,true)}}
async function stageOfflineUpdate(){const file=$('#offlineUpdateFile').files[0];if(!file)return toast('Choose an update ZIP.',true);try{const content=await fileBase64(file,500);const d=await adminApi('/api/v3/admin/update/stage',{method:'POST',body:JSON.stringify({filename:file.name,content_base64:content})});toast(`Update ${d.detected_version} staged`);await loadAdminMaintenance()}catch(e){toast(e.message,true)}}

function initVfxTilt(){if(window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;$$('.vfx-tilt').forEach(card=>{if(card.dataset.tiltBound)return;card.dataset.tiltBound='1';card.addEventListener('mousemove',e=>{const r=card.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;card.style.transform=`perspective(900px) rotateX(${-y*3}deg) rotateY(${x*4}deg) translateZ(2px)`});card.addEventListener('mouseleave',()=>card.style.transform='')})}

function bindV3Events(){
  $('#adminPortalButton')?.addEventListener('click',()=>showPage('admin'));$('#adminUnlockButton')?.addEventListener('click',openAdminDialog);$('#adminUnlockCenter')?.addEventListener('click',openAdminDialog);$('#adminAuthForm')?.addEventListener('submit',submitAdminAuth);
  $('#saveMyProfile')?.addEventListener('click',saveMyProfile);$('#regeneratePlan')?.addEventListener('click',regeneratePlan);
  $('#practicalTool')?.addEventListener('change',loadPracticalTemplates);$('#practicalLevel')?.addEventListener('change',loadPracticalTemplates);$('#startPractical')?.addEventListener('click',startPractical);$('#submitPractical')?.addEventListener('click',submitPractical);
  $('#refreshWorkspace')?.addEventListener('click',loadWorkspace);$('#saveWorkspaceFile')?.addEventListener('click',saveWorkspaceFile);$('#newWorkspaceFile')?.addEventListener('click',newWorkspaceFile);$('#workspaceUpload')?.addEventListener('change',uploadWorkspace);
  $('#issueCertificate')?.addEventListener('click',issueCertificate);$('#verifyCertificate')?.addEventListener('click',verifyCertificate);
  $$('.admin-tab').forEach(b=>b.addEventListener('click',()=>switchAdminTab(b.dataset.adminTab)));$('#batchForm')?.addEventListener('submit',saveBatchForm);$('#assignmentForm')?.addEventListener('submit',createAssignmentForm);$('#announcementForm')?.addEventListener('submit',createAnnouncementForm);$('#stageContentImport')?.addEventListener('click',stageContentImport);$('#createFullBackup')?.addEventListener('click',createFullBackup);$('#stageRestore')?.addEventListener('click',stageRestore);$('#stageOfflineUpdate')?.addEventListener('click',stageOfflineUpdate);
}

// ---------------- Billinger v2.4: Career & Portfolio Command Centre ----------------
function splitCsv(value=''){return String(value).split(/[,;\n]+/).map(x=>x.trim()).filter(Boolean)}
function parsePipeRecords(value, fields){return String(value||'').split(/\n+/).map(x=>x.trim()).filter(Boolean).map(line=>{const parts=line.split('|').map(x=>x.trim());const out={};fields.forEach((f,i)=>out[f]=parts[i]||'');return out})}
function recordsToLines(records,fields){return (records||[]).map(x=>fields.map(f=>x[f]||'').join(' | ')).join('\n')}
function careerApi(path,options={}){if(!state.currentStudent)throw new Error('Select a student first.');return api(path,options)}
function switchCareerTab(tab){$$('.career-tab').forEach(b=>b.classList.toggle('active',b.dataset.careerTab===tab));$$('.career-tab-pane').forEach(p=>p.classList.toggle('active',p.id===`career-tab-${tab}`))}
function secureUrl(path){const join=path.includes('?')?'&':'?';return `${path}${join}student_id=${encodeURIComponent(state.currentStudent.id)}`}
async function secureDownload(path,filename='',open=false){try{const r=await fetch(secureUrl(path),{headers:{'X-Student-Token':state.studentToken}});if(!r.ok){let msg='Download failed';try{msg=(await r.json()).error||msg}catch(_){}throw new Error(msg)}const blob=await r.blob(),url=URL.createObjectURL(blob);if(open){window.open(url,'_blank','noopener')}else{const a=document.createElement('a');a.href=url;a.download=filename||'Billinger_Document';a.click();setTimeout(()=>URL.revokeObjectURL(url),5000)}}catch(e){toast(e.message,true)}}

async function loadCareer(){
  if(!state.currentStudent||!state.studentToken)return;
  try{const d=await careerApi(`/api/v4/career/dashboard?student_id=${state.currentStudent.id}`);state.career=d;renderCareer(d)}catch(e){toast(e.message,true)}
}
function renderCareer(d){
  $('#careerJobCount').textContent=d.summary.jobs;$('#careerRecommendedCount').textContent=d.summary.recommended;$('#careerApplicationCount').textContent=d.summary.applications;$('#careerGmailStatus').textContent=d.gmail.connected?'Connected':d.gmail.client_configured?'Client ready':'Not connected';
  const p=d.profile||{};$('#candidateName').value=p.full_name||'';$('#candidateEmail').value=p.email||'';$('#candidatePhone').value=p.phone||'';$('#candidateLocation').value=p.location||'';$('#candidateHeadline').value=p.headline||'';$('#candidateSummary').value=p.summary||'';$('#candidateSkills').value=(p.skills||[]).join(', ');$('#candidateExperience').value=recordsToLines(p.experience,['role','company','years','details']);$('#candidateEducation').value=recordsToLines(p.education,['qualification','institution','year']);$('#candidateCertifications').value=(p.certifications||[]).map(x=>x.name||'').filter(Boolean).join('\n');$('#candidateRoles').value=(p.preferences?.target_roles||[]).join(', ');$('#candidateLocations').value=(p.preferences?.locations||[]).join(', ');$('#candidateMinMatch').value=p.preferences?.minimum_match||75;$('#candidateGithub').value=p.links?.github||'';$('#candidateLinkedin').value=p.links?.linkedin||'';$('#candidatePortfolioUrl').value=p.links?.portfolio||'';$('#candidateResumeText').value=p.master_resume_text||'';$('#candidateVerified').checked=!!p.verified;
  $('#jobSourceList').innerHTML=d.sources.length?d.sources.map(x=>`<div class="career-item"><div class="career-item-head"><div><b>${escapeHtml(x.name)}</b><small>${escapeHtml(x.source_type)} · ${escapeHtml(x.identifier)}</small></div><span class="pill">${x.active?'Active':'Paused'}</span></div><small>${x.last_scan_at?`Last scan ${new Date(x.last_scan_at).toLocaleString()} · ${escapeHtml(x.last_result||'')}`:'Not scanned yet'}</small></div>`).join(''):'<p class="muted">No approved job sources configured.</p>';
  renderCareerJobs(d.jobs);renderPortfolioData(d);renderCareerDocuments(d);renderApplications(d);
}
function renderCareerJobs(jobs){
  const query=($('#careerJobSearch')?.value||'').toLowerCase();const filtered=(jobs||[]).filter(j=>`${j.company} ${j.title} ${j.location} ${(j.match?.matched||[]).join(' ')}`.toLowerCase().includes(query));
  $('#careerJobList').innerHTML=filtered.length?filtered.map(j=>`<article class="career-job-card" data-job-card="${j.id}"><div class="career-job-score"><span class="pill">${escapeHtml(j.status.replaceAll('_',' '))}</span><strong>${Math.round(j.match_score)}%</strong></div><h3>${escapeHtml(j.title)}</h3><p><b>${escapeHtml(j.company)}</b> · ${escapeHtml(j.location||'Location not listed')}</p><small>${escapeHtml(j.match?.recommendation||'')} · Matched: ${escapeHtml((j.match?.matched||[]).slice(0,8).join(', ')||'none')}</small><div class="match-bars">${Object.values(j.match?.components||{}).map(v=>`<i style="--v:${v}%"></i>`).join('')}</div><div class="actions"><button class="button primary job-prepare" data-job="${j.id}">Prepare application</button><button class="button secondary job-research" data-job="${j.id}">Interview research</button>${j.url?`<a class="button ghost" href="${escapeHtml(j.url)}" target="_blank" rel="noopener">Official page</a>`:''}</div><details><summary>Match details</summary><p><b>Missing/unverified:</b> ${escapeHtml((j.match?.missing||[]).slice(0,15).join(', ')||'none')}</p><p>${escapeHtml(j.match?.truth_notice||'')}</p></details></article>`).join(''):'<div class="empty-state"><h2>No matching jobs</h2><p>Add a permitted source or paste a job description.</p></div>';
  $$('.job-prepare').forEach(b=>b.onclick=()=>selectCareerJob(b.dataset.job,'apply'));$$('.job-research').forEach(b=>b.onclick=()=>selectCareerJob(b.dataset.job,'track'));
  fillJobSelects(jobs||[]);
}
function fillJobSelects(jobs){const options='<option value="">Select a job</option>'+jobs.map(j=>`<option value="${j.id}">${escapeHtml(j.company)} — ${escapeHtml(j.title)} (${Math.round(j.match_score)}%)</option>`).join('');['careerApplyJob','careerInterviewJob'].forEach(id=>{const el=$('#'+id);if(el){const old=el.value;el.innerHTML=options;if(jobs.some(j=>j.id===old))el.value=old}});const pj=$('#portfolioJobSelect');if(pj){const old=pj.value;pj.innerHTML='<option value="">General DevOps portfolio</option>'+jobs.map(j=>`<option value="${j.id}">${escapeHtml(j.company)} — ${escapeHtml(j.title)}</option>`).join('');if(jobs.some(j=>j.id===old))pj.value=old}}
function selectCareerJob(id,tab){state.selectedCareerJob=state.career.jobs.find(x=>x.id===id);if(!state.selectedCareerJob)return;$('#careerApplyJob').value=id;$('#careerInterviewJob').value=id;const p=state.career.profile;$('#careerEmailTo').value='';$('#careerEmailSubject').value=`Application for ${state.selectedCareerJob.title} — ${p.full_name||state.currentStudent.name}`;$('#careerEmailBody').value=`Dear Hiring Manager,\n\nI am applying for the ${state.selectedCareerJob.title} position at ${state.selectedCareerJob.company}. My verified DevOps skills and selected portfolio evidence align with several requirements in the role.\n\nPlease find my tailored resume attached. I would welcome the opportunity to discuss how my practical Linux, automation, CI/CD, container, cloud and reliability work can support your team.\n\nRegards,\n${p.full_name||state.currentStudent.name}`;switchCareerTab(tab);showPage('career')}
function renderCareerDocuments(d){
  const portfolioOptions='<option value="">No portfolio attachment</option>'+d.portfolio_builds.map(x=>`<option value="${x.id}">${escapeHtml(x.title)} · ${new Date(x.created_at).toLocaleDateString()}</option>`).join('');['careerApplyPortfolio','careerEmailPortfolio'].forEach(id=>{if($('#'+id))$('#'+id).innerHTML=portfolioOptions});
  const resumeOptions='<option value="">Select a tailored resume</option>'+d.resume_variants.map(x=>`<option value="${x.id}">${escapeHtml(x.title)} · ${Math.round(x.match_score)}%</option>`).join('');$('#careerEmailResume').innerHTML=resumeOptions;
  $('#careerResumeList').innerHTML=d.resume_variants.length?d.resume_variants.map(x=>`<div class="career-item"><b>${escapeHtml(x.title)}</b><small>Match ${Math.round(x.match_score)}% · ${new Date(x.created_at).toLocaleString()}</small><div class="actions"><button class="button ghost secure-file" data-url="${x.links.pdf}" data-name="Resume.pdf">PDF</button><button class="button ghost secure-file" data-url="${x.links.docx}" data-name="Resume.docx">DOCX</button></div></div>`).join(''):'<p class="muted">No tailored resume generated.</p>';
  $$('.secure-file').forEach(b=>b.onclick=()=>secureDownload(b.dataset.url,b.dataset.name));
  const latestDraft=d.email_drafts[0];if(latestDraft&&latestDraft.status==='draft')renderEmailPreview(latestDraft);
}
async function saveCandidateProfile(e){e.preventDefault();try{const data={student_id:state.currentStudent.id,full_name:$('#candidateName').value,email:$('#candidateEmail').value,phone:$('#candidatePhone').value,location:$('#candidateLocation').value,headline:$('#candidateHeadline').value,summary:$('#candidateSummary').value,skills:splitCsv($('#candidateSkills').value),experience:parsePipeRecords($('#candidateExperience').value,['role','company','years','details']),education:parsePipeRecords($('#candidateEducation').value,['qualification','institution','year']),certifications:splitCsv($('#candidateCertifications').value).map(name=>({name})),preferences:{target_roles:splitCsv($('#candidateRoles').value),locations:splitCsv($('#candidateLocations').value),minimum_match:Number($('#candidateMinMatch').value||75)},links:{github:$('#candidateGithub').value,linkedin:$('#candidateLinkedin').value,portfolio:$('#candidatePortfolioUrl').value},master_resume_text:$('#candidateResumeText').value,verified:$('#candidateVerified').checked};await careerApi('/api/v4/profile/save',{method:'POST',body:JSON.stringify(data)});toast('Verified candidate profile saved');await loadCareer()}catch(err){toast(err.message,true)}}
async function addJobSource(e){e.preventDefault();try{await careerApi('/api/v4/source/add',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,source_type:$('#jobSourceType').value,name:$('#jobSourceName').value,identifier:$('#jobSourceIdentifier').value})});e.target.reset();toast('Approved job source added');await loadCareer()}catch(err){toast(err.message,true)}}
async function scanJobSources(){try{$('#scanJobSources').disabled=true;$('#scanJobSources').textContent='Scanning approved sources…';const d=await careerApi('/api/v4/source/scan',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id})});toast(`Imported ${d.imported} jobs; ${d.errors.length} source warnings`);await loadCareer()}catch(e){toast(e.message,true)}finally{$('#scanJobSources').disabled=false;$('#scanJobSources').textContent='Scan all sources'}}
async function analyzeManualJob(e){e.preventDefault();try{const d=await careerApi('/api/v4/job/analyze',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,company:$('#manualJobCompany').value,title:$('#manualJobTitle').value,location:$('#manualJobLocation').value,url:$('#manualJobUrl').value,description:$('#manualJobDescription').value})});toast(`Job analyzed: ${Math.round(d.match_score)}% match`);e.target.reset();await loadCareer();selectCareerJob(d.id,'apply')}catch(err){toast(err.message,true)}}
async function generateCareerResume(){const jobId=$('#careerApplyJob').value;if(!jobId)return toast('Select a job first.',true);try{const r=await careerApi('/api/v4/resume/generate',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,job_id:jobId,portfolio_build_id:$('#careerApplyPortfolio').value})});state.selectedCareerResume=r;$('#careerResumeResult').className='career-result';$('#careerResumeResult').innerHTML=`<h3>Tailored resume ready · ${Math.round(r.match_score)}%</h3><p><b>Included:</b> ${escapeHtml(r.included_keywords.join(', ')||'verified profile content')}</p><p><b>Not claimed:</b> ${escapeHtml(r.missing_keywords.join(', ')||'none')}</p><div class="actions"><button id="downloadNewResumePdf" class="button primary">Download PDF</button><button id="downloadNewResumeDocx" class="button secondary">Download DOCX</button></div>`;$('#downloadNewResumePdf').onclick=()=>secureDownload(r.links.pdf,'Tailored_Resume.pdf');$('#downloadNewResumeDocx').onclick=()=>secureDownload(r.links.docx,'Tailored_Resume.docx');toast('Truthful job-specific resume generated');await loadCareer();$('#careerEmailResume').value=r.id}catch(e){toast(e.message,true)}}
async function createCareerEmail(e){e.preventDefault();const jobId=$('#careerApplyJob').value||state.selectedCareerJob?.id;if(!jobId)return toast('Select a job first.',true);try{const d=await careerApi('/api/v4/email/draft',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,job_id:jobId,resume_variant_id:$('#careerEmailResume').value,portfolio_build_id:$('#careerEmailPortfolio').value,recipient:$('#careerEmailTo').value,subject:$('#careerEmailSubject').value,body:$('#careerEmailBody').value})});state.selectedEmailDraft=d;renderEmailPreview(d);toast('Application email preview created — not sent')}catch(err){toast(err.message,true)}}
function renderEmailPreview(d){const box=$('#careerEmailPreview');if(!box)return;box.className='mail-preview';box.innerHTML=`<span class="pill">${escapeHtml(d.status)}</span><h3>${escapeHtml(d.subject)}</h3><p><b>To:</b> ${escapeHtml(d.recipient)}</p><pre>${escapeHtml(d.body)}</pre><p><b>Attachments:</b> ${escapeHtml((d.attachments||[]).map(x=>x.split('/').pop()).join(', ')||'none')}</p><div class="actions"><button id="downloadEmlDraft" class="button secondary">Download .EML</button><button id="sendGmailDraft" class="button primary">Approve and send through Gmail</button></div><p class="muted">Sending requires typing the exact confirmation word SEND. The bot never sends silently.</p>`;$('#downloadEmlDraft').onclick=()=>secureDownload(d.download,'Application_Email.eml');$('#sendGmailDraft').onclick=()=>sendGmailDraft(d.id)}
async function saveGmailClient(){const f=$('#gmailClientFile').files[0];if(!f)return toast('Choose the Google OAuth client JSON.',true);try{const content=await fileBase64(f,1);await careerApi('/api/v4/gmail/client',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,filename:f.name,content_base64:content})});toast('Gmail OAuth client saved securely');await loadCareer()}catch(e){toast(e.message,true)}}
async function connectGmail(){try{const redirect=`${location.origin}/oauth/gmail/callback`;const d=await careerApi('/api/v4/gmail/auth/start',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,redirect_uri:redirect})});window.open(d.authorization_url,'BillingerGmailOAuth','width=720,height=780');toast('Complete Gmail authorization, then refresh Career Command')}catch(e){toast(e.message,true)}}
async function sendGmailDraft(id){const confirmation=window.prompt('Type SEND to approve this exact recipient, subject and attachments.');if(confirmation!=='SEND')return toast('Email was not sent.');try{const d=await careerApi('/api/v4/email/send',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,draft_id:id,confirmation})});toast(`Application sent through Gmail · ${d.gmail_message_id}`);await loadCareer()}catch(e){toast(e.message,true)}}
function renderApplications(d){$('#careerApplicationList').innerHTML=d.applications.length?d.applications.map(x=>`<div class="career-item"><div class="career-item-head"><div><b>${escapeHtml(x.company)} — ${escapeHtml(x.title)}</b><small>${escapeHtml(x.status.replaceAll('_',' '))} · Match ${Math.round(x.match_score)}%</small></div><span class="pill">${x.follow_up_date?`Follow up ${x.follow_up_date}`:''}</span></div><p>${escapeHtml(x.notes||'')}</p></div>`).join(''):'<p class="muted">No applications tracked yet.</p>'}
async function prepareCareerInterview(){
  const id=$('#careerInterviewJob').value;if(!id)return toast('Select a job.',true);
  const box=$('#careerResearchResult');box.className='career-result';box.innerHTML='<p>Researching the role and routing a company-specific question pack…</p>';
  try{
    const d=await careerApi('/api/v4/research',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,job_id:id,company_url:$('#careerCompanyUrl').value})});
    let aiPack=null,aiError='';
    try{
      aiPack=await api('/api/v6/ai/questions/generate',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,mode:'company',tool:d.recruitment_payload.track||'DevOps',difficulty:d.recruitment_payload.difficulty||'professional',count:9,context:{company:d.company||'',target_role:d.recruitment_payload.target_role,job_description:d.recruitment_payload.job_description,resume_text:d.recruitment_payload.resume_text,evidence_basis:d.evidence_basis,likely_rounds:d.likely_rounds}})});
    }catch(e){aiError=e.message}
    const aiMarkup=aiPack?`<div class="ai-analysis-box"><div class="ai-result-head"><span class="pill">Online AI pack</span><b>${escapeHtml(aiPack.provider)} · ${escapeHtml(aiPack.model)}</b></div><ol>${aiPack.questions.map(q=>`<li>${escapeHtml(q.prompt)}</li>`).join('')}</ol><p class="muted">Question set ${escapeHtml(aiPack.session_id)} is retained for this learner.</p></div>`:`<p class="muted">Online AI enrichment unavailable: ${escapeHtml(aiError)}. The verified local interview pack remains available.</p>`;
    box.innerHTML=`<h3>Company and role interview pack ready</h3><p>${escapeHtml(d.warning)}</p><p><b>Evidence basis:</b> ${escapeHtml(d.evidence_basis.join(', '))}</p><p><b>Likely rounds:</b> ${escapeHtml(d.likely_rounds.join(' → '))}</p><details><summary>${d.questions.length} verified local questions</summary><ol>${d.questions.map(q=>`<li>${escapeHtml(q)}</li>`).join('')}</ol></details>${aiMarkup}<button id="launchPreparedRecruitment" class="button primary">Open full mock recruitment</button>`;
    $('#launchPreparedRecruitment').onclick=()=>{$('#recruitmentRole').value=d.recruitment_payload.target_role;$('#recruitmentTrack').value=d.recruitment_payload.track;$('#recruitmentDifficulty').value=d.recruitment_payload.difficulty;$('#recruitmentResume').value=d.recruitment_payload.resume_text;$('#recruitmentJob').value=d.recruitment_payload.job_description;showPage('recruitment')};
    toast('Company and job-specific interview pack prepared');
  }catch(e){box.innerHTML=`<p class="provider-error">${escapeHtml(e.message)}</p>`;toast(e.message,true)}
}

async function loadPortfolio(){if(!state.currentStudent||!state.studentToken)return;try{const d=state.career||await careerApi(`/api/v4/career/dashboard?student_id=${state.currentStudent.id}`);state.career=d;renderPortfolioData(d)}catch(e){toast(e.message,true)}}
function renderPortfolioData(d){
  if(!$('#portfolioProjectList'))return;const projects=d.projects||[],builds=d.portfolio_builds||[];$('#portfolioReadyCount').textContent=projects.filter(x=>['approved','portfolio_ready'].includes(x.status)).length;$('#portfolioBuildCount').textContent=builds.length;$('#portfolioBlockedCount').textContent=projects.filter(x=>x.report?.secret_findings?.length).length;
  $('#portfolioProjectList').innerHTML=projects.length?projects.map(p=>`<div class="portfolio-project-card"><div class="career-item-head"><div><b>${escapeHtml(p.title)}</b><small>${escapeHtml(p.origin)} · ${escapeHtml(p.level)}</small></div><strong class="portfolio-score">${Math.round(p.score)}%</strong></div><span class="portfolio-status pill">${escapeHtml(p.status.replaceAll('_',' '))}</span><p>${escapeHtml((p.problem_statement||p.business_requirement||'').slice(0,220))}</p>${p.report?.secret_findings?.length?`<p class="secret-warning">Blocked: ${p.report.secret_findings.length} possible secret(s) detected.</p>`:''}<div class="actions"><button class="button ghost portfolio-edit" data-id="${p.id}">Review/edit</button></div></div>`).join(''):'<p class="muted">No portfolio project has been added.</p>';
  $$('.portfolio-edit').forEach(b=>b.onclick=()=>editPortfolioProject(b.dataset.id));
  $('#portfolioBuildList').innerHTML=builds.length?builds.map(b=>`<div class="career-item"><b>${escapeHtml(b.title)}</b><small>${new Date(b.created_at).toLocaleString()} · ${b.selected_projects.length} projects</small><div class="actions"><button class="button ghost portfolio-file" data-url="${b.links.website}" data-open="1">Website</button><button class="button ghost portfolio-file" data-url="${b.links.pdf}">PDF</button><button class="button ghost portfolio-file" data-url="${b.links.zip}">ZIP</button></div></div>`).join(''):'<p class="muted">No portfolio build generated.</p>';
  $$('.portfolio-file').forEach(b=>b.onclick=()=>secureDownload(b.dataset.url,b.dataset.url.includes('zip')?'Portfolio.zip':b.dataset.url.includes('pdf')?'Portfolio.pdf':'Portfolio.html',b.dataset.open==='1'));
  fillJobSelects(d.jobs||[]);
}
function editPortfolioProject(id){const p=state.career.projects.find(x=>x.id===id);if(!p)return;$('#portfolioProjectId').value=p.id;$('#portfolioTitle').value=p.title;$('#portfolioOrigin').value=p.origin;$('#portfolioLevel').value=p.level;$('#portfolioTools').value=p.tools.join(', ');$('#portfolioProblem').value=p.problem_statement;$('#portfolioBusiness').value=p.business_requirement;$('#portfolioArchitecture').value=p.architecture;$('#portfolioImplementation').value=p.implementation;$('#portfolioSecurity').value=p.security_controls;$('#portfolioTesting').value=p.testing;$('#portfolioMonitoring').value=p.monitoring;$('#portfolioTroubleshooting').value=p.troubleshooting;$('#portfolioRollback').value=p.rollback;$('#portfolioOutcome').value=p.outcome;$('#portfolioEvidence').value=p.evidence.join('\n');$('#portfolioRepo').value=p.repository_url;$('#portfolioApprove').checked=['approved','portfolio_ready'].includes(p.status);window.scrollTo({top:0,behavior:'smooth'})}
async function savePortfolioProject(e){e.preventDefault();try{const d={student_id:state.currentStudent.id,id:$('#portfolioProjectId').value,title:$('#portfolioTitle').value,origin:$('#portfolioOrigin').value,level:$('#portfolioLevel').value,tools:splitCsv($('#portfolioTools').value),problem_statement:$('#portfolioProblem').value,business_requirement:$('#portfolioBusiness').value,architecture:$('#portfolioArchitecture').value,implementation:$('#portfolioImplementation').value,security_controls:$('#portfolioSecurity').value,testing:$('#portfolioTesting').value,monitoring:$('#portfolioMonitoring').value,troubleshooting:$('#portfolioTroubleshooting').value,rollback:$('#portfolioRollback').value,outcome:$('#portfolioOutcome').value,evidence:splitCsv($('#portfolioEvidence').value),repository_url:$('#portfolioRepo').value,status:$('#portfolioApprove').checked?'approved':'draft'};const r=await careerApi('/api/v4/portfolio/project/save',{method:'POST',body:JSON.stringify(d)});toast(`Project scored ${Math.round(r.score)}% · ${r.status.replaceAll('_',' ')}`);e.target.reset();$('#portfolioProjectId').value='';state.career=null;await loadCareer();await loadPortfolio()}catch(err){toast(err.message,true)}}
async function buildPortfolio(){try{const d=await careerApi('/api/v4/portfolio/build',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,job_id:$('#portfolioJobSelect').value,template:$('#portfolioTemplate').value})});toast('Portfolio website, PDF and GitHub-ready ZIP generated');state.career=null;await loadCareer();await loadPortfolio();secureDownload(d.links.website,'DevOps_Portfolio.html',true)}catch(e){toast(e.message,true)}}

function bindV4Events(){
  $$('.career-tab').forEach(b=>b.addEventListener('click',()=>switchCareerTab(b.dataset.careerTab)));
  $('#candidateProfileForm')?.addEventListener('submit',saveCandidateProfile);$('#jobSourceForm')?.addEventListener('submit',addJobSource);$('#scanJobSources')?.addEventListener('click',scanJobSources);$('#manualJobForm')?.addEventListener('submit',analyzeManualJob);$('#careerJobSearch')?.addEventListener('input',()=>renderCareerJobs(state.career?.jobs||[]));$('#generateCareerResume')?.addEventListener('click',generateCareerResume);$('#careerEmailForm')?.addEventListener('submit',createCareerEmail);$('#saveGmailClient')?.addEventListener('click',saveGmailClient);$('#connectGmail')?.addEventListener('click',connectGmail);$('#prepareCareerInterview')?.addEventListener('click',prepareCareerInterview);$('#refreshCareer')?.addEventListener('click',()=>{state.career=null;loadCareer()});
  $('#portfolioProjectForm')?.addEventListener('submit',savePortfolioProject);$('#buildPortfolio')?.addEventListener('click',buildPortfolio);$('#refreshPortfolio')?.addEventListener('click',()=>{state.career=null;loadPortfolio()});
}


// ---------------- Billinger v2.5 Studio Experience ----------------
function closeStudioNav(){
  $('#sidebar')?.classList.remove('open');
  document.body.classList.remove('nav-open');
  $('#menuButton')?.setAttribute('aria-expanded','false');
}

function initStudioExperience(){
  if(document.body.dataset.studioBound)return;
  document.body.dataset.studioBound='1';
  const progress=$('#scrollProgress');
  const updateProgress=()=>{
    if(!progress)return;
    const max=Math.max(1,document.documentElement.scrollHeight-window.innerHeight);
    progress.style.width=`${Math.min(100,(window.scrollY/max)*100)}%`;
  };
  window.addEventListener('scroll',updateProgress,{passive:true});
  window.addEventListener('resize',updateProgress,{passive:true});
  updateProgress();

  if(!window.matchMedia('(prefers-reduced-motion: reduce)').matches){
    const revealObserver=new IntersectionObserver(entries=>entries.forEach(entry=>{
      if(entry.isIntersecting){entry.target.classList.add('revealed');revealObserver.unobserve(entry.target)}
    }),{threshold:.08,rootMargin:'0px 0px -40px'});
    $$('.stats-grid,.dashboard-grid,.library-audit-strip,.page-header').forEach(el=>{
      el.classList.add('reveal-ready');revealObserver.observe(el);
    });
  }

  const halo=$('#pointerHalo');
  if(halo&&window.matchMedia('(pointer:fine)').matches&&!window.matchMedia('(prefers-reduced-motion: reduce)').matches){
    window.addEventListener('pointermove',e=>{
      halo.style.left=`${e.clientX}px`;halo.style.top=`${e.clientY}px`;halo.style.opacity='1';
    },{passive:true});
    document.addEventListener('pointerover',e=>{if(e.target.closest('button,a,input,select,textarea,.tool-card,.career-job-card'))halo.classList.add('active')});
    document.addEventListener('pointerout',e=>{if(e.target.closest('button,a,input,select,textarea,.tool-card,.career-job-card'))halo.classList.remove('active')});
  }
}


// ---------------- Billinger v2.8: Dark Accessibility & Eye Comfort ----------------
const DISPLAY_PREF_KEY='billinger_display_v28';
function getDisplayPreferences(){
  const defaults={theme:'comfort',textSize:'normal',highContrast:true,reduceMotion:true};
  try{return {...defaults,...JSON.parse(localStorage.getItem(DISPLAY_PREF_KEY)||'{}')}}catch(_){return defaults}
}
function applyDisplayPreferences(pref=getDisplayPreferences(),persist=false){
  const b=document.body;if(!b)return;
  b.classList.remove('theme-comfort-dark','theme-standard-dark','high-contrast','text-large','text-xlarge','reduce-motion');
  b.classList.add(pref.theme==='standard'?'theme-standard-dark':'theme-comfort-dark');
  if(pref.highContrast!==false)b.classList.add('high-contrast');
  if(pref.textSize==='large')b.classList.add('text-large');
  if(pref.textSize==='xlarge')b.classList.add('text-xlarge');
  if(pref.reduceMotion!==false)b.classList.add('reduce-motion');
  document.documentElement.style.colorScheme='dark';
  const themeMeta=document.querySelector('meta[name="theme-color"]');if(themeMeta)themeMeta.content=pref.theme==='standard'?'#070b12':'#0b1016';
  if(persist){try{localStorage.setItem(DISPLAY_PREF_KEY,JSON.stringify(pref))}catch(_){}}
  const theme=$('#displayTheme'),size=$('#displayTextSize'),contrast=$('#displayHighContrast'),motion=$('#displayReduceMotion');
  if(theme)theme.value=pref.theme||'comfort';if(size)size.value=pref.textSize||'normal';if(contrast)contrast.checked=pref.highContrast!==false;if(motion)motion.checked=pref.reduceMotion!==false;
  const quick=$('#comfortQuickToggle');if(quick)quick.textContent=pref.theme==='comfort'?'☾ Comfort':'◐ Standard';
}
function saveDisplayPreferences(){
  const pref={theme:$('#displayTheme')?.value||'comfort',textSize:$('#displayTextSize')?.value||'normal',highContrast:$('#displayHighContrast')?.checked!==false,reduceMotion:$('#displayReduceMotion')?.checked!==false};
  applyDisplayPreferences(pref,true);toast('Display preferences saved on this browser');
}
function toggleComfortTheme(){const p=getDisplayPreferences();p.theme=p.theme==='comfort'?'standard':'comfort';applyDisplayPreferences(p,true)}
function bindV28DisplayEvents(){
  ['displayTheme','displayTextSize','displayHighContrast','displayReduceMotion'].forEach(id=>$('#'+id)?.addEventListener('change',saveDisplayPreferences));
  $('#comfortQuickToggle')?.addEventListener('click',toggleComfortTheme);
  applyDisplayPreferences(getDisplayPreferences(),false);
}

// ---------------- Billinger v2.6: Adaptive Multi-Provider AI Mentor ----------------
function renderAiAnalysis(value){
  if(value===null||value===undefined)return '';
  if(Array.isArray(value))return `<ul>${value.map(x=>`<li>${typeof x==='object'?renderAiAnalysis(x):escapeHtml(x)}</li>`).join('')}</ul>`;
  if(typeof value==='object')return `<div class="ai-analysis-grid">${Object.entries(value).map(([k,v])=>`<section><h4>${escapeHtml(k.replaceAll('_',' '))}</h4>${renderAiAnalysis(v)}</section>`).join('')}</div>`;
  return `<p>${escapeHtml(String(value)).replace(/\n/g,'<br>')}</p>`;
}

async function loadAiControl(){
  try{
    const status=await api('/api/v6/ai/status');
    const configured=status.configured_providers||[];
    const route=status.routes?.lesson_tutor||[];
    $('#aiStatusBanner').innerHTML=`<div><span class="eyebrow">FAILOVER STATUS</span><h2>${status.enabled?'Adaptive AI enabled':'Online AI disabled'}</h2><p>${configured.length?`${configured.length} provider(s) ready · Tutor route: ${route.join(' → ')}`:'No online provider key is configured. The complete deterministic course remains available.'}</p></div><span class="pill">${status.auto_failover?'Automatic failover ON':'Manual routing'}</span>`;
  }catch(e){$('#aiStatusBanner').innerHTML=`<div><h2>AI status unavailable</h2><p>${escapeHtml(e.message)}</p></div>`}
  if(!adminToken()){
    $('#aiAdminLocked')?.classList.remove('hidden');$('#aiAdminDashboard')?.classList.add('hidden');$('#aiSecretStorage').textContent='Administrator locked';return;
  }
  try{
    const d=await adminApi('/api/v6/ai/dashboard');state.aiDashboard=d;renderAiDashboard(d);
    $('#aiAdminLocked').classList.add('hidden');$('#aiAdminDashboard').classList.remove('hidden');
  }catch(e){$('#aiAdminLocked').classList.remove('hidden');$('#aiAdminDashboard').classList.add('hidden');$('#aiSecretStorage').textContent='Administrator session required';}
}

function renderAiDashboard(d){
  $('#aiSecretStorage').textContent=d.secret_storage;
  const providerIcons={gemini:'✦',openai:'◎',groq:'⚡',openrouter:'◇'};
  const cache=modelCacheMap(d);
  $('#aiProviderOverview').innerHTML=d.providers.map(p=>`<button type="button" class="ai-provider-chip" data-provider-jump="${p.provider}"><span>${providerIcons[p.provider]||'AI'}</span><b>${escapeHtml(p.label)}</b><small>${p.configured&&p.enabled?'Configured':p.configured?'Saved / disabled':'Add API key'}</small></button>`).join('');
  $('#aiProviderGrid').innerHTML=d.providers.map(p=>`<form id="ai-provider-card-${p.provider}" class="panel ai-provider-card" data-ai-provider-form="${p.provider}">
    <div class="ai-provider-head"><span class="ai-provider-icon">${providerIcons[p.provider]||'AI'}</span><div><span class="eyebrow">${escapeHtml(p.provider.toUpperCase())}</span><h3>${escapeHtml(p.label)}</h3><small>${escapeHtml(p.purpose)}</small></div><span class="provider-state ${p.last_status}">${escapeHtml(p.cooldown_active?'cooldown':p.last_status)}</span></div>
    <label class="checkbox-label"><input name="enabled" type="checkbox" ${p.enabled?'checked':''}><span>Enabled in fallback routes</span></label>
    <label>API key<input name="api_key" type="password" autocomplete="new-password" placeholder="${p.configured?`Saved as ${escapeHtml(p.key_hint)} — leave blank to keep`:'Paste API key'}"></label>
    <div class="model-actions"><label>Model<input name="model" list="model-list-${p.provider}" value="${escapeHtml(p.model)}"><datalist id="model-list-${p.provider}">${(cache[p.provider]?.models||[]).slice(0,500).map(m=>`<option value="${escapeHtml(m.id)}">`).join('')}</datalist></label><button class="button secondary ai-provider-discover" type="button" data-provider="${p.provider}">Discover models</button></div><p class="provider-model-note">${cache[p.provider]?.status==='ready'?`${cache[p.provider].models.length} models discovered ${cache[p.provider].discovered_at?new Date(cache[p.provider].discovered_at).toLocaleString():''}`:'Discover models after saving the key.'}</p>
    <label>Daily request limit<input name="daily_limit" type="number" min="1" max="5000" value="${p.daily_limit}"></label>
    <div class="provider-usage"><span>${p.used_today} / ${p.daily_limit} calls today</span><span>${p.last_success_at?`Last success ${new Date(p.last_success_at).toLocaleString()}`:'No successful call yet'}</span></div>
    ${p.last_error?`<p class="provider-error">${escapeHtml(p.last_error)}</p>`:''}
    <div class="actions"><button class="button primary ai-provider-save" type="submit">Save securely</button><button class="button secondary ai-provider-test" type="button" data-provider="${p.provider}">Test connection</button><button class="button ghost ai-provider-remove" type="button" data-provider="${p.provider}">Remove key</button></div>
  </form>`).join('');
  $$('[data-provider-jump]').forEach(b=>b.onclick=()=>{const card=$(`#ai-provider-card-${b.dataset.providerJump}`);card?.scrollIntoView({behavior:'smooth',block:'center'});card?.classList.add('provider-highlight');setTimeout(()=>card?.classList.remove('provider-highlight'),1300)});
  $$('[data-ai-provider-form]').forEach(f=>f.addEventListener('submit',saveAiProvider));
  $$('.ai-provider-test').forEach(b=>b.onclick=()=>testAiProvider(b.dataset.provider,b));
  $$('.ai-provider-discover').forEach(b=>b.onclick=()=>discoverAiModels(b.dataset.provider,b));
  $$('.ai-provider-remove').forEach(b=>b.onclick=()=>removeAiProvider(b.dataset.provider));
  const s=d.settings;$('#onlineAiEnabled').checked=!!s.online_ai_enabled;$('#autoAiFailover').checked=!!s.auto_failover;$('#redactAiPii').checked=!!s.redact_personal_data;$('#allowAiStudentContent').checked=!!s.allow_student_content;$('#aiGlobalDailyLimit').value=s.global_daily_request_limit;$('#aiRequestTimeout').value=s.request_timeout_seconds;$('#aiMaxOutputTokens').value=s.max_output_tokens;
  $('#aiTaskRoutes').innerHTML=d.tasks.map(t=>`<div class="ai-route-row"><div><b>${escapeHtml(t.label)}</b><small>${escapeHtml(t.task)}</small></div><input data-ai-route-input="${t.task}" value="${escapeHtml(t.providers.join(', '))}"><button class="button secondary ai-route-save" data-task="${t.task}">Save route</button></div>`).join('');
  $('#fallbackDryRunTask').innerHTML=d.tasks.map(t=>`<option value="${escapeHtml(t.task)}">${escapeHtml(t.label)}</option>`).join('');
  $('#aiModelDiscoverySummary').innerHTML=d.providers.map(p=>{const c=cache[p.provider]||{};return `<div class="model-cache-item"><b>${escapeHtml(p.label)}</b><small>${c.status==='ready'?`${(c.models||[]).length} models · ${c.discovered_at?new Date(c.discovered_at).toLocaleString():'cached'}`:escapeHtml(c.error||c.status||'not checked')}</small></div>`}).join('');
  $$('.ai-route-save').forEach(b=>b.onclick=()=>saveAiRoute(b.dataset.task));
  $('#aiUsageLog').innerHTML=d.recent_usage.length?d.recent_usage.map(x=>`<div class="ai-usage-item"><span class="provider-state ${x.status}">${escapeHtml(x.status)}</span><div><b>${escapeHtml(x.task.replaceAll('_',' '))}</b><small>${escapeHtml(x.provider)} · ${escapeHtml(x.model)}</small></div><time>${x.duration_ms} ms<br>${new Date(x.created_at).toLocaleString()}</time></div>`).join(''):'<p class="muted">No AI calls have been made.</p>';
}

function openAiAdmin(){state.pendingAiAdmin=true;openAdminDialog()}
async function saveAiProvider(e){e.preventDefault();const f=e.currentTarget,p=f.dataset.aiProviderForm,button=$('.ai-provider-save',f);button.disabled=true;button.textContent='Encrypting…';try{await adminApi('/api/v6/ai/provider/save',{method:'POST',body:JSON.stringify({provider:p,enabled:f.enabled.checked,api_key:f.api_key.value,model:f.model.value,daily_limit:Number(f.daily_limit.value)})});f.api_key.value='';toast(`${p} configuration saved locally`);await loadAiControl()}catch(err){toast(err.message,true)}finally{button.disabled=false;button.textContent='Save securely'}}
async function testAiProvider(provider,button){button.disabled=true;button.textContent='Testing…';try{const d=await adminApi('/api/v6/ai/provider/test',{method:'POST',body:JSON.stringify({provider})});toast(`${provider} connected in ${d.duration_ms} ms`);await loadAiControl()}catch(e){toast(e.message,true)}finally{button.disabled=false;button.textContent='Test connection'}}
async function removeAiProvider(provider){if(!confirm(`Remove the saved ${provider} API key from this bot?`))return;try{await adminApi('/api/v6/ai/provider/save',{method:'POST',body:JSON.stringify({provider,remove_key:true})});toast(`${provider} key removed`);await loadAiControl()}catch(e){toast(e.message,true)}}
async function saveAiRoute(task){const input=$(`[data-ai-route-input="${CSS.escape(task)}"]`);const providers=splitCsv(input.value).map(x=>x.toLowerCase());try{await adminApi('/api/v6/ai/route/save',{method:'POST',body:JSON.stringify({task,providers})});toast(`${task.replaceAll('_',' ')} route saved`);await loadAiControl()}catch(e){toast(e.message,true)}}
async function saveAiGlobalSettings(e){e.preventDefault();try{await adminApi('/api/v6/ai/settings/save',{method:'POST',body:JSON.stringify({online_ai_enabled:$('#onlineAiEnabled').checked,auto_failover:$('#autoAiFailover').checked,redact_personal_data:$('#redactAiPii').checked,allow_student_content:$('#allowAiStudentContent').checked,global_daily_request_limit:Number($('#aiGlobalDailyLimit').value),request_timeout_seconds:Number($('#aiRequestTimeout').value),max_output_tokens:Number($('#aiMaxOutputTokens').value)})});toast('AI privacy, budget and failover policy saved');await loadAiControl()}catch(e){toast(e.message,true)}}

async function runCurriculumAudit(e){e.preventDefault();const box=$('#curriculumAuditResult');box.className='ai-analysis-box';box.innerHTML='<p>Building the exact coverage manifest and routing the audit…</p>';try{const coverage=await api('/api/v2/coverage');const reduced={summary:coverage.summary,scope_notice:coverage.scope_notice,tools:coverage.tools.map(t=>({name:t.name,commands:t.command_examples,levels:t.levels.map(l=>({name:l.name,lessons:l.lesson_titles,labs:l.labs.map(x=>x.title)})),tickets:t.tickets.map(x=>x.title),incidents:t.incidents.map(x=>x.title),capstones:t.capstones.map(x=>x.title)}))};const d=await adminApi('/api/v6/ai/curriculum/audit',{method:'POST',body:JSON.stringify({scope:$('#curriculumAuditScope').value,current_version:$('#curriculumAuditVersion').value,coverage:reduced})});box.innerHTML=`<div class="ai-result-head"><span class="pill">Review required</span><b>${escapeHtml(d.provider)} · ${escapeHtml(d.model)}</b></div>${renderAiAnalysis(d.proposal)}<p class="legal-note">${escapeHtml(d.notice)}</p>`;toast('Curriculum gap proposal created for administrator review');await loadAiControl()}catch(err){box.innerHTML=`<p class="provider-error">${escapeHtml(err.message)}</p>`;toast(err.message,true)}}

async function analyzeLastTestWithAi(){if(!state.lastTestResult)return;const box=$('#testAiAnalysis');box.className='ai-analysis-box';box.innerHTML='<p>Analyzing repeated mistakes, missing commands and revision priorities…</p>';try{const d=await api('/api/v6/ai/test/analyze',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,...state.lastTestResult})});box.innerHTML=`<div class="ai-result-head"><span class="pill">AI advisory</span><b>${escapeHtml(d.provider_label)} · ${escapeHtml(d.model)}</b></div>${renderAiAnalysis(d.analysis)}`;toast('Adaptive test analysis completed')}catch(e){box.innerHTML=`<p class="provider-error">${escapeHtml(e.message)}</p>`;toast(e.message,true)}}

async function startAiTest(){if(!state.currentStudent)return;const button=$('#startAiTest');button.disabled=true;button.textContent='Generating questions…';try{const d=await api('/api/v6/ai/questions/generate',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,mode:$('#aiTestMode').value,tool:$('#aiTestTool').value,difficulty:$('#aiTestDifficulty').value,count:Number($('#aiTestCount').value),context:$('#aiTestContext').value})});state.aiTest=d;$('#aiTestSetup').classList.add('hidden');$('#aiTestResult').classList.add('hidden');$('#aiTestRunner').classList.remove('hidden');$('#aiTestRoute').textContent=`${d.provider} · ${d.model}`;$('#aiTestProgressText').textContent=`${d.questions.length} adaptive questions · pass mark ${d.pass_mark}%`;$('#aiTestForm').innerHTML=d.questions.map((q,i)=>`<article class="question-card panel"><div class="question-meta"><span>AI question ${i+1} · ${escapeHtml(d.difficulty)}</span><span>${escapeHtml(d.mode)}</span></div><h3>${escapeHtml(q.prompt).replace(/\n/g,'<br>')}</h3><textarea name="aiq_${q.id}" rows="8" placeholder="Give commands, reasoning, evidence, security controls and rollback where relevant..."></textarea>${q.source_url?`<p class="legal-note">${escapeHtml(q.attribution||q.source_title)} <a href="${escapeHtml(q.source_url)}" target="_blank" rel="noreferrer">Open source</a></p>`:`<p class="legal-note">${escapeHtml(q.source_title||'AI-generated role simulation')} · verify commands against official documentation.</p>`}</article>`).join('');$('#aiTestForm').oninput=()=>{const answered=d.questions.filter(q=>$(`[name="aiq_${CSS.escape(q.id)}"]`)?.value.trim()).length;$('#aiTestProgressMeter').style.width=`${answered/d.questions.length*100}%`};$('#aiTestProvider').textContent=`Generated by ${d.provider} · ${d.model}`;toast('Adaptive AI test generated')}catch(e){toast(e.message,true)}finally{button.disabled=false;button.textContent='Generate adaptive AI test'}}
async function submitAiTest(){if(!state.aiTest)return;const button=$('#submitAiTest');button.disabled=true;button.textContent='Evaluating…';const answers=state.aiTest.questions.map(q=>({id:q.id,answer:$(`[name="aiq_${CSS.escape(q.id)}"]`)?.value||''}));try{const r=await api('/api/v6/ai/questions/submit',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,session_id:state.aiTest.session_id,answers})});$('#aiTestRunner').classList.add('hidden');const box=$('#aiTestResult');box.className='panel result-summary';box.innerHTML=`<div class="score-hero ${r.passed?'pass':'fail'}"><strong>${r.score}%</strong><h2>${r.passed?'Adaptive test passed':'Targeted revision required'}</h2><p>Generated through ${escapeHtml(r.provider)} · ${escapeHtml(r.model)}</p></div><div class="detail-list">${r.details.map((d,i)=>`<div class="detail-item"><b>Question ${i+1}: ${d.score}%</b><p><b>Missing:</b> ${escapeHtml((d.missing||[]).join(', ')||'none')}</p><details><summary>Model answer</summary><p>${escapeHtml(d.ideal_answer)}</p></details></div>`).join('')}</div>${r.ai_analysis?`<div class="ai-analysis-box"><div class="ai-result-head"><span class="pill">Adaptive diagnosis</span><b>${escapeHtml(r.ai_analysis.provider_label)} · ${escapeHtml(r.ai_analysis.model)}</b></div>${renderAiAnalysis(r.ai_analysis.analysis)}</div>`:''}${r.ai_analysis_error?`<p class="provider-error">AI summary unavailable: ${escapeHtml(r.ai_analysis_error)}</p>`:''}<button id="newAiTest" class="button secondary wide">Generate another adaptive test</button>`;$('#newAiTest').onclick=()=>{box.classList.add('hidden');$('#aiTestSetup').classList.remove('hidden');state.aiTest=null};toast('Adaptive AI test evaluated')}catch(e){toast(e.message,true)}finally{button.disabled=false;button.textContent='Submit adaptive AI test'}}

function bindV26Events(){
  $('#unlockAiAdmin')?.addEventListener('click',openAiAdmin);$('#openAiAdminDialog')?.addEventListener('click',openAiAdmin);$('#aiGlobalSettingsForm')?.addEventListener('submit',saveAiGlobalSettings);$('#curriculumAuditForm')?.addEventListener('submit',runCurriculumAudit);$('#startAiTest')?.addEventListener('click',startAiTest);$('#submitAiTest')?.addEventListener('click',submitAiTest);
}

// ---------------- Billinger v2.7: Final Readiness and Mastery ----------------
async function loadFinalReadiness(){
  if(!state.currentStudent||!state.studentToken)return;
  try{
    const d=await api(`/api/v7/readiness?student_id=${state.currentStudent.id}`);state.finalReadiness=d;renderFinalReadiness(d);
    await api('/api/v7/readiness/seen',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id})});
  }catch(e){toast(e.message,true)}
}
function renderFinalReadiness(d){
  $('#finalReadinessPercent').textContent=`${d.readiness_percent}%`;
  $('#finalReadinessTitle').textContent=d.ready_to_learn?'Ready to begin the structured course':'Complete the required launch checks';
  $('#finalReadinessNotice').textContent=d.notice;
  $('#goToLearningFromReadiness').disabled=!d.ready_to_learn;
  const callout=$('#dashboardReadinessCallout');if(callout){callout.classList.toggle('ready',d.ready_to_learn);$('h2',callout).textContent=d.ready_to_learn?'Learning launch gate passed':'Complete readiness before regular learning';$('p',callout).textContent=d.ready_to_learn?'Your baseline, backup, learning goal, library and first plan are ready.':'Baseline, verified backup, learning goal, and first plan are checked in one place.'}
  $('#finalReadinessSteps').innerHTML=d.steps.map(x=>`<article class="readiness-step ${x.complete?'complete':''} ${x.required?'required':''}"><div class="readiness-step-head"><b>${escapeHtml(x.label)}</b><span class="step-state">${x.complete?'✓ Complete':x.required?'Required':'Optional'}</span></div><small>${escapeHtml(x.detail)}</small></article>`).join('');
  const p=d.profile||{};populateReadinessRoles(p.target_role||'Junior DevOps Engineer');$('#readinessMinutes').value=p.study_minutes||90;
  const b=d.baseline;if(b){$('#baselineSummary').className='mini-result success';$('#baselineSummary').innerHTML=`<b>${escapeHtml(b.classification)}</b><br>${b.score}% · Start with ${escapeHtml(b.recommended_start||'linux')}`}
  else{$('#baselineSummary').className='mini-result';$('#baselineSummary').textContent='No baseline result yet.'}
  if(d.environment?.results)renderEnvironment(d.environment.results,$('#finalEnvironmentSummary'));else $('#finalEnvironmentSummary').textContent='Not scanned yet.';
  $('#backupPlanSummary').className=`mini-result ${d.backup?.status==='healthy'?'success':'warning'}`;$('#backupPlanSummary').textContent=d.backup?.summary||'No verified backup yet.';
}
async function populateReadinessRoles(selected=''){
  let roles=state.v23Status?.roles;
  if(!roles){try{state.v23Status=await api('/api/v3/status');roles=state.v23Status.roles}catch(_){roles=[]}}
  const el=$('#readinessRole');if(!el)return;const current=selected||el.value;el.innerHTML=(roles||[]).map(r=>`<option ${r===current?'selected':''}>${escapeHtml(r)}</option>`).join('');
}
async function saveReadinessProfile(e){e.preventDefault();if(!state.currentStudent)return;try{await api('/api/v3/profile/save',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,name:state.currentStudent.name,email:state.currentStudent.email||'',target_role:$('#readinessRole').value,study_minutes:Number($('#readinessMinutes').value),active:true,active_track:'Full DevOps Track'})});toast('Learning goal saved');await loadFinalReadiness()}catch(err){toast(err.message,true)}}
async function startBaselineAssessment(){if(!state.currentStudent)return;try{const d=await api('/api/v7/baseline/start',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id})});state.baselineSession=d;$('#baselineRunner').classList.remove('hidden');$('#baselineForm').innerHTML=d.questions.map((q,i)=>`<article class="question-card panel"><div class="question-meta"><span>Baseline ${i+1} of ${d.count}</span><span>${escapeHtml(q.tool)} · ${escapeHtml(q.difficulty)}</span></div><h3>${escapeHtml(q.prompt)}</h3><div class="choice-list">${q.choices.map((c,j)=>`<label><input type="radio" name="base_${escapeHtml(q.id)}" value="${j}"><span>${escapeHtml(c)}</span></label>`).join('')}</div></article>`).join('');$('#baselineForm').onchange=()=>{const answered=d.questions.filter(q=>$(`input[name="base_${CSS.escape(q.id)}"]:checked`)).length;$('#baselineProgressText').textContent=`${answered} of ${d.count} answered`;$('#baselineProgressMeter').style.width=`${answered/d.count*100}%`};$('#baselineRunner').scrollIntoView({behavior:'smooth',block:'start'})}catch(e){toast(e.message,true)}}
async function submitBaselineAssessment(){const d=state.baselineSession;if(!d)return;const answers=d.questions.map(q=>({id:q.id,answer:Number($(`input[name="base_${CSS.escape(q.id)}"]:checked`)?.value??-1)}));if(answers.some(x=>x.answer<0)&&!confirm('Some questions are unanswered. Submit anyway?'))return;const button=$('#submitBaseline');button.disabled=true;button.textContent='Scoring baseline…';try{const r=await api('/api/v7/baseline/submit',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id,session_id:d.session_id,answers})});$('#baselineForm').innerHTML=`<div class="baseline-result-hero"><strong>${r.score}%</strong><h2>${escapeHtml(r.classification)}</h2><p>Recommended starting focus: ${escapeHtml(r.recommended_start_name)}</p></div><div class="baseline-domain-grid">${Object.entries(r.domain_scores).map(([k,v])=>`<div class="baseline-domain"><b>${escapeHtml(k)}</b><span>${v}%</span></div>`).join('')}</div><p class="legal-note">${escapeHtml(r.message)}</p>`;button.classList.add('hidden');state.baselineSession=null;toast('Baseline assessment completed');await loadFinalReadiness()}catch(e){toast(e.message,true)}finally{button.disabled=false;button.textContent='Submit baseline assessment'}}
function renderEnvironment(d,target){if(!target)return;const rows=d.tools||[];target.className='environment-results';target.innerHTML=rows.map(x=>`<div class="environment-item"><span class="${x.installed?'ok':'missing'}">${x.installed?'✓':'○'}</span><div><b>${escapeHtml(x.name)} · ${escapeHtml(x.purpose)}</b><small>${escapeHtml(x.version)}</small></div></div>`).join('')+`<p class="legal-note">Core ready: ${d.core_ready?'yes':'Python runtime not detected by this scan'}. Missing optional tools do not block learning.</p>`}
async function runEnvironmentCheck(targetId){if(!state.currentStudent)return;const target=$('#'+targetId);if(target)target.innerHTML='<p>Running read-only version checks…</p>';try{const d=await api('/api/v7/environment/check',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id})});renderEnvironment(d,target);toast('Environment scan completed');await loadFinalReadiness()}catch(e){if(target)target.innerHTML=`<p class="provider-error">${escapeHtml(e.message)}</p>`;toast(e.message,true)}}
async function createReadinessBackup(){if(!adminToken()){openAdminDialog();toast('Unlock administrator access, then create the backup.',true);return}try{const d=await adminApi('/api/v3/admin/backup/create',{method:'POST',body:'{}'});toast(`Backup created: ${d.file_name||d.id}`);const h=await adminApi('/api/v7/backup/health');$('#backupPlanSummary').className=`mini-result ${h.status==='healthy'?'success':'warning'}`;$('#backupPlanSummary').textContent=h.summary;await loadFinalReadiness()}catch(e){toast(e.message,true)}}
async function generateFirstPlan(){if(!state.currentStudent)return;try{const d=await api('/api/v3/plan/generate',{method:'POST',body:JSON.stringify({student_id:state.currentStudent.id})});$('#backupPlanSummary').className='mini-result success';$('#backupPlanSummary').innerHTML=`Plan generated: ${d.study_minutes} minutes · focus ${escapeHtml(d.focus_tool)}`;toast('Today’s learning plan generated');await loadFinalReadiness()}catch(e){toast(e.message,true)}}
async function loadMasteryGates(){if(!state.currentStudent)return;try{const d=await api(`/api/v7/mastery?student_id=${state.currentStudent.id}`);state.mastery=d;$('#masteryGateGrid').innerHTML=d.tools.map(x=>`<article class="mastery-card ${x.mastered?'mastered':''}"><div class="mastery-card-head"><div><span class="eyebrow">${escapeHtml(x.icon)} ${escapeHtml(x.tool)}</span><h3>${escapeHtml(x.name)}</h3></div><span class="mastery-percent">${x.percent}%</span></div><div class="gate-list">${x.requirements.map(r=>`<div class="gate-row ${r.complete?'complete':''}"><i>${r.complete?'✓':'○'}</i><span>${escapeHtml(r.label)}</span><b>${r.current}${r.unit||''} / ${r.target}${r.unit||''}</b></div>`).join('')}</div></article>`).join('')}catch(e){toast(e.message,true)}}
async function verifySystemBackup(){const box=$('#systemBackupHealth');if(!adminToken()){box.className='mini-result warning';box.textContent='Unlock administrator access to verify backups.';return}try{const h=await adminApi('/api/v7/backup/health');box.className=`mini-result ${h.status==='healthy'?'success':'warning'}`;box.textContent=h.summary}catch(e){box.className='mini-result warning';box.textContent=e.message}}

async function loadCourseFreshness(){try{const d=await api('/api/v7/freshness');$('#courseFreshnessSummary').innerHTML=`<article><small>Recorded current</small><strong>${d.summary.current}</strong></article><article><small>Review due/unreviewed</small><strong>${d.summary.review_due}</strong></article><article><small>Deprecated</small><strong>${d.summary.deprecated}</strong></article><article><small>AI proposals pending</small><strong>${d.pending_ai_proposals}</strong></article>`;const unlocked=!!adminToken();$('#courseFreshnessGrid').innerHTML=d.items.map(x=>`<form class="freshness-card" data-freshness-form="${x.tool}"><div class="freshness-head"><div><span class="eyebrow">${escapeHtml(x.icon)} ${escapeHtml(x.tool)}</span><h3>${escapeHtml(x.name)}</h3></div><span class="freshness-state ${escapeHtml(x.effective_status)}">${escapeHtml(x.effective_status.replaceAll('_',' '))}</span></div><label>Course version<input name="course_version" value="${escapeHtml(x.course_version)}" ${unlocked?'':'readonly'}></label><label>Tool version covered<input name="tool_version_covered" value="${escapeHtml(x.tool_version_covered)}" ${unlocked?'':'readonly'}></label><label>Official documentation<input name="official_doc_url" value="${escapeHtml(x.official_doc_url)}" ${unlocked?'':'readonly'}></label><div class="form-grid two"><label>Last reviewed<input name="last_reviewed" type="date" value="${escapeHtml(x.last_reviewed)}" ${unlocked?'':'readonly'}></label><label>Status<select name="review_status" ${unlocked?'':'disabled'}><option value="review_required" ${x.review_status==='review_required'?'selected':''}>Review required</option><option value="current" ${x.review_status==='current'?'selected':''}>Current</option><option value="review_due" ${x.review_status==='review_due'?'selected':''}>Review due</option><option value="deprecated" ${x.review_status==='deprecated'?'selected':''}>Deprecated</option></select></label></div><label>Deprecated or migration notes<textarea name="deprecated_notes" rows="2" ${unlocked?'':'readonly'}>${escapeHtml(x.deprecated_notes)}</textarea></label><label>Reviewer<input name="reviewer" value="${escapeHtml(x.reviewer)}" ${unlocked?'':'readonly'}></label>${unlocked?'<button class="button secondary wide">Save reviewed metadata</button>':'<p class="legal-note">Unlock administrator access to edit freshness records.</p>'}</form>`).join('');$$('[data-freshness-form]').forEach(f=>f.onsubmit=saveFreshnessRecord)}catch(e){toast(e.message,true)}}
async function saveFreshnessRecord(e){e.preventDefault();const f=e.currentTarget;try{await adminApi('/api/v7/freshness/save',{method:'POST',body:JSON.stringify({tool:f.dataset.freshnessForm,course_version:f.course_version.value,tool_version_covered:f.tool_version_covered.value,official_doc_url:f.official_doc_url.value,last_reviewed:f.last_reviewed.value,review_status:f.review_status.value,deprecated_notes:f.deprecated_notes.value,reviewer:f.reviewer.value})});toast('Course freshness metadata saved');await loadCourseFreshness()}catch(err){toast(err.message,true)}}

function modelCacheMap(d){const m={};(d.model_cache||[]).forEach(x=>m[x.provider]=x);return m}
async function discoverAiModels(provider,button){button.disabled=true;button.textContent='Discovering…';try{const d=await adminApi('/api/v7/ai/models/discover',{method:'POST',body:JSON.stringify({provider})});toast(`${provider}: ${d.count} account-accessible models found`);await loadAiControl()}catch(e){toast(e.message,true)}finally{button.disabled=false;button.textContent='Discover models'}}
async function runFallbackDryRun(e){e.preventDefault();const box=$('#fallbackDryRunResult');try{const d=await adminApi('/api/v7/ai/fallback/dry-run',{method:'POST',body:JSON.stringify({task:$('#fallbackDryRunTask').value,simulated_failures:splitCsv($('#fallbackSimulatedProviders').value)})});box.className=`mini-result ${d.would_succeed?'success':'warning'}`;box.innerHTML=`<b>${d.would_succeed?`Would use ${escapeHtml(d.selected_provider)}`:'No provider would be available'}</b><br>${d.trace.map(x=>`${escapeHtml(x.provider)}: ${escapeHtml(x.status)}`).join(' → ')}<br><small>${escapeHtml(d.notice)}</small>`}catch(err){box.className='mini-result warning';box.textContent=err.message}}

function bindV27Events(){
  $('#refreshFinalReadiness')?.addEventListener('click',loadFinalReadiness);$('#goToLearningFromReadiness')?.addEventListener('click',()=>showPage('roadmap'));$('#readinessProfileForm')?.addEventListener('submit',saveReadinessProfile);$('#startBaselineAssessment')?.addEventListener('click',startBaselineAssessment);$('#submitBaseline')?.addEventListener('click',submitBaselineAssessment);$('#cancelBaseline')?.addEventListener('click',()=>$('#baselineRunner').classList.add('hidden'));$('#runFinalEnvironmentCheck')?.addEventListener('click',()=>runEnvironmentCheck('finalEnvironmentSummary'));$('#runSystemEnvironmentCheck')?.addEventListener('click',()=>runEnvironmentCheck('systemEnvironmentResults'));$('#createFinalBackup')?.addEventListener('click',createReadinessBackup);$('#generateFirstPlan')?.addEventListener('click',generateFirstPlan);$('#refreshMasteryGates')?.addEventListener('click',loadMasteryGates);$('#verifyBackupHealth')?.addEventListener('click',verifySystemBackup);$('#refreshCourseFreshness')?.addEventListener('click',loadCourseFreshness);$('#fallbackDryRunForm')?.addEventListener('submit',runFallbackDryRun);
}
