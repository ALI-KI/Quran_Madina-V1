#!/usr/bin/env python3
"""Fail the build if the offline SVG mushaf or verse hit maps are incomplete."""
from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).parent))
from prepare_interactive_mushaf import scan,source_data
base=Path(__file__).resolve().parent.parent
pages=base/'app/src/main/assets/mushaf-svg'
data=source_data(base/'app/src/main/assets/quran-data.js')
manifest=json.loads((pages/'manifest.json').read_text())
assert manifest['source_commit']=='b4155f07e4aea087d2c458069acff9f7c7e749f6'
assert manifest['pages']==604 and manifest['ayah_polygons']==6236
assert len(list(pages.glob('[0-9][0-9][0-9].svg')))==604
n=0
for p in range(1,605):n+=scan(p,pages/f'{p:03}.svg',data)
assert n==6236
print('VERIFIED: 604 pages and exactly 6,236 source-mapped verse regions; APK may be built')
