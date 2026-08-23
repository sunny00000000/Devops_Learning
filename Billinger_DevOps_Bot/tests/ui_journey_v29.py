"""Browser-rendered 1080p/1440p/4K precision validation."""
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
def lum(rgb):
    vals=[]
    for v in rgb:
        c=v/255; vals.append(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4)
    return .2126*vals[0]+.7152*vals[1]+.0722*vals[2]
def ratio(a,b):
    hi,lo=sorted([lum(a),lum(b)],reverse=True); return (hi+.05)/(lo+.05)

def render(page,w,h,name):
    page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(120)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 2'), (w,page.evaluate('document.documentElement.scrollWidth'),page.evaluate('innerWidth'))
    page.screenshot(path=str(ROOT/f'docs/{name}.png'),full_page=False)

def main():
    html=(ROOT/'static/index.html').read_text(encoding='utf-8')
    html=re.sub(r'<link rel="stylesheet" href="/styles\.css\?v=[^"]+">','',html)
    html=re.sub(r'<script src="/app\.js\?v=[^"]+"></script>','',html)
    css=(ROOT/'static/styles.css').read_text(encoding='utf-8');js=(ROOT/'static/app.js').read_text(encoding='utf-8')
    errors=[]
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        page=b.new_page(viewport={'width':1920,'height':1080})
        page.on('pageerror',lambda e:errors.append('pageerror:'+str(e)))
        page.on('console',lambda m:errors.append('console:'+m.text) if m.type=='error' else None)
        page.set_content(html,wait_until='domcontentloaded');page.add_style_tag(content=css);page.add_script_tag(content='window.v27FirstRun=false');page.add_script_tag(content=MOCK);page.add_script_tag(content=js);page.evaluate('init()')
        page.wait_for_selector('#page-dashboard.active')
        assert '4k precision build 2.9.0' in page.locator('.studio-build-badge').inner_text().lower()
        panel=page.locator('.studio-gallery .stat').first
        assert panel.evaluate('e=>getComputedStyle(e).backdropFilter') in ('none','')
        assert page.locator('.topbar').evaluate('e=>getComputedStyle(e).backdropFilter') in ('none','')
        fg=rgb_tuple(panel.locator('strong').evaluate('e=>getComputedStyle(e).color'))
        bg=rgb_tuple(panel.evaluate('e=>getComputedStyle(e).backgroundColor'))
        cr=ratio(fg,bg); assert cr>=7,(fg,bg,cr)
        render(page,1920,1080,'v29_precision_1080p')
        render(page,2560,1440,'v29_precision_1440p')
        render(page,3840,2160,'v29_precision_4k')
        # Check bounded reading width and crisp non-transformed exhibit at 4K.
        content_w=page.locator('.content').evaluate('e=>e.getBoundingClientRect().width')
        assert 2500 <= content_w <= 3250,content_w
        transform=page.locator('.ops-console.studio-exhibit').evaluate('e=>getComputedStyle(e).transform')
        assert transform=='none',transform
        b.close()
    assert not errors,errors
    print('V2.9 4K PRECISION BROWSER JOURNEY PASSED')
    print(json.dumps({'contrast_ratio':round(cr,2),'content_width_4k':round(content_w,1),'console_errors':0,'viewports':['1920x1080','2560x1440','3840x2160']},indent=2))
if __name__=='__main__': main()
