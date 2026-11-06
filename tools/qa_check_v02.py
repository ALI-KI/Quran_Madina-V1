"""Development sanity checks for v0.2 preview. Not a certification of the Quran text or APK."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, hashlib
root=Path(__file__).resolve().parents[1]
a=root/'app/src/main/assets'
html=Path('/mnt/data/Quran_Madina_Updated_Preview.html').read_text(encoding='utf-8')
data=json.loads((a/'quran-data.js').read_text(encoding='utf-8').split('window.QURAN_DATA=',1)[1].strip().rstrip(';'))
checks=[]
def ok(name,condition):
 checks.append((name, bool(condition)))
 if not condition: raise AssertionError(name)
ok('All 114 surah names included',len(data['names'])==114 and data['names'][11]=='يوسف')
ok('6236 verses included',len(data['verses'])==6236)
ok('604 page data ranges included',len(data['pages'])==604)
ok('Quran text included in static HTML fallback', 'ذَٰلِكَ' in html and '<main class="main-area"' in html)
ok('Approved ornamental strips embedded in preview','data:image/png;base64,' in html)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for w,h in [(360,780),(390,844),(412,915)]:
  page=browser.new_page(viewport={'width':w,'height':h},device_scale_factor=1)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html);page.wait_for_timeout(200)
  ok(f'Page 2 has 5 verse units on {w}px screen',page.locator('.ayah-text').count()==5)
  ok(f'Original page fits vertical screen {w}px',page.evaluate('''() => {const m=document.querySelector('.main-area');return m.scrollHeight<=m.clientHeight+2;}'''))
  ok(f'Bottom tabs present on {w}px screen',page.locator('nav [data-tab]').count()==5)
  ok(f'No JavaScript errors on {w}px screen',not errors)
  if w==412:
   page.screenshot(path='/mnt/data/Quran_Madina_v0.2_Reader.png')
   page.locator('#surahTitle').click();page.wait_for_timeout(80)
   ok('Surah picker shows all 114 surahs',page.locator('#surahPickerList [data-action=surah]').count()==114)
   page.screenshot(path='/mnt/data/Quran_Madina_v0.2_Surah_List.png')
   page.locator('#surahFilter').fill('يوسف')
   ok('Surah picker filters by surah name',page.locator('#surahPickerList button:visible').count()==1)
   page.locator('#surahPickerList button:visible').first.click();page.wait_for_timeout(80)
   ok('Opening Yusuf displays correct surah name','يوسف' in page.locator('#surahTitle').inner_text())
   page.locator('[data-tab=index]').click()
   ok('Index tab lists all 114 surahs',page.locator('.content-page .line-item').count()==114)
   page.screenshot(path='/mnt/data/Quran_Madina_v0.2_Index.png')
   page.locator('.content-page .line-item').nth(1).click()
   page.locator('[data-action=search]').click()
   page.locator('#searchInput').fill('الرحمن')
   ok('Search returns Quran verses',page.locator('#searchResults [data-action=gotoGlobal]').count()>10)
   page.locator('#drawer [data-action=close]').click()
   page.locator('.ayah-text').first.click()
   ok('Verse action menu opens',page.locator('#verseSheet').is_visible())
   page.locator('[data-action=bookmarkVerse]').click()
   page.locator('[data-tab=bookmarks]').click()
   ok('Bookmarked verse saved and visible',page.locator('.content-page .line-item').count()>=1)
   page.locator('[data-tab=settings]').click()
   ok('Developer identity and email in app', 'Mahmoud Elgamsy' in page.locator('.contact-card').inner_text() and 'mobd3on@gmail.com' in page.locator('.contact-card').inner_text())
  page.close()
 browser.close()
report='\n'.join(('[PASS] ' if success else '[FAIL] ')+name for name,success in checks)
report+='\n\nTOTAL: '+str(len(checks))+' browser and data checks passed.\n'
report+='NOT VALIDATED: original official 15-line Madinah page geometry; complete verse text proofing; recitation availability/licensing; Android APK build or on-device playback.\n'
(root/'QA_RESULTS_v0.2.txt').write_text(report,encoding='utf-8')
print(report)
