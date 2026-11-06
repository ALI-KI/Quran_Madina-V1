import re,json,hashlib,unicodedata,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
source=pathlib.Path('/usr/share/texlive/texmf-dist/tex/latex/quran')
sty=(source/'quran.sty').read_text()
quran=(source/'qurantext-uthmani.def').read_text()
namepart=re.search(r'\\def\\@@surahname\[#1\]\{%(.*?)\\else\\relax\\fi\}',sty,re.S).group(1)
names=[x.strip() for x in namepart.split('\\or')[1:]]
counts=re.search(r'\\def\\qt@getversenum#1\{%\s*\\ifcase#1(.*?)\\else',sty,re.S).group(1)
counts=[int(x.strip()) for x in re.findall(r'\\or\s*(\d+)',counts)]
assert len(names)==len(counts)==114

def ranges(macro):
 s=re.search(r'\\def\\qt@'+macro+r'#1\s*\{[%\s]*\\ifcase#1(.*?)\\else',sty,re.S)
 assert s,macro
 return [tuple(map(int, pair)) for pair in re.findall(r'\\or\s*(\d+)\s*-\s*(\d+)',s.group(1))]
pages=ranges('getpagedomain'); juz=ranges('getjuzdomain'); quarter=ranges('getquarterdomain')
assert len(pages)==604 and len(juz)==30 and len(quarter)==240
assert pages[0]==(1,7) and pages[1]==(8,12) and pages[-1][1]==6236
assert all(pages[i][1]+1==pages[i+1][0] for i in range(603))
assert all(juz[i][1]+1==juz[i+1][0] for i in range(29))
assert all(quarter[i][1]+1==quarter[i+1][0] for i in range(239))
lines=[l for l in quran.splitlines() if l.startswith('\\qt@newcmd\\qurantext@')]
assert len(lines)==6236, len(lines)
verses=[]; si=0; an=0
for line in lines:
 m=re.fullmatch(r'\\qt@newcmd\\qurantext@([a-z]+)\{(.*?)\\qt@no\{﴿([٠-٩]+)﴾\}\}',line)
 if not m: raise Exception('verse parse failed '+line[:120])
 text=m.group(2).strip()
 # Macro inserted by LaTeX before surah opening, not part of verse text.
 text=text.replace('\\basmalah','').replace('\\qt@par','').strip()
 if '\\' in text: print('unknown macro',len(verses)+1,repr(text[:140])); raise Exception('unexpected macro')
 n=int(m.group(3).translate(str.maketrans('٠١٢٣٤٥٦٧٨٩','0123456789')))
 if an>=counts[si]:si+=1;an=0
 an+=1
 assert n==an,(si+1,an,n)
 verses.append([si+1,an,text])
assert si==113 and an==counts[-1]
assert sum(counts)==len(verses)==6236
payload={'name':'Madinah Quran - data from LaTeX quran package 2.3 by Seiied-Mohammad-Javad Razavian', 'source':'https://ctan.org/pkg/quran', 'license':'LPPL-1.3c-or-later', 'names':names, 'counts':counts, 'pages':pages, 'juz':juz, 'quarters':quarter, 'verses':verses}
path=ROOT/'app/src/main/assets/quran-data.js'
raw=json.dumps(payload,ensure_ascii=False,separators=(',',':'))
path.write_text('/* Quran text source: LaTeX quran 2.3 (LPPL 1.3c). Review against authorized Mushaf before publishing. */\nwindow.QURAN_DATA='+raw+';\n')
print('output',path,'size',path.stat().st_size,'sha256',hashlib.sha256(path.read_bytes()).hexdigest());print('first',verses[:9]);print('last',verses[-1]);print('pages',len(pages),'juz',len(juz),'quarters',len(quarter))
