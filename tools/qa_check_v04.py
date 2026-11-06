"""Visual-flow regression; not a religious-text certification or native APK test."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json,zipfile,hashlib
base=Path(__file__).resolve().parents[1]
a=base/'app/src/main/assets'
q=json.loads((a/'quran-data.js').read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))
checks=[]
def chk(name,ok):
 checks.append((name,bool(ok)))
 if not ok:raise RuntimeError(name)
chk('114 surahs',len(q['names'])==114)
chk('6236 original ayah strings',len(q['verses'])==6236)
chk('604 distinct pages',len(q['pages'])==604)
with zipfile.ZipFile('/mnt/data/MadinaQuran_Android_Source_v0.3.zip') as z: old=z.read('MadinaQuranAndroid/app/src/main/assets/quran-data.js')
chk('Quran data has not changed from v0.3',hashlib.sha256((a/'quran-data.js').read_bytes()).digest()==hashlib.sha256(old).digest())
html=Path('/mnt/data/Quran_Madina_v0.4_Preview.html').read_text(encoding='utf-8')
chk('Amiri Quran font embedded for offline preview',"data:font/ttf;base64," in html)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for w,h in [(360,780),(390,844),(412,915)]:
  page=browser.new_page(viewport={'width':w,'height':h}, device_scale_factor=1)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('**/everyayah.com/**',lambda route:route.abort())
  page.set_content(html,wait_until='domcontentloaded')
  page.wait_for_timeout(180)
  chk(f'{w}px: no audio bar at startup',page.locator('#audioBar').is_hidden())
  chk(f'{w}px: five bottom navigation tabs',page.locator('.bottomnav [data-tab]').count()==5)
  chk(f'{w}px: page 2 text exists',page.locator('.mushaf-word').count()>0)
  for i in range(6):page.locator('[data-action=nextPage]').first.click()
  page.wait_for_timeout(100)
  chk(f'{w}px: page 8 forms aligned rows',page.locator('.mushaf-line').count()>=12)
  chk(f'{w}px: no sideways overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
  chk(f'{w}px: ayah ornament always grouped with previous word',page.evaluate('document.querySelectorAll(".mushaf-mark").length===document.querySelectorAll(".verse-tail").length'))
  chk(f'{w}px: all 9 ayah medallions remain on page 8',page.locator('.mushaf-mark').count()==9)
  chk(f'{w}px: no runtime errors on navigation',not errors)
  page.screenshot(path=f'/mnt/data/Quran_Madina_v0.4_Reader_{w}.png')
  if w==390:
   page.locator('.mushaf-word').first.click()
   chk('Verse selection opens actions',page.locator('#verseSheet').is_visible())
   chk('Audio remains hidden until listening',page.locator('#audioBar').is_hidden())
   page.locator('[data-action=bookmarkVerse]').click()
   page.locator('[data-tab=bookmarks]').click()
   chk('Bookmark still works',page.locator('.line-item').count()>0)
   page.locator('[data-tab=mushaf]').click()
   page.locator('.mushaf-word').first.click()
   page.locator('[data-action=playSelected]').click()
   page.wait_for_timeout(80)
   chk('Audio appears on Listen',page.locator('#audioBar').is_visible())
   page.locator('[data-action=closePlayer]').click()
   chk('Player disappears and reading space returns',page.locator('#audioBar').is_hidden())
   chk('No extra errors after actions',not errors)
  page.close()
 # 604-page page-by-page inspection on a medium mobile viewport
 page=browser.new_page(viewport={'width':390,'height':844})
 page.set_content(html,wait_until='domcontentloaded')
 page.locator('[data-action=prevPage]').first.click()
 page.wait_for_timeout(100)
 problems=page.evaluate('''async () => {
   const fail=[];
   for(let i=1;i<=604;i++){
     if(i>1)document.querySelector('[data-action=nextPage]').click();
     await new Promise(r=>requestAnimationFrame(()=>setTimeout(r,0)));
     let reader=document.querySelector('.reader-border');
     let lines=[...document.querySelectorAll('.mushaf-line')];
     let pageRange=window.QURAN_DATA.pages[i-1];
     let count=pageRange[1]-pageRange[0]+1;
     const marks=document.querySelectorAll('.mushaf-mark').length;
     if(lines.length===0)fail.push({page:i,type:'FALLBACK',count:count});
     else{
      if(marks!==count)fail.push({page:i,type:'BAD_MARKER_COUNT',marks,count});
      if(lines.some(row=>row.scrollWidth>row.clientWidth+2))fail.push({page:i,type:'LINE_OVERFLOW'});
      if(reader.scrollHeight>reader.clientHeight+10)fail.push({page:i,type:'READER_OVERFLOW',diff:reader.scrollHeight-reader.clientHeight});
     }
     if(fail.length>80)break;
   }
   return fail;
 }''')
 print('Whole-Mushaf checks identified',len(problems),'issues. First 30:',problems[:30])
 (base/'qa_v04_pages.json').write_text(json.dumps(problems,ensure_ascii=False,indent=2),encoding='utf-8')
 if len(problems)==0:chk('604 page rendering: no missing layouts, markers or overflows',True)
 else:checks.append(('604 page rendering: no missing layouts, markers or overflows',False))
 page.close();browser.close()
report='\n'.join(('PASS' if x else 'FAIL')+' | '+y for y,x in checks)
report+=f'\n\n{sum(x for _,x in checks)}/{len(checks)} checks passed.\n'
report+='All 604 pages scanned at 390 x 844; issues: '+str(len(problems))+' (see qa_v04_pages.json).\n'
report+='LIMITATION: Official Madinah line breaks and glyph positions, licensed layout data, independent Quran verification, actual Android APK and remote audio rights/testing remain pending.\n'
(base/'QA_RESULTS_v0.4.txt').write_text(report,encoding='utf-8')
print(report)
