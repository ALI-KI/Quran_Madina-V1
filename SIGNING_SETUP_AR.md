# تثبيت مفتاح توقيع التطبيق — خطوة إلزامية لمرة واحدة

**المشروع:** مصحف المدينة الذكي — `com.mahmoudelgamsy.madinaquran`  
**تصميم وتطوير:** م. محمود الجمصي — Mahmoud Elgamsy

## أولًا: هل سبق توزيع أي APK على مستخدمين؟

- لو تم تثبيت APK صادر من `assembleDebug` على الأجهزة، فمفتاح Debug الأصلي الذي وقّع **هذا APK نفسه** هو المطلوب للتحديث المباشر. مفتاح Debug الذي يولده GitHub runner غالبًا مؤقت ويضيع بعد نهاية التشغيل؛ وبدون النسخة الأصلية منه لا يمكن إنشاء APK جديد يحدّث النسخة القديمة مع الاحتفاظ بالبيانات. لا يمكن استخراج المفتاح الخاص من APK.
- لو سبق أنشأت مفتاح إصدار Release أو Upload Key صالحًا للتوزيع خارج Google Play، **استخدمه كما هو ولا تنشئ مفتاحًا جديدًا**.
- لو لم توزع أي نسخة بعد، يمكنك إنشاء مفتاح Release واحد على جهازك الشخصي، ثم احتفظ به ونسخة احتياطية آمنة منه مدى عمر التطبيق.
- إذا نُشر التطبيق عبر **Google Play App Signing**، فمفتاح توقيع نسخ المستخدمين تديره Google ومفتاح Upload مختلف؛ اتبع تعليمات Play Console لتحديث التطبيق عبر المتجر.

## إنشاء مفتاح لمرة واحدة فقط (إذا لم يوجد أي مفتاح قديم مستخدم)

على كمبيوتر فيه JDK/Android Studio افتح Terminal أو PowerShell في مجلد خاص خارج مستودع GitHub:

```powershell
keytool -genkeypair -v -keystore madina-release.jks -storetype PKCS12 -alias madina-quran -keyalg RSA -keysize 3072 -validity 12000
```

سيطلب كلمة مرور وبيانات الشهادة. حافظ على نفس الكلمة والمفتاح في كل الإصدارات. لا تضع الملف أو كلماته في المستودع أو في محادثات عامة. احتفظ بنسختين احتياطيتين مشفرتين، واحفظ كلمة المرور في مدير كلمات مرور.

## تجهيز Secrets في GitHub

داخل المستودع افتح: **Settings → Secrets and variables → Actions → Repository secrets** ثم أضف أربعة Secrets:

- `QURAN_KEYSTORE_BASE64`: ملف `.jks` الأصلي بعد تحويله إلى Base64 (كامل المحتوى وليس اسم الملف)
- `QURAN_STORE_PASSWORD`: كلمة مرور مخزن المفاتيح
- `QURAN_KEY_ALIAS`: اسم المفتاح داخل الملف، مثل `madina-quran`
- `QURAN_KEY_PASSWORD`: كلمة مرور المفتاح (غالبًا نفس كلمة مرور مخزن المفاتيح عند استخدام PKCS12)

في Windows PowerShell (من مكان ملف `.jks`):

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes((Resolve-Path '.\madina-release.jks'))) | Set-Clipboard
```

يتم نسخ Base64 للحافظة؛ الصقه مباشرة في Secret باسم `QURAN_KEYSTORE_BASE64` ولا تحفظه في ملف بالمستودع. نظّف الحافظة بعد ذلك إن أمكن.

## تثبيت بصمة توقيع ثابتة لمنع تغيير المفتاح دون الانتباه

اعرض البصمة العامة (لا تكشف كلمة المرور):

```powershell
keytool -list -v -keystore madina-release.jks -alias madina-quran
```

ابحث عن `SHA256:` ضمن **Certificate fingerprints** وانسخ البصمة المكونة من 64 رمزًا سداسيًا (يمكن تضمين `:` بين الأزواج). ثم ادخل:

**Settings → Secrets and variables → Actions → Variables → New repository variable**

واكتب اسم المتغير: `QURAN_SIGNING_CERT_SHA256`، وقيمته بصمة SHA256 للشهادة نفسها. هذا **ليس سرًا**؛ استخدامه يوقف أي بناء بمفتاح مختلف، حتى لو تغيرت قيمة Secret بالخطأ.

إذا عندك APK مثبت/موزع سابقًا، افحص شهادة **ملف APK القديم** باستخدام `apksigner verify --print-certs old.apk`، وقارن بصمتها مع بصمة JKS الذي تنوي استعماله. عدم التطابق يعني أن APK الجديد لن يحدّث التطبيق القديم مباشرة (خارج نظام ترحيل مفاتيح معتمد/Google Play).

## البناء والتحديث

1. ارفع محتويات هذا المشروع **كاملة** إلى جذر المستودع؛ لا ترفع `.jks` أو كلمات المرور.
2. في **Actions → Build Quran Android signed APK → Run workflow** شغل البناء.
3. عند النجاح نزّل `MadinaQuran-signed-release-APK` من **Artifacts**، وستجد `app-release.apk` بعد فك ZIP.
4. كل تشغيل جديد على نفس Workflow يزيد `versionCode` تلقائيًا. قيمة `applicationId` تبقى ثابتة، ويُراجع توقيع الـAPK مع البصمة المعتمدة قبل رفعه.
5. لا تغير ملف JKS أو alias أو شهادة التوقيع في إصدارات التطبيق المقبلة.

**مهم:** مجرد إكمال GitHub Actions لا يثبت دقة صفحات القرآن أو تلاواته؛ هذه مسألة اعتماد منفصلة قبل النشر العام.
