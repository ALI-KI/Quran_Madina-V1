#!/usr/bin/env python3
"""Independently re-audit staged SVGs and the generated visual page index."""
from pathlib import Path
import hashlib
import json
import sys
sys.path.insert(0,str(Path(__file__).parent))
from prepare_interactive_mushaf import audit_all, source_data, SOURCE_COMMIT

base=Path(__file__).resolve().parent.parent
assets=base/'app/src/main/assets'
pages_folder=assets/'mushaf-svg'
data=source_data(assets/'quran-data.js')
manifest=json.loads((pages_folder/'manifest.json').read_text(encoding='utf-8'))
assert manifest['source_commit']==SOURCE_COMMIT
assert manifest['pages']==604 and manifest['unique_ayahs']==6236
assert len(list(pages_folder.glob('[0-9][0-9][0-9].svg')))==604
pages,polygons,overlaps=audit_all(pages_folder,data)
assert manifest['ayah_polygons']==polygons
assert manifest['overlaps']==overlaps
js=(pages_folder/'page-map.js').read_text(encoding='utf-8').strip()
assert js.startswith('window.MUSHAF_PAGE_MAP=') and js.endswith(';')
raw=js[len('window.MUSHAF_PAGE_MAP='):-1]
index=json.loads(raw)
assert hashlib.sha256(raw.encode('utf-8')).hexdigest()==manifest['page_map_sha256']
assert index['source_commit']==SOURCE_COMMIT
assert index['pages']==pages
assert index['unique_ayahs']==6236
assert index['polygons']==polygons
print(f'VERIFIED: 604 original SVG pages, {len(data["verses"])} Quran ayahs, '
      f'{polygons} interactive verse polygons; navigation uses matching page map')
