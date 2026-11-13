# v0.8.1 — Validation summary

## Root cause confirmed from the connected GitHub source
- The secondary `quran-data.js` says printed page 120 contains al-Ma'idah 5:71–5:76.
- The pinned original SVG metadata (`hafs/kfqc/json/120.json`) says page 120 has 5:71–5:77.
- The pinned source `121.json` starts with 5:78, so 5:77 is **valid** and should not be silently removed.
- The previous validator incorrectly required a different edition's page boundaries to match.

## Implemented correction
- Validate the actual source SVG polygons against their Quran verse IDs, and require contiguous order within every page.
- Enforce global 1–6236 verse coverage and 604 complete SVG pages (and strictly prevent missing/noncontiguous/unknown polygon IDs).
- Generate `mushaf-svg/page-map.js` from the same source artwork that the APK bundles.
- Load this map before app.js; use it for page navigation, verse selection, and polygon verification in the WebView.
- Update CI cache key so stale contents from v0.8 are not reused.
- Keep applicationId, Gradle signing configuration, JKS restoration and fingerprint checks unchanged.

## Executed checks
- `python -m py_compile` — passed for both updated Python scripts.
- `node --check` — passed for app.js.
- Generated a **synthetic 604-page source fixture** matching the application verse corpus and introducing the known page-120 discrepancy; the full staging/validation pipeline passed.
- Introduced an invalid polygon in the fixture: validation correctly stopped with an exception.

## NOT yet performed
- A full 604-page audit using the actual GitHub SVG contents (will run on GitHub Actions after upload).
- Actual Android Gradle build, signature verification on the new version, or on-device test.
- Independent page-by-page religious/typographical verification for public release.
