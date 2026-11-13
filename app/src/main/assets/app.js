/* Madina Quran development edition — Original quran text preserved from source package.
   Source: https://ctan.org/pkg/quran (LPPL-1.3c-or-later). Visual line layout not yet official KFGQPC vector layout.
   App design and development: Eng. Mahmoud Elgamsy. */
(() => {
'use strict';
const Q=window.QURAN_DATA;
if(!Q || Q.verses.length!==6236 || Q.pages.length!==604) {document.body.textContent='تعذر التحقق من بيانات المصحف.';return;}
const $=id=>document.getElementById(id);
const ar=n=>String(n).replace(/\d/g,c=>'٠١٢٣٤٥٦٧٨٩'[+c]);
const clean=s=>String(s).normalize('NFKD').replace(/[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]/g,'').replace(/[أإآٱ]/g,'ا').replace(/ى/g,'ي').replace(/ؤ/g,'و').replace(/ئ/g,'ي').replace(/ة/g,'ه').toLowerCase().trim();
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const load=(k,d)=>{try{const x=JSON.parse(localStorage.getItem(k));return x===null?d:x}catch(e){return d}};
const save=(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}};
let state=Object.assign({page:2,tab:'mushaf',readerMode:'original',night:false,fontSize:31,playerOpen:false,repeat:'off',speed:1,selected:8,indexType:'surahs',search:''},load('mq_settings_v2',{}));
const RECITERS={
 minshawy:{name:'محمد صديق المنشاوي',dir:'Minshawy_Murattal_128kbps',mode:'ayah'},
 husary:{name:'محمود خليل الحصري',dir:'Husary_128kbps',mode:'ayah'},
 sudais:{name:'عبد الرحمن السديس',dir:'Abdurrahmaan_As-Sudais_192kbps',mode:'ayah'},
 afasy:{name:'مشاري راشد العفاسي',dir:'Alafasy_128kbps',mode:'ayah'},
 ghamdi:{name:'سعد الغامدي',dir:'Ghamadi_40kbps',mode:'ayah'},
 maher:{name:'ماهر المعيقلي',dir:'MaherAlMuaiqly128kbps',mode:'ayah'},
 ali:{name:'علي جابر',dir:'Ali_Jaber_64kbps',mode:'ayah'},
 arkani:{name:'عبد الولي الأركاني',dir:'',mode:'surah',url:'https://cdn.mp3quran.net/audio/abdulwali-arkani/r1/'}
};
if(!RECITERS[state.reciter])state.reciter='minshawy';
state.page=Math.max(1,Math.min(604,+state.page||2));state.fontSize=Math.max(23,Math.min(40,+state.fontSize||31));
let bookmarks=load('mq_bookmarks_v1',{}),visited=load('mq_progress_v1',{});
const quarterStarts=new Map(Q.quarters.map((span,i)=>[span[0]-1,i]));
const quarterName=i=>`بداية الربع ${ar((i%4)+1)} من الحزب ${ar(Math.floor(i/4)+1)}`;
const surahStart=[];let acc=0;for(let i=0;i<114;i++){surahStart.push(acc);acc+=Q.counts[i]}
const audio=new Audio();audio.preload='none';let soundPlaying=false,loading=false;
// Audio controls are intentionally absent while reading; they appear only on a deliberate Listen action.
let audioVisible=false;
let selectionVisible=false;
state.playerOpen=false; // Always begin in compact audio mode, even if an older preview was expanded.
let activeIndex=Math.max(0,Math.min(6235,+state.selected||7));
let toastT=null;
function toast(msg){const el=$('toast');el.textContent=msg;el.hidden=false;clearTimeout(toastT);toastT=setTimeout(()=>el.hidden=true,3500)}
function persist(){save('mq_settings_v2',state)}
function valAt(index){return Q.verses[Math.max(0,Math.min(6235,index))]}
function pageOf(index){let a=0,b=603;while(a<b){let m=(a+b)>>1;if(Q.pages[m][1]<=index)a=m+1;else b=m}return a+1}
function groupOf(index,ranges){let a=0,b=ranges.length-1;while(a<b){let m=(a+b)>>1;if(ranges[m][1]<=index)a=m+1;else b=m}return a+1}
function idFor(v){return v[0]+':'+v[1]}
function nameAt(index){let v=valAt(index);return Q.names[v[0]-1]}
function currentStart(){return Q.pages[state.page-1][0]-1}
function currentSurah(){return valAt(currentStart())[0]}
function trackPage(){let k=new Date().toLocaleDateString('en-CA');(visited[k] ||= []);if(!visited[k].includes(state.page)){visited[k].push(state.page);save('mq_progress_v1',visited)}}
function setPage(n,keepSelected=false){const RECITERS={
 minshawy:{name:'محمد صديق المنشاوي',dir:'Minshawy_Murattal_128kbps',mode:'ayah'},
 husary:{name:'محمود خليل الحصري',dir:'Husary_128kbps',mode:'ayah'},
 sudais:{name:'عبد الرحمن السديس',dir:'Abdurrahmaan_As-Sudais_192kbps',mode:'ayah'},
 afasy:{name:'مشاري راشد العفاسي',dir:'Alafasy_128kbps',mode:'ayah'},
 ghamdi:{name:'سعد الغامدي',dir:'Ghamadi_40kbps',mode:'ayah'},
 maher:{name:'ماهر المعيقلي',dir:'MaherAlMuaiqly128kbps',mode:'ayah'},
 ali:{name:'علي جابر',dir:'Ali_Jaber_64kbps',mode:'ayah'},
 arkani:{name:'عبد الولي الأركاني',dir:'',mode:'surah',url:'https://cdn.mp3quran.net/audio/abdulwali-arkani/r1/'}
};
if(!RECITERS[state.reciter])state.reciter='minshawy';
state.page=Math.max(1,Math.min(604,Number(n)||1));state.tab='mushaf';if(!keepSelected)activeIndex=currentStart();state.selected=activeIndex;persist();document.fonts?.load('26px "Amiri Quran"').then(()=>requestAnimationFrame(fitMushaf)).catch(()=>{});
window.addEventListener('resize',()=>requestAnimationFrame(fitMushaf));
trackPage();render();$('mainArea').scrollTop=0;if(keepSelected)requestAnimationFrame(()=>focusSelected())}
function jumpTo(index){activeIndex=Math.max(0,Math.min(6235,index));setPage(pageOf(activeIndex),true);closeLayers();requestAnimationFrame(()=>focusSelected())}
function setTab(t){state.tab=t;persist();closeLayers();render();$('mainArea').scrollTop=0}
function decorateAyah(i, verse){const key=idFor(verse);const q=quarterStarts.get(i);const pin=q===undefined?'':`<span class="quarter-badge" role="note" title="${quarterName(q)}">۞ <span>ربع الحزب</span></span>`;return `${pin}<span class="ayah-text${(audioVisible||selectionVisible)&&activeIndex===i?' active':''}${bookmarks[key]?' marked':''}" data-verse="${i}" title="${esc(Q.names[verse[0]-1])} ${ar(verse[1])}">${esc(verse[2])}</span><span class="ayah-no" data-digits="${String(verse[1]).length}" data-verse="${i}">${ar(verse[1])}</span> `}
function maybeBismillah(firstV){if(firstV[1]===1&&firstV[0]!==1&&firstV[0]!==9)return '<div class="bismillah">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div>';return ''}
function renderMushaf(){
 if(state.readerMode==='flex')return renderFlex();
 const p=state.page;
 const pageFile=String(p).padStart(3,'0');
 // KFGQPC vector artwork, rendered once during the Android APK build. This is NOT HTML typesetting.
 // Page art is unmodified Quran text and punctuation; UI overlay is entirely separate.
 return `<article class="official-reader" aria-label="صفحة مصحف المدينة ${ar(p)}">
  <div class="official-art-frame" data-action="pageAyahs" role="button" tabindex="0" aria-label="اختر آية من الصفحة ${ar(p)}">
   <img class="official-page-art" alt="الصفحة ${ar(p)} من مصحف المدينة النبوية، رواية حفص" src="mushaf-pages/${pageFile}.webp" loading="eager"
      onerror="this.hidden=true;this.nextElementSibling.hidden=false">
   <div class="official-missing" hidden>لم تُدرج ملفات الصفحات الرسمية في نسخة المعاينة هذه. أُعدَّ المشروع لبناء الصفحات الـ٦٠٤ من النسخة المتجهية للمجمع أثناء بناء APK، ولن نعرض نصًا مُعاد التنسيق بدل المصحف الأصلي.</div>
  </div>
  <button class="official-verse-select" data-action="pageAyahs">اختيار آية للاستماع أو وضع علامة مرجعية <span aria-hidden="true">⌄</span></button>
 </article>`;
}
function openPageAyahs(){
 const [lo,hi]=Q.pages[state.page-1];
 const rows=[];
 for(let i=lo-1;i<hi;i++){
  const v=Q.verses[i],tag=bookmarks[idFor(v)]?'★ ':'';
  rows.push(`<button class="line-item" data-action="chooseVerse" data-arg="${i}"><span class="num">${ar(v[1])}</span><span class="meta"><strong>${tag}سورة ${esc(Q.names[v[0]-1])}</strong><small>${esc(v[2].slice(0,105))}${v[2].length>105?'…':''}</small></span></button>`);
 }
 showLayer(`<div class="drawer-head"><h3>اختر آية من الصفحة ${ar(state.page)}</h3><button class="icon-btn" data-action="close">×</button></div><p class="hint">النص المطبوع لا يُعاد تنسيقه؛ تحديد الآية يتم من القائمة لحين اعتماد إحداثيات كل آية على الصفحة الرسمية.</p><div class="line-list">${rows.join('')}</div>`);
}
function renderFlex(){let sur=currentSurah();let start=surahStart[sur-1],end=start+Q.counts[sur-1];let items=[];
 for(let i=start;i<end;i++){const v=valAt(i);let mark=bookmarks[idFor(v)]?'★':'';const qi=quarterStarts.get(i);const tag=qi===undefined?'':`<span class="quarter-badge" aria-label="${quarterName(qi)}">۞ ${quarterName(qi)}</span>`;items.push(`<button class="line-item" data-verse="${i}"><div class="num">الآية ${ar(v[1])} ${mark}</div>${tag}<div class="result-verse ayah-text ${(audioVisible||selectionVisible)&&activeIndex===i?'active':''}">${esc(v[2])}</div></button>`)}
 return `<section class="content-page flex-reader"><h1 class="title-pill">سورة ${esc(Q.names[sur-1])}</h1>${sur!==1&&sur!==9?'<p class="bismillah">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</p>':''}<div class="line-list">${items.join('')}</div></section>`;
}
function renderIndex(){const t=state.indexType;const tabs=`<div class="tabs"><button data-action="indexType" data-arg="surahs" class="${t==='surahs'?'active':''}">السور</button><button data-action="indexType" data-arg="juz" class="${t==='juz'?'active':''}">الأجزاء</button><button data-action="indexType" data-arg="pages" class="${t==='pages'?'active':''}">الصفحات</button></div>`;
 let rows=[];if(t==='surahs'){for(let s=1;s<=114;s++)rows.push(`<button class="line-item" data-action="surah" data-arg="${s}"><div class="num">${ar(s)}</div><div class="meta"><strong>سورة ${esc(Q.names[s-1])}</strong><small>${ar(Q.counts[s-1])} آية • تبدأ في الصفحة ${ar(pageOf(surahStart[s-1]))}</small></div><span class="chevron">‹</span></button>`)}
 if(t==='juz'){for(let j=0;j<30;j++)rows.push(`<button class="line-item" data-action="gotoGlobal" data-arg="${Q.juz[j][0]-1}"><div class="num">${ar(j+1)}</div><div class="meta"><strong>الجزء ${ar(j+1)}</strong><small>سورة ${esc(nameAt(Q.juz[j][0]-1))} • صفحة ${ar(pageOf(Q.juz[j][0]-1))}</small></div><span class="chevron">‹</span></button>`)}
 if(t==='pages'){for(let p=1;p<=604;p++)rows.push(`<button class="line-item" data-action="page" data-arg="${p}"><div class="num">${ar(p)}</div><div class="meta"><strong>الصفحة ${ar(p)}</strong><small>سورة ${esc(nameAt(Q.pages[p-1][0]-1))}</small></div><span class="chevron">‹</span></button>`)}
 return `<section class="content-page"><h1 class="title-pill">فهرس المصحف</h1>${tabs}<div class="line-list">${rows.join('')}</div></section>`}
function renderBookmarks(){let rows=Object.entries(bookmarks).map(([k,b])=>{let [s,a]=k.split(':').map(Number),idx=surahStart[s-1]+a-1;return {idx,s,a,b}}).sort((a,b)=>b.b.time-a.b.time).map(x=>`<button class="line-item" data-action="gotoGlobal" data-arg="${x.idx}"><span class="num">★</span><span class="meta"><strong>${esc(Q.names[x.s-1])} — الآية ${ar(x.a)}</strong><small>${esc(x.b.type)} • الصفحة ${ar(pageOf(x.idx))}</small><span class="result-verse" style="font-size:17px;line-height:1.5">${esc(Q.verses[x.idx][2].slice(0,85))}…</span></span><span class="chevron">‹</span></button>`);
 return `<section class="content-page"><h1 class="title-pill">علاماتي المرجعية</h1><p class="hint">تُحفظ جميع العلامات على هاتفك، ويمكنك الرجوع لأي آية مباشرةً.</p>${rows.length?`<div class="line-list">${rows.join('')}</div>`:'<div class="progress-card">لم تضف علامات بعد. اضغط على أي آية، واختر «إضافة علامة».</div>'}</section>`}
function renderProgress(){let dates=Object.keys(visited).sort().reverse();let today=new Date().toLocaleDateString('en-CA');let unique=new Set(Object.values(visited).flat());let total=Object.values(visited).reduce((a,b)=>a+b.length,0);
 let datesRows=dates.slice(0,30).map(d=>`<div class="settings-row"><strong>${esc(d)}</strong><span>${ar(visited[d].length)} صفحات</span></div>`).join('');return `<section class="content-page"><h1 class="title-pill">المتابعة والورد اليومي</h1><div class="progress-card"><div class="large-stat">${ar((visited[today]||[]).length)}</div>صفحات زرتها اليوم</div><div class="progress-card"><div class="large-stat">${ar(unique.size)} / ٦٠٤</div>عدد الصفحات المختلفة التي قرأتها في التطبيق</div><p class="hint">المتابعة تسجل الصفحات التي تفتحها، ولا تعد شهادة بإتمام تلاوتها؛ سيتم إضافة تأكيد الورد والختمة في الإصدار التالي.</p><h2 class="section-heading">سجل الأيام</h2>${datesRows||'لم يُسجل نشاط بعد.'}</section>`}
function renderSettings(){return `<section class="content-page"><h1 class="title-pill">الإعدادات</h1><h2 class="section-heading">القراءة</h2><div class="settings-row"><span>وضع القراءة</span><button class="setting-button" data-action="readerMode">${state.readerMode==='original'?'المصحف بالصفحات':'القراءة المرنة'}</button></div><div class="settings-row"><span>المظهر الليلي</span><input type="checkbox" id="nightCheck" ${state.night?'checked':''}></div><div class="settings-row"><span>حجم الخط</span><input id="fontRange" type="range" min="23" max="40" value="${state.fontSize}"></div><div class="settings-row"><span>مصدر التلاوة</span><button class="setting-button" data-action="reciterPicker">${esc(RECITERS[state.reciter].name)} ▾</button></div><div class="settings-row"><span>إدارة التحميلات</span><button class="setting-button" data-action="download">تحميل السورة الحالية</button></div><div class="settings-row"><span>مراجعة المصادر القرآنية</span><span class="badge-soft">قيد التدقيق النهائي</span></div><p class="hint">وضع المصحف الأصلي يعرض صفحات متجهية ثابتة محوّلة للعرض على الهاتف من أرشيف المجمع، دون إعادة توزيع الكلمات. التحديد الموضعي المباشر على الحروف يتطلب خرائط آيات مُراجَعة. الوضع المرن مستقل.</p><h2 class="section-heading">عن التطبيق والمطوّر</h2><div class="contact-card"><div>✦ تصميم وتطوير ✦</div><h2>م. محمود الجمصي</h2><div class="en">Mahmoud Elgamsy</div><a href="tel:+966562284194">🇸🇦 +966 56 228 4194</a><a href="tel:+201017230727">🇪🇬 +20 101 723 0727</a><a href="mailto:mobd3on@gmail.com">✉ mobd3on@gmail.com</a></div><p class="source-info">مصدر نص البحث والقراءة المرنة: حزمة LaTeX Quran للمطوّر Seiied-Mohammad-Javad Razavian بموجب LPPL 1.3c. المصحف الأصلي من ملفات مجمع الملك فهد المتجهية، عبر نسخة مرآة مثبتة الإصدار، وتخضع المطابقة النهائية للمراجعة. مصدر التلاوة المقترح: EveryAyah — ولم تُضمَّن تسجيلات داخل التطبيق؛ يلزم التحقق من شروط استخدامها قبل النشر العام. <br><a href="https://ctan.org/pkg/quran">المصدر البرمجي للقرآن</a></p></section>`}
function applyHeader(){const first=currentStart(),shown=(activeIndex>=first&&activeIndex<Q.pages[state.page-1][1])?activeIndex:first,v=valAt(shown),g=first+1,quarter=groupOf(g,Q.quarters);$('surahTitle').textContent='سُورَةُ '+Q.names[v[0]-1];$('pageFacts').innerHTML=`<span>الجزء ${ar(groupOf(g,Q.juz))}</span><span>الحزب ${ar(Math.ceil(quarter/4))}</span><span>الربع ${ar((quarter-1)%4+1)}</span><span>ص ${ar(state.page)}</span>`;}
// The original mushaf is a single verified page artwork; no CSS/JS reflow is permitted.
function fitMushaf(){}
function focusSelected(){
 const target=$('mainArea').querySelector('.ayah-text.active'),main=$('mainArea');
 if(!target)return;
 if(state.readerMode==='original')return;
 const d=target.getBoundingClientRect().top-main.getBoundingClientRect().top;
 if(d>main.clientHeight*.64||d<0)main.scrollTop+=d-main.clientHeight*.25;
}
function syncAudioPanel(){
 $('audioBar').classList.toggle('collapsed',!state.playerOpen);
 $('audioBar').hidden=!audioVisible;
 $('audioBar').setAttribute('aria-hidden',String(!audioVisible));
 requestAnimationFrame(fitMushaf);
}
function stopAndHideAudio(){
 loading=false;soundPlaying=false;audio.pause();audio.removeAttribute('src');audio.load();
 audioVisible=false;state.playerOpen=false;syncAudioPanel();updateAudioUI();document.querySelectorAll('.ayah-text.active').forEach(e=>e.classList.remove('active'));
}
function render(){document.body.classList.toggle('night',!!state.night);document.documentElement.style.setProperty('--ayahSize',state.fontSize+'px');applyHeader();
 const pages={mushaf:renderMushaf,index:renderIndex,bookmarks:renderBookmarks,progress:renderProgress,settings:renderSettings};$('mainArea').innerHTML=(pages[state.tab]||renderMushaf)();document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('selected',b.dataset.tab===state.tab));syncAudioPanel();updateAudioUI();requestAnimationFrame(fitMushaf)}
