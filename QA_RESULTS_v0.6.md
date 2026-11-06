# QA — Quran Madina v0.6

## Scope

**Bug fixed:** Surah names and part labels floated over Quran text, and large blank gaps appeared around surah transitions on pages such as 221, 235, 255 and 267.

## Changes

- Surah headings inside the page use a separate, natural-flow, centered ornamental divider rather than reusing the first page ribbon with negative margins.
- No duplicate juz/part badge within the page body.
- Multi-surah pages use a single unified vertical line budget for all surah sections: no half-page flex allocations for a one-line preceding surah.
- Bismillah follows each surah divider as a distinct, non-overlapping item.
- Neither Quran text nor page/ayah range data was changed; immutable source checksum is checked by CI.

## Automated layout checks

- 604 / 604 pages scanned at viewport 390 × 844, in three uninterrupted groups (1–200, 201–400, 401–604): **zero detected overlapping consecutive rows, zero clipped lines, zero missing numbered verse endings, zero browser JavaScript errors**.
- All 51 pages that contain more than one surah checked at 390 × 844.
- 11 high-risk pages checked at 360 × 780 and 412 × 915: 221, 235, 255, 267, 596, 599, 600, 601, 602, 603, 604.
- Total cross-size surah boundary checks: 73. No overlap detected and all used the fitted mode.
- Sample visual screenshots: QA screenshots directory (pages 221, 235, 255, 267, 604).

## Important limitations

These tests certify neither the script/diacritics against the King Fahd Complex official edition nor the exact printed 15-line layout of the Madinah Mushaf. The line layout is a screen-fitting approximation, not authoritative per-word location. No APK has been built or tested on physical Android hardware in this run; GitHub Actions is provided to make a debug APK.
