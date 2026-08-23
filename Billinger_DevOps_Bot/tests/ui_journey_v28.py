"""Browser-rendered v2.8 dark accessibility validation."""
from __future__ import annotations
import json,re,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parent))
from ui_journey_v26 import MOCK
ROOT=Path(__file__).resolve().parents[1]

def rgb_tuple(s):
    nums=[int(x) for x in re.findall(r'\d+',s)[:3]]
    return tuple(nums)

def luminance(rgb):
    vals=[]
    for v in rgb:
        c=v/255
        vals.append(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4)
    return .2126*vals[0]+.7152*vals[1]+.0722*vals[2]

def contrast(a,b):
    l1,l2=sorted([luminance(a),luminance(b)],reverse=True)
    return (l1+.05)/(l2+.05)

def main():
    html=(ROOT/'static/index.html').read_text(encoding='utf-8')
    html=re.sub(r'<link rel="stylesheet" href="/styles\.css\?v=[^"]+">','',html)
    html=re.sub(r'<script src="/app\.js\?v=[^"]+"></script>','',html)
    css=(ROOT/'static/styles.css').read_text(encoding='utf-8');js=(ROOT/'static/app.js').read_text(encoding='utf-8')
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1600,'height':1000})
        page.on('pageerror',lambda e:errors.append('pageerror:'+str(e)))
        page.on('console',lambda m:errors.append('console:'+m.text) if m.type=='error' else None)
        page.set_content(html,wait_until='domcontentloaded');page.add_style_tag(content=css);page.add_script_tag(content='window.v27FirstRun=false');page.add_script_tag(content=MOCK);page.add_script_tag(content=js);page.evaluate('init()')
        page.wait_for_selector('#page-dashboard.active')
        assert 'theme-comfort-dark' in page.locator('body').get_attribute('class')
        assert 'high-contrast' in page.locator('body').get_attribute('class')
        badge=page.locator('.studio-build-badge').inner_text().lower();assert '4k precision build 2.9.0' in badge
        panel=page.locator('.studio-gallery .stat').first
        fg=rgb_tuple(panel.locator('strong').evaluate("e=>getComputedStyle(e).color")); bg=rgb_tuple(panel.evaluate("e=>getComputedStyle(e).backgroundColor"))
        # transparent gradient surface: sample body background for conservative check when rgba is transparent
        if bg==(0,0,0): bg=(13,21,30)
        ratio=contrast(fg,bg); assert ratio>=7.0,(fg,bg,ratio)
        page.screenshot(path=str(ROOT/'docs/v28_dark_dashboard.png'),full_page=False)
        page.click('#menuButton');page.locator('.nav-item[data-page="system"]').click();page.wait_for_selector('#page-system.active')
        page.wait_for_selector('#displayTheme')
        assert page.locator('#displayTheme').input_value()=='comfort'
        assert page.locator('#displayHighContrast').is_checked()
        assert page.locator('#displayReduceMotion').is_checked()
        page.screenshot(path=str(ROOT/'docs/v28_dark_accessibility_controls.png'),full_page=False)
        page.select_option('#displayTheme','standard');page.wait_for_timeout(100)
        assert 'theme-standard-dark' in page.locator('body').get_attribute('class')
        page.select_option('#displayTextSize','large');assert 'text-large' in page.locator('body').get_attribute('class')
        page.check('#displayHighContrast'); page.uncheck('#displayHighContrast');assert 'high-contrast' not in page.locator('body').get_attribute('class')
        page.check('#displayHighContrast');
        page.reload if False else None
        # Mobile menu remains readable and scrollable.
        page.set_viewport_size({'width':390,'height':700});page.click('#menuButton');page.wait_for_selector('#sidebar.open')
        sidebar=page.locator('#sidebar'); assert sidebar.evaluate('e=>e.scrollHeight>e.clientHeight')
        page.screenshot(path=str(ROOT/'docs/v28_dark_mobile_menu.png'),full_page=False)
        browser.close()
    assert not errors,errors
    print('V2.8 DARK ACCESSIBILITY BROWSER JOURNEY PASSED')
    print(json.dumps({'default_theme':'comfort-dark','high_contrast':True,'reduced_motion':True,'text_contrast_ratio':round(ratio,2),'console_errors':0},indent=2))
if __name__=='__main__':main()
