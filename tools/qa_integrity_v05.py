"""Offline Quran DATA integrity checks for CI. These do not certify the printed Mushaf."""
from pathlib import Path
import json, hashlib
root=Path(__file__).resolve().parents[1]
a=root/'app/src/main/assets'
corpus=a/'quran-data.js'
data=json.loads(corpus.read_text(encoding='utf8').split('window.QURAN_DATA=',1)[1].strip().rstrip(';'))
assert len(data['names'])==114,'Expected 114 surahs'
assert len(data['verses'])==6236,'Expected 6236 verses'
assert len(data['pages'])==604,'Expected 604 page ranges'
assert len(data['quarters'])==240,'Expected 240 quarter ranges'
assert len(data['juz'])==30,'Expected 30 juz ranges'
assert sum(data['counts'])==len(data['verses'])
assert len(data['counts'])==114
assert sum(data['counts'])==6236
verses=data['verses']
for surah in range(1,115):
    ayat=[v for v in verses if v[0]==surah]
    assert len(ayat)==data['counts'][surah-1]
    assert [a[1] for a in ayat]==list(range(1,len(ayat)+1)),f'Bad ayah order in surah {surah}'
    assert all(isinstance(v[2],str) and v[2].strip() for v in ayat)
for label,groups in [('pages',data['pages']),('quarters',data['quarters']),('juz',data['juz'])]:
    previous=0
    for i,(start,stop) in enumerate(groups,1):
        assert start==previous+1,(label,i,'discontinuous')
        assert stop>=start,(label,i,'invalid span')
        previous=stop
    assert previous==6236,(label,'incomplete')
checksum=hashlib.sha256(corpus.read_bytes()).hexdigest()
assert checksum=='43ab605249e943056c38d30f6888b7bae39ec176212e359522386e6b6e204bd7','Quran text has changed from reviewed v0.4 input'
assert (root/'.github/workflows/build-apk.yml').exists()
assert (root/'app/src/main/res/mipmap-xxxhdpi/ic_launcher.png').exists()
print('OK: 114 surahs, 6236 verses, 604 pages, 240 quarter ranges, 30 juz, immutable data SHA256',checksum)
print('NOT A CERTIFICATION: full official Mushaf glyph/line-layout and recitation pairing remain to be verified.')
