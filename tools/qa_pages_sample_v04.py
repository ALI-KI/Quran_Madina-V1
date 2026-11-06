from pathlib import Path
from playwright.sync_api import sync_playwright
import json
html=Path('/mnt/data/Quran_Madina_v0.4_Preview.html').read_text()
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=b.new_page(viewport={'width':390,'height':844});page.set_content(html,wait_until='domcontentloaded')
 results=page.evaluate('''async () => {
 const pages=[1,2,3,8,9,15,35,55,163,300,432,570,602,603,604],fail=[];
 for(const i of pages){
  document.querySelector('[data-tab="index"]').click();
  document.querySelector('[data-action="indexType"][data-arg="pages"]').click();
  document.querySelector(`[data-action="page"][data-arg="${i}"]`).click();
  await new Promise(r=>requestAnimationFrame(()=>setTimeout(r,50)));
  const r=document.querySelector('.reader-border');
  const lines=[...document.querySelectorAll('.mushaf-line')];
  const actualMarks=document.querySelectorAll('.mushaf-mark').length;
  const [a,b]=window.QURAN_DATA.pages[i-1];
  const normal=lines.every(el=>el.scrollWidth<=el.clientWidth+3);
  const noHeightOverflow=r.scrollHeight<=r.clientHeight+6;
  fail.push({page:i,lines:lines.length,expected:b-a+1,markers:actualMarks,normal,noHeightOverflow,
   topbar:document.querySelector('#surahTitle').textContent,readerDiff:r.scrollHeight-r.clientHeight});
 }
 return fail;
}''')
 print(json.dumps(results,ensure_ascii=False,indent=2))
 Path('/mnt/data/MadinaQuranAndroid/QA_PAGE_SAMPLE_v0.4.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
 b.close()