function showLayer(html,isVerse=false){$('shade').hidden=false;const el=isVerse?$('verseSheet'):$('drawer');el.innerHTML=html;el.hidden=false}
function closeLayers(){selectionVisible=false;$('shade').hidden=true;$('drawer').hidden=true;$('verseSheet').hidden=true;if(!audioVisible)document.querySelectorAll('.ayah-text.active').forEach(e=>e.classList.remove('active'))}
function openSurahPicker(){
 const list=Q.names.map((name,i)=>`<button class="line-item" data-action="surah" data-arg="${i+1}"><span class="num">${ar(i+1)}</span><span class="meta"><strong>سورة ${esc(name)}</strong><small>${ar(Q.counts[i])} آية · الصفحة ${ar(pageOf(surahStart[i]))}</small></span><span class="chevron">‹</span></button>`).join('');
 showLayer(`<div class="drawer-head"><h3>فهرس السور — ١١٤ سورة</h3><button class="icon-btn" data-action="close">×</button></div><input class="searchfield" id="surahFilter" placeholder="ابحث باسم السورة أو رقمها" autocomplete="off"/><div class="line-list" id="surahPickerList">${list}</div>`);
}
function openMenu(){showLayer(`<div class="drawer-head"><h3>فهرس التطبيق</h3><button class="icon-btn" data-action="close">×</button></div><div class="line-list" style="margin-top:18px"><button class="line-item" data-action="tab" data-arg="mushaf">المصحف</button><button class="line-item" data-action="tab" data-arg="index">الفهرس والأجزاء والأرباع</button><button class="line-item" data-action="tab" data-arg="bookmarks">علاماتي المرجعية</button><button class="line-item" data-action="tab" data-arg="progress">متابعة الورد</button><button class="line-item" data-action="tab" data-arg="settings">الإعدادات وعن المطوّر</button><button class="line-item" data-action="readerMode">التبديل بين وضعي القراءة</button></div>`)}
function searchUI(){showLayer(`<div class="drawer-head"><h3>بحث في القرآن</h3><button class="icon-btn" data-action="close">×</button></div><input id="searchInput" class="searchfield" placeholder="اكتب كلمة أو جملة من القرآن…" autocomplete="off" inputmode="search"/><div id="searchResults" class="line-list"></div>`);setTimeout(()=>$('searchInput')?.focus(),60)}
function updateSearch(q){const result=$('searchResults');if(!result)return;const query=clean(q);if(query.length<2){result.innerHTML='<p class="hint">اكتب حرفين أو أكثر للبحث في القرآن كاملًا دون إنترنت.</p>';return}
 let found=[];for(let i=0;i<6236;i++){if(clean(Q.verses[i][2]).includes(query)){found.push(i);if(found.length>=75)break}}result.innerHTML=`<p class="hint">${found.length===75?'أول ٧٥ نتيجة':ar(found.length)+' نتائج'}</p>`+found.map(i=>{let v=valAt(i);return `<button class="line-item" data-action="gotoGlobal" data-arg="${i}"><span class="meta"><strong>${esc(Q.names[v[0]-1])} • ${ar(v[1])}</strong><span class="result-verse" style="font-size:17px;line-height:1.6">${esc(v[2].slice(0,95))}${v[2].length>95?'…':''}</span></span></button>`}).join('')}
