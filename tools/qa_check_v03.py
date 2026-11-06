"""Functional browser checks for UI v0.3 — NOT an official Quran-text proofing or native Android test."""
from playwright.sync_api import sync_playwright
from pathlib import Path
from zipfile import ZipFile
import json,hashlib
root=Path(__file__).resolve().parents[1]
a=root/'app/src/main/assets'
html=Path('/mnt/data/Quran_Madina_v0.3_Preview.html').read_text(encoding='utf8')
q=(a/'quran-data.js').read_bytes()
data=json.loads(q.decode('utf8').split('window.QURAN_DATA=',1)[1].strip().rstrip(';'))
checks=[]
def verify(label, passed):
 checks.append((label,bool(passed)))
 if not passed:raise AssertionError(label)
verify('114 surahs are present',len(data['names'])==114)
verify('6236 Quran ayah records are present',len(data['verses'])==6236)
verify('604 numbered page ranges are present',len(data['pages'])==604)
verify('Quran page ranges cover all verses exactly once',data['pages'][0][0]==1 and data['pages'][-1][1]==6236 and all(data['pages'][i-1][1]+1==data['pages'][i][0] for i in range(1,604)))
with ZipFile('/mnt/data/MadinaQuran_Android_Source_v0.2.zip') as z:
 old=z.read('MadinaQuranAndroid/app/src/main/assets/quran-data.js')
verify('Quran source dataset unmodified from previous release',hashlib.sha256(q).digest()==hashlib.sha256(old).digest())
verify('Vector ayah ornaments are embedded inside the offline preview','verse-medallion.svg' not in html and 'data:image/svg+xml;base64,' in html)
verify('Audio is hidden by default in HTML fallback','id="audioBar" hidden' in html)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for w,h in [(360,780),(390,844),(412,915)]:
  page=browser.new_page(viewport={'width':w,'height':h},device_scale_factor=1)
  errors=[]
  page.on('pageerror',lambda err: errors.append(str(err)))
  page.route('**/everyayah.com/**',lambda route:route.abort())
  page.set_content(html,wait_until='domcontentloaded')
  page.wait_for_timeout(180)
  verify(f'{w}px: audio controls absent at launch',page.locator('#audioBar').is_hidden())
  verify(f'{w}px: five footer sections kept',page.locator('nav.bottomnav [data-tab]').count()==5 and page.locator('.bottomnav').is_visible())
  verify(f'{w}px: page-2 shows verse numbers 1–5',page.locator('.page-verse-text .ayah-no').count()==5)
  verify(f'{w}px: side ornament narrower than 18px',page.evaluate('document.querySelector(".mushaf-edge").getBoundingClientRect().width')<18)
  verify(f'{w}px: no horizontal overflow',page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+2'))
  verify(f'{w}px: reader fits vertically on page 2',page.evaluate('document.querySelector(".main-area").scrollHeight <= document.querySelector(".main-area").clientHeight+3'))
  verify(f'{w}px: no javascript runtime errors',not errors)
  if w==390:
   base=page.locator('.main-area').bounding_box()['height']
   page.locator('.ayah-text').first.click()
   verify('Verse selection opens action sheet',page.locator('#verseSheet').is_visible())
   verify('Selecting an ayah by itself does NOT show audio bar',page.locator('#audioBar').is_hidden())
   page.locator('[data-action=playSelected]').click()
   page.wait_for_timeout(150)
   verify('Explicit Listen action reveals player',page.locator('#audioBar').is_visible())
   verify('Player starts compact',page.locator('#audioBar').evaluate('(x)=>x.classList.contains("collapsed")'))
   verify('Reader height decreases only while listening',page.locator('.main-area').bounding_box()['height']<base)
   page.screenshot(path='/mnt/data/Quran_Madina_v0.3_Audio.png')
   page.locator('.audio-bar .reciter').click()
   verify('Reciter name expands advanced audio controls',page.locator('#playerExpanded').is_visible())
   page.locator('.audio-bar .reciter').click()
   verify('Reciter name collapses advanced audio controls',page.locator('#playerExpanded').is_hidden())
   page.locator('[data-action=closePlayer]').click()
   verify('Close audio button hides the player',page.locator('#audioBar').is_hidden())
   verify('Reading space is fully restored',abs(page.locator('.main-area').bounding_box()['height']-base)<2)
   page.locator('.ayah-text').first.click()
   page.locator('[data-action=bookmarkVerse]').click()
   verify('Bookmark creation does not summon audio player',page.locator('#audioBar').is_hidden())
   page.locator('[data-tab=bookmarks]').click()
   verify('Saved verse exists in bookmarks',page.locator('.content-page .line-item').count()>0)
   page.locator('[data-tab=mushaf]').click()
   page.locator('#surahTitle').click()
   verify('Surah selector lists 114 surahs',page.locator('#surahPickerList [data-action=surah]').count()==114)
   page.locator('#surahFilter').fill('يوسف')
   verify('Surah selector filters by surah name',page.locator('#surahPickerList button:visible').count()==1)
   page.locator('#surahPickerList button:visible').first.click()
   verify('Surah navigation opens Yusuf', 'يوسف' in page.locator('#surahTitle').inner_text())
   page.locator('[data-tab=settings]').click()
   verify('Designer identity and contacts preserved', all(x in page.locator('.contact-card').inner_text() for x in ['Mahmoud Elgamsy','mobd3on@gmail.com','+966 56 228 4194','+20 101 723 0727']))
   verify('No JS errors after navigation and controls',not errors)
  page.close()
 browser.close()
report='\n'.join(('PASS' if passed else 'FAIL')+' | '+label for label,passed in checks)
report+='\n\n'+str(len(checks))+' automated source/browser checks passed.'
report+='\nNOT VALIDATED: official Madinah Mushaf 15-line exact layout, Qur\'an text independent proofreading, Android APK compilation, actual offline MP3 playback, audio rights.\n'
(root/'QA_RESULTS_v0.3.txt').write_text(report,encoding='utf8')
print(report)
