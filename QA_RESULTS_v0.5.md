# QA — Madina Quran v0.5

Date: 2026-11-06

## Source integrity

**PASS:** 114 surahs, 6236 verses, 604 sequential page ranges, 240 sequential quarter ranges, 30 juz, contiguous ayah numbering, no blank verses, preserved source-data SHA-256. This tests integrity and structure **not correctness against an independently authenticated Quran edition**.

## Full 604-page visual/DOM scan at 390×844

**PASS:** 604/604 pages showed the fitted reading layout (page 1 checked individually; remaining 603 checked sequentially), no clipped lines or horizontal line overflow, exact expected decorated verse-marker count and quarter-start count per page, no JavaScript runtime errors. 240 quarter markers across the entire Quran.

## Representative test across smaller and larger phones

**PASS:** 24/24 checks (pages 2, 6, 19, 30, 37, 163, 580 and 604 at 360×780, 390×844 and 412×915). No overflow, no missing bottom navigation tabs, fitted page rendering.

## Native Android

**NOT YET TESTED:** Android APK compilation on GitHub Actions and Android status-bar hiding on a physical phone. Kotlin code and theme were updated, but build logs are required to confirm compilation.

## High-priority limitations

- Word break positions and the exact number/placement of printed Madinah Mushaf lines have **not** been certified against an authorized source. This is a screen-fitting engine for development.
- Reciter API URLs and downloaded audio not verified on hardware; redistribution terms pending.
- Night UI visually reviewed in a Chromium mobile viewport, not on each Android vendor skin.
- Font availability depends on the device. No font file is redistributed in this package.

## Developer identity

م. محمود الجمصي / Mahmoud Elgamsy — +966 56 228 4194 / +20 101 723 0727 — mobd3on@gmail.com