function openVerse(index){selectionVisible=true;activeIndex=index;state.selected=index;persist();let v=valAt(index);let marked=bookmarks[idFor(v)];const html=`<div class="drawer-head"><h3>${esc(Q.names[v[0]-1])} — الآية ${ar(v[1])}</h3><button class="icon-btn" data-action="close">×</button></div><div class="sheet-verse">${esc(v[2])}</div><div class="verse-actions"><button data-action="playSelected">▶ استماع</button><button data-action="bookmarkVerse">${marked?'★ حذف العلامة':'☆ إضافة علامة'}</button><button data-action="copyVerse">نسخ الآية</button><button data-action="markMemorize">علامة حفظ</button><button data-action="markReview">علامة مراجعة</button><button data-action="repeatAyah">تكرار الآية</button></div>`;
 showLayer(html,true);document.querySelectorAll('.ayah-text').forEach(e=>e.classList.toggle('active',Number(e.dataset.verse)===activeIndex))}
function bookmark(type='مرجعية'){const v=valAt(activeIndex),key=idFor(v);if(type==='toggle'&&bookmarks[key]){delete bookmarks[key];toast('تم حذف العلامة')}else{bookmarks[key]={type:type==='toggle'?'مرجعية':type,time:Date.now()};toast('تم حفظ العلامة: '+Q.names[v[0]-1]+' '+ar(v[1]))}save('mq_bookmarks_v1',bookmarks);closeLayers();render()}
function shareCopy(){const v=valAt(activeIndex),s=v[2]+'\n['+Q.names[v[0]-1]+': '+v[1]+']';if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(s).then(()=>toast('تم نسخ الآية')).catch(()=>oldCopy(s))}else oldCopy(s)}
function oldCopy(s){const t=document.createElement('textarea');t.value=s;document.body.appendChild(t);t.select();try{document.execCommand('copy');toast('تم نسخ الآية')}catch(e){toast('تعذر النسخ في هذا المتصفح')}t.remove()}
function audioName(index){const v=valAt(index);return `${String(v[0]).padStart(3,'0')}${String(v[1]).padStart(3,'0')}.mp3`}
function audioUrl(index){
 const rec=RECITERS[state.reciter],v=valAt(index);
 if(rec.mode==='surah')return `${rec.url}${String(v[0]).padStart(3,'0')}.mp3`;
 return `https://everyayah.com/data/${rec.dir}/${audioName(index)}`;
}
function offlineExists(index){
 if(!window.AndroidBridge)return false;
 const v=valAt(index);
 try{return !!window.AndroidBridge.hasAudio(state.reciter,v[0],v[1])}catch(e){return false}
}
function sourceFor(index){
 const rec=RECITERS[state.reciter],v=valAt(index);
 const file=rec.mode==='surah'?`${String(v[0]).padStart(3,'0')}.mp3`:audioName(index);
 return offlineExists(index)?`https://app.local/audio/${state.reciter}/${file}`:audioUrl(index);
}
function openReciterPicker(){
 const rows=Object.entries(RECITERS).map(([key,rec])=>`<button class="line-item" data-action="chooseReciter" data-arg="${key}"><span class="meta"><strong>${state.reciter===key?'✓ ':''}${esc(rec.name)}</strong><small>${rec.mode==='ayah'?'تسجيل آية بآية · تنزيل السورة متاح':'تسجيل السورة كاملة · ليس ملفًا منفصلًا لكل آية'}</small></span></button>`).join('');
 showLayer(`<div class="drawer-head"><h3>اختيار القارئ</h3><button class="icon-btn" data-action="close">×</button></div><div class="line-list">${rows}</div>`);
}
function chooseReciter(key){
 if(!RECITERS[key])return;
 audio.pause();audio.removeAttribute('src');audio.load();soundPlaying=false;
 state.reciter=key;persist();closeLayers();$('reciterButton').firstChild.textContent=RECITERS[key].name+' ';
 updateAudioUI();render();toast('تم اختيار القارئ: '+RECITERS[key].name);
}
function updateAudioUI(){const play=$('playButton');play.textContent=soundPlaying?'Ⅱ':'▶';play.setAttribute('aria-label',soundPlaying?'إيقاف مؤقت':'تشغيل');const v=valAt(activeIndex);$('currentAyahLabel').textContent=Q.names[v[0]-1]+': '+ar(v[1]);$('elapsed').textContent=time(audio.currentTime);$('duration').textContent=time(audio.duration);$('audioSeek').value=(isFinite(audio.duration)&&audio.duration>0)?Math.floor(audio.currentTime/audio.duration*100):0;document.querySelector('[data-action="speed"]').textContent=state.speed+'×';document.querySelector('[data-action="repeat"]').textContent=({off:'بدون تكرار',ayah:'تكرار الآية',surah:'تكرار السورة'}[state.repeat]||'بدون تكرار')}
function time(n){if(!isFinite(n))return '0:00';return `${Math.floor(n/60)}:${String(Math.floor(n%60)).padStart(2,'0')}`}
async function playIndex(index){if(RECITERS[state.reciter].mode==='surah'&&valAt(index)[1]>1)toast('تلاوة عبد الولي الأركاني متاحة بالسورة كاملة، وسيبدأ التشغيل من أول السورة');audioVisible=true;syncAudioPanel();activeIndex=Math.max(0,Math.min(6235,index));state.selected=activeIndex;persist();loading=true;audio.pause();audio.src=sourceFor(activeIndex);audio.playbackRate=state.speed;audio.load();try{await audio.play();soundPlaying=true;loading=false;updateAudioUI();if(state.tab==='mushaf'&&state.readerMode==='original'&&pageOf(activeIndex)!==state.page)setPage(pageOf(activeIndex),true);else if(state.tab==='mushaf')render()}catch(e){soundPlaying=false;loading=false;updateAudioUI();toast('تعذر تشغيل التلاوة. تحقق من الإنترنت أو حمّل السورة داخل تطبيق أندرويد.')}}
function togglePlay(){audioVisible=true;syncAudioPanel();if(!audio.src||audio.readyState===0){playIndex(activeIndex);return}if(soundPlaying){audio.pause();soundPlaying=false;updateAudioUI()}else{audio.play().then(()=>{soundPlaying=true;updateAudioUI()}).catch(()=>playIndex(activeIndex))}}
function nextAyah(step=1,play=false){if(RECITERS[state.reciter].mode==='surah'){toast('تسجيل هذا القارئ بالسورة كاملة؛ التنقل بالآيات غير متاح');return;}const i=Math.max(0,Math.min(6235,activeIndex+step));if(play)playIndex(i);else{activeIndex=i;state.selected=i;jumpTo(i)}}
audio.addEventListener('ended',()=>{soundPlaying=false;if(RECITERS[state.reciter].mode==='surah'){stopAndHideAudio();return;}if(state.repeat==='ayah'){playIndex(activeIndex);return}const v=valAt(activeIndex),next=activeIndex+1;if(next>=6236 || (state.repeat==='off'&&next>=surahStart[v[0]-1]+Q.counts[v[0]-1])){if(state.repeat==='surah')playIndex(surahStart[v[0]-1]);else {audioVisible=false;syncAudioPanel();updateAudioUI()}return}playIndex(next)});
audio.addEventListener('timeupdate',updateAudioUI);audio.addEventListener('error',()=>{soundPlaying=false;updateAudioUI();if(loading)toast('الرابط الصوتي غير متاح حاليًا')});
function downloadSurah(){const s=valAt(activeIndex)[0];if(window.AndroidBridge?.downloadSurah){window.AndroidBridge.downloadSurah(state.reciter,s);toast('بدأ تنزيل سورة '+Q.names[s-1]+' للاستماع بدون نت')}else toast('تنزيل التلاوات متاح من داخل تطبيق أندرويد؛ هذه معاينة تعمل دون تثبيت')}
window.onNativeDownloadProgress=(reciter,s,done,total)=>{toast('تنزيل سورة '+Q.names[s-1]+': '+ar(done)+' / '+ar(total)+' آية')};
window.onNativeDownloadCompleted=(reciter,s,fail)=>{toast(fail?'اكتمل التنزيل مع وجود '+ar(fail)+' ملفات غير متاحة':'اكتمل تنزيل سورة '+Q.names[s-1]+' بدون إنترنت')};
function handleAction(a,arg){switch(a){case'menu':openMenu();break;case'pageAyahs':openPageAyahs();break;case'chooseVerse':closeLayers();openVerse(+arg);break;case'reciterPicker':openReciterPicker();break;case'chooseReciter':chooseReciter(arg);break;case'search':searchUI();break;case'close':closeLayers();break;case'index':setTab('index');break;case'surahPicker':openSurahPicker();break;case'tab':setTab(arg);break;case'page':setPage(arg);break;case'surah':jumpTo(surahStart[+arg-1]);break;case'gotoGlobal':jumpTo(+arg);break;case'indexType':state.indexType=arg;render();break;case'prevPage':setPage(state.page-1);break;case'nextPage':setPage(state.page+1);break;case'quickBookmark':activeIndex=currentStart();bookmark('toggle');break;case'bookmarkVerse':bookmark('toggle');break;case'markMemorize':bookmark('حفظ');break;case'markReview':bookmark('مراجعة');break;case'copyVerse':shareCopy();break;case'playSelected':closeLayers();playIndex(activeIndex);break;case'repeatAyah':state.repeat='ayah';persist();closeLayers();playIndex(activeIndex);break;case'playAudio':togglePlay();break;case'prevAyah':nextAyah(-1,true);break;case'nextAyah':nextAyah(1,true);break;case'closePlayer':stopAndHideAudio();break;case'togglePlayer':state.playerOpen=!state.playerOpen;syncAudioPanel();break;case'download':downloadSurah();break;case'speed':state.speed=({1:1.25,1.25:1.5,1.5:0.75,0.75:1})[state.speed]||1;audio.playbackRate=state.speed;persist();updateAudioUI();break;case'repeat':state.repeat=({off:'ayah',ayah:'surah',surah:'off'})[state.repeat];persist();updateAudioUI();break;case'readerMode':state.readerMode=state.readerMode==='original'?'flex':'original';persist();closeLayers();render();break;}}
document.addEventListener('click',e=>{if(e.target.id==='shade'){closeLayers();return}const b=e.target.closest('[data-tab],[data-verse],[data-action]');if(!b)return;if(b.dataset.tab){setTab(b.dataset.tab);return}if(b.hasAttribute('data-verse')){openVerse(+b.dataset.verse);return}if(b.dataset.action)handleAction(b.dataset.action,b.dataset.arg)});
document.addEventListener('input',e=>{if(e.target.id==='searchInput')updateSearch(e.target.value);if(e.target.id==='surahFilter'){const filter=clean(e.target.value);$('surahPickerList')?.querySelectorAll('[data-action=surah]').forEach(b=>{b.hidden=!!filter&&!clean(b.textContent).includes(filter)&&String(b.dataset.arg)!==filter;});}if(e.target.id==='fontRange'){state.fontSize=Number(e.target.value);persist();document.documentElement.style.setProperty('--ayahSize',state.fontSize+'px')}if(e.target.id==='audioSeek'){if(isFinite(audio.duration)&&audio.duration>0)audio.currentTime=Number(e.target.value)/100*audio.duration}});
document.addEventListener('change',e=>{if(e.target.id==='nightCheck'){state.night=e.target.checked;persist();render()}});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeLayers();if(e.key==='ArrowLeft'&&state.tab==='mushaf'&&!e.target.matches('input'))setPage(state.page+1);if(e.key==='ArrowRight'&&state.tab==='mushaf'&&!e.target.matches('input'))setPage(state.page-1)});
let startX=0;const main=$('mainArea');main.addEventListener('touchstart',e=>{if(e.touches.length===1)startX=e.touches[0].clientX},{passive:true});main.addEventListener('touchend',e=>{if(state.tab!=='mushaf'||state.readerMode!=='original'||e.changedTouches.length!==1)return;let delta=e.changedTouches[0].clientX-startX;if(Math.abs(delta)>85){if(delta>0)setPage(state.page+1);else setPage(state.page-1)}},{passive:true});
document.fonts?.load('26px "Amiri Quran"').then(()=>requestAnimationFrame(fitMushaf)).catch(()=>{});
window.addEventListener('resize',()=>requestAnimationFrame(fitMushaf));
trackPage();render();
})();
