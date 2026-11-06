import json,re,pathlib,hashlib
from playwright.sync_api import sync_playwright
root=pathlib.Path(__file__).resolve().parents[1]
source=(root/'app/src/main/assets/quran-data.js').read_text()
data=json.loads(source.split('window.QURAN_DATA=',1)[1].strip().rstrip(';'))
checks=[]
def ok(name,cond):checks.append((name,bool(cond)));assert cond,name
ok('6236 verses',len(data['verses'])==6236)
ok('114 surahs',len(data['counts'])==len(data['names'])==114)
ok('604 pages',len(data['pages'])==604)
ok('30 juz',len(data['juz'])==30)
ok('240 quarter sections',len(data['quarters'])==240)
ok('correct total surah verse counts',sum(data['counts'])==6236)
for k in ['pages','juz','quarters']:
 seq=data[k]
 ok(k+' starts at first ayah and ends at last',seq[0][0]==1 and seq[-1][1]==6236)
 ok(k+' segments contiguous',all(seq[i][1]+1==seq[i+1][0] for i in range(len(seq)-1)))
start=0
for si,count in enumerate(data['counts']):
 for i in range(count):
  verse=data['verses'][start+i]
  okcond=(verse[0]==si+1 and verse[1]==i+1 and bool(verse[2]))
  if not okcond:raise AssertionError((si,i,verse))
 start+=count
checks.append(('verse IDs correct across all surahs',True))
html=pathlib.Path('/mnt/data/Quran_Madina_Preview.html').read_text()
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':412,'height':915})
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(html);page.wait_for_timeout(200)
 ok('first render 5 verses page 2',page.locator('.ayah-text').count()==5)
 ok('ornamental border preserved',page.locator('.mushaf-edge').count()==2)
 ok('5 bottom tabs preserved',page.locator('[data-tab]').count()==5)
 page.locator('[data-action="nextPage"]').click()
 ok('next page works',page.locator('.page-number').inner_text().strip()=='٣')
 page.locator('[data-action="prevPage"]').click()
 ok('previous page works',page.locator('.page-number').inner_text().strip()=='٢')
 page.locator('[data-action="search"]').click()
 page.locator('#searchInput').fill('الرحمن')
 ok('search results appear',page.locator('#searchResults [data-action="gotoGlobal"]').count()>=10)
 page.locator('#drawer [data-action="close"]').click()
 page.locator('.ayah-text').first.click()
 ok('verse actions open',page.locator('#verseSheet').is_visible())
 page.locator('[data-action="bookmarkVerse"]').click()
 page.locator('[data-tab="bookmarks"]').click()
 ok('bookmark appears',page.locator('.content-page .line-item').count()==1)
 page.locator('[data-tab="settings"]').click()
 ok('developer credit present', 'Mahmoud Elgamsy' in page.locator('.contact-card').inner_text())
 ok('contact numbers present', '+966 56 228 4194' in page.locator('.contact-card').inner_text() and '+20 101 723 0727' in page.locator('.contact-card').inner_text())
 ok('no uncaught JS errors',not errors)
 browser.close()
report='\n'.join(('[PASS] ' if v else '[FAIL] ')+n for n,v in checks)
(root/'QA_RESULTS.txt').write_text('Initial static data and browser UI test (not Android APK test)\n'+report+'\n\nTOTAL: '+str(len(checks))+' checks passed\n\nSHA256 of Quran data: '+hashlib.sha256((root/'app/src/main/assets/quran-data.js').read_bytes()).hexdigest()+'\n')
print(report+'\nTOTAL '+str(len(checks))+' passed.')
