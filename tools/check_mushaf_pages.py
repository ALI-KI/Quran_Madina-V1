#!/usr/bin/env python3
"""Fast package integrity check; stops APK creation if 604 authentic page assets are absent."""
from pathlib import Path
import json
import sys
root=Path('app/src/main/assets/mushaf-pages')
manifest=root/'manifest.json'
if not manifest.is_file(): sys.exit('ERROR: Original fixed-layout mushaf assets missing; run prepare_mushaf_pages.py first.')
d=json.loads(manifest.read_text())
if len(d.get('pages',[]))!=604 or d.get('page_count')!=604:sys.exit('ERROR: manifest does not contain exactly 604 pages')
for i in range(1,605):
    p=root/f'{i:03}.webp'
    if not p.exists() or p.stat().st_size<4000:sys.exit(f'ERROR: page {i:03} missing or corrupt')
print('OK: 604 fixed-layout pages present')
