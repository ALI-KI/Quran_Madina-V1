#!/usr/bin/env python3
"""Local synthetic SVG contract test; NOT part of Quran art or shipped pages."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import tempfile

base=Path(__file__).resolve().parent.parent
assets=base/'app/src/main/assets'
html=(assets/'index.html').read_text()
html=html.replace('<link rel="stylesheet" href="style.css">','<style>'+(assets/'style.css').read_text()+'</style>')
fixture='<svg xmlns="http://www.w3.org/2000/svg" width="345" height="550" viewBox="0 0 345 550"><rect width="345" height="550" fill="#fff7e8"/>'
for i in range(9):
    fixture+=f'<path class="ayahPolygon" surah="2" ayah="{49+i}" fill-opacity="0" d="M0 {60*i}H345V{60*(i+1)}H0Z"/>'
fixture+=('<path d="M0 0 L1 1 L2 2 Z"/>'*850)+'</svg>'
html=html.replace('<script src="quran-data.js"></script><script src="app.js"></script>',
   '<script>'+(assets/'quran-data.js').read_text()+'</script>'+f'<script>window.fetch=async()=>({{ok:true,status:200,text:async()=>{fixture!r}}});</script>'+ '<script>'+(assets/'app.js').read_text()+'</script>')
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    for width,height in [(360,780),(390,844),(412,915)]:
        page=browser.new_page(viewport={'width':width,'height':height})
        errors=[]
        page.on('pageerror',lambda err:errors.append(str(err)))
        page.goto('about:blank')
        page.set_content(html)
        for _ in range(6):page.locator('[data-action="nextPage"]').click()
        page.wait_for_timeout(180)
        assert page.locator('path.ayahPolygon').count()==9,'not all interactive polygons loaded'
        assert not page.locator('.official-verse-select').count(),'old verse-list button still occupies page'
        assert not errors,errors
        target=page.locator('path.ayahPolygon[data-verse="55"]')
        assert target.count()==1
        target.click(force=True,position={'x':4,'y':4})
        assert page.locator('#verseSheet').is_visible(),'tapping polygon did not open chosen ayah'
        assert '٤٩' in page.locator('#verseSheet').inner_text(),'wrong ayah selected'
        assert page.locator('path.ayah-selected').count()==1,'ayah highlight missing'
        assert not errors,errors
        print('PASS: '+str(width)+'×'+str(height)+' direct ayah touch and highlight with synthetic polygon coordinates')
        page.close()
    browser.close()
print('Synthetic SVG test only; original Mushaf artwork and all 604 maps require GitHub Actions validation.')
