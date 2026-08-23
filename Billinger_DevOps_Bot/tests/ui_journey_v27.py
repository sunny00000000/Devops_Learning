"""Browser-rendered v2.7 first-run readiness and mastery-gate journey."""
from __future__ import annotations
import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from ui_journey_v26 import MOCK
ROOT=Path(__file__).resolve().parents[1]

def main():
    html=(ROOT/'static/index.html').read_text(encoding='utf-8')
    html=re.sub(r'<link rel="stylesheet" href="/styles\.css\?v=[^"]+">','',html)
    html=re.sub(r'<script src="/app\.js\?v=[^"]+"></script>','',html)
    css=(ROOT/'static/styles.css').read_text(encoding='utf-8');js=(ROOT/'static/app.js').read_text(encoding='utf-8')
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1440,'height':1000})
        page.on('pageerror',lambda e:errors.append('pageerror:'+str(e)))
        page.on('console',lambda m:errors.append('console:'+m.text) if m.type=='error' else None)
        page.set_content(html,wait_until='domcontentloaded');page.add_style_tag(content=css);page.add_script_tag(content='window.v27FirstRun=true');page.add_script_tag(content=MOCK);page.add_script_tag(content=js);page.evaluate('init()')
        page.wait_for_selector('#page-readiness.active')
        page.wait_for_function("document.querySelectorAll('.readiness-step').length===8")
        assert page.locator('.readiness-work-grid > *').count()==4
        page.wait_for_function("document.querySelectorAll('.mastery-card').length===21")
        assert page.locator('.mastery-card .gate-row').count()==21*9
        page.click('#startBaselineAssessment');page.wait_for_function("document.querySelectorAll('#baselineForm .question-card').length===20")
        for i in range(20): page.locator('#baselineForm .question-card').nth(i).locator('input').first.check()
        page.once('dialog',lambda d:d.accept());page.click('#submitBaseline');page.wait_for_selector('.baseline-result-hero')
        assert 'Intermediate learner' in page.locator('.baseline-result-hero').inner_text()
        page.click('#runFinalEnvironmentCheck');page.wait_for_function("document.querySelectorAll('#finalEnvironmentSummary .environment-item').length===10")
        page.screenshot(path=str(ROOT/'docs/v27_final_readiness.png'),full_page=False)
        page.click('#menuButton');page.locator('.nav-item[data-page="system"]').click();page.wait_for_selector('#page-system.active')
        page.wait_for_function("document.querySelectorAll('[data-freshness-form]').length===21")
        page.screenshot(path=str(ROOT/'docs/v27_system_freshness.png'),full_page=False)
        browser.close()
    assert not errors,errors
    print('V2.7 FINAL READINESS BROWSER JOURNEY PASSED')
    print(json.dumps({'readiness_steps':8,'baseline_questions':20,'environment_tools':10,'mastery_tools':21,'gates_per_tool':9,'freshness_records':21,'console_errors':0},indent=2))
if __name__=='__main__':main()
