#!/usr/bin/env python3
"""Verify KFQPC Hafs SVG polygons and derive the page index from the SAME edition.

Do not compare the source edition's per-page ayahs with CTAN's pagination: these
can differ by one or more ayahs, even when both Quran verse texts are correct.
Instead require every visual page to contain contiguous, valid verse IDs, then
verify global ordering and full coverage of all 6,236 ayahs. Never invent a verse
or alter an SVG path.
"""
import argparse
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

PAGES = 604
VERSES = 6236
SVG_NS = '{http://www.w3.org/2000/svg}'
SOURCE_COMMIT = 'b4155f07e4aea087d2c458069acff9f7c7e749f6'
QURAN_SOURCE = 'window.QURAN_DATA='


def source_data(file):
    raw = Path(file).read_text(encoding='utf-8')
    return json.loads(raw.split(QURAN_SOURCE, 1)[1].strip().rstrip(';'))


def verse_lookup(data):
    assert len(data['verses']) == VERSES
    lookup = {}
    for i, verse in enumerate(data['verses'], start=1):
        key = (int(verse[0]), int(verse[1]))
        if key in lookup:
            raise ValueError(f'Quran source duplicate verse identifier: {key}')
        lookup[key] = i
    if len(lookup) != VERSES:
        raise ValueError('Quran source must include all verses exactly once')
    return lookup


def scan(page, svgfile, lookup):
    if svgfile.stat().st_size < 20000:
        raise ValueError(f'Page {page}: SVG suspiciously small')
    root = ET.parse(svgfile).getroot()
    if root.tag != SVG_NS + 'svg':
        raise ValueError(f'Page {page}: not SVG content')
    for tag in root.iter():
        local = tag.tag.rsplit('}', 1)[-1]
        if local in ('script', 'foreignObject', 'image', 'iframe'):
            raise ValueError(f'Page {page}: disallowed SVG element {local}')
        if any(k.startswith('on') or k.endswith('}href') for k in tag.attrib):
            raise ValueError(f'Page {page}: executable/external SVG reference found')
    polys = [node for node in root.iter()
             if node.tag == SVG_NS+'path' and 'ayahPolygon' in node.attrib.get('class', '').split()]
    if not polys:
        raise ValueError(f'Page {page}: SVG has no clickable ayah areas')
    indices = set()
    for node in polys:
        key = (int(node.attrib.get('surah', 0)), int(node.attrib.get('ayah', 0)))
        if key not in lookup:
            raise ValueError(f'Page {page}: unknown verse in source SVG: {key}')
        if not node.attrib.get('d'):
            raise ValueError(f'Page {page}: empty polygon: {key}')
        index = lookup[key]
        if index in indices:
            raise ValueError(f'Page {page}: duplicate polygon for {key}')
        indices.add(index)
    start, end = min(indices), max(indices)
    if indices != set(range(start, end+1)):
        missing = sorted(set(range(start, end+1)) - indices)
        raise ValueError(f'Page {page}: noncontiguous Quran verses inside SVG; missing={missing[:8]}')
    return start, end, len(polys)


def audit_all(source, data):
    lookup = verse_lookup(data)
    pages = []
    seen = set()
    polygons = 0
    overlaps = []
    for page in range(1, PAGES+1):
        svg = source/f'{page:03}.svg'
        if not svg.is_file():
            raise FileNotFoundError(f'Missing original Hafs SVG page {page:03}')
        start, end, n = scan(page, svg, lookup)
        # A verse may legitimately be shown across two adjacent printed pages,
        # but no gaps or backwards jumps are allowed.
        if page == 1 and start != 1:
            raise ValueError('Page 001 must begin with Quran verse 1')
        if pages:
            previous_end = pages[-1][1]
            if start > previous_end + 1:
                raise ValueError(f'Page {page}: missing global ayahs {previous_end+1}..{start-1}')
            if end <= previous_end:
                raise ValueError(f'Page {page}: page goes backwards or duplicates previous page')
            if start <= previous_end:
                if previous_end-start+1 > 1:
                    raise ValueError(f'Page {page}: unexpected multiple duplicated ayahs across pages')
                overlaps.append({'previous_page':page-1,'next_page':page,'ayah_index':start})
        pages.append([start,end])
        seen.update(range(start,end+1))
        polygons += n
        if page%100==0:
            print(f'Validated {page}/{PAGES} source pages',flush=True)
    if pages[-1][1] != VERSES or len(seen) != VERSES:
        missing = sorted(set(range(1,VERSES+1))-seen)
        raise ValueError(f'Incomplete SVG ayah coverage: unique={len(seen)}, missing={missing[:8]}')
    return pages, polygons, overlaps


def main():
    pa = argparse.ArgumentParser()
    pa.add_argument('--source', type=Path, required=True)
    pa.add_argument('--output', type=Path, required=True)
    pa.add_argument('--data', type=Path, required=True)
    args = pa.parse_args()
    data = source_data(args.data)
    if len(data['pages']) != PAGES:
        raise ValueError('Expected 604 pages in auxiliary search text data')
    pages, polygons, overlaps = audit_all(args.source, data)
    args.output.mkdir(parents=True, exist_ok=True)
    for p in range(1,PAGES+1):
        src = args.source/f'{p:03}.svg'
        dst = args.output/src.name
        shutil.copyfile(src,dst)
    page_index = {'source_commit':SOURCE_COMMIT,'edition':'hafs/kfqc',
                  'pages':pages,'unique_ayahs':VERSES,'polygons':polygons,
                  'overlaps':overlaps}
    payload = json.dumps(page_index,ensure_ascii=False,separators=(',',':'))
    # Required for app navigation and in-page polygon validation. Generated from
    # the exact SVG files bundled within this APK, not a different edition.
    (args.output/'page-map.js').write_text('window.MUSHAF_PAGE_MAP='+payload+';\n',encoding='utf-8')
    manifest = {'source':'quran-ws/quran-svg','edition':'hafs/kfqc',
                'source_commit':SOURCE_COMMIT,'pages':PAGES,
                'unique_ayahs':VERSES,'ayah_polygons':polygons,
                'boundary_differences_vs_auxiliary_data':sum(
                    1 for i,pair in enumerate(pages) if pair!=data['pages'][i]),
                'overlaps':overlaps,
                'page_map_sha256':hashlib.sha256(payload.encode('utf-8')).hexdigest()}
    (args.output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'OK: {PAGES} original SVG pages, {VERSES} unique verified ayahs, '
          f'{polygons} page-polygons; {manifest["boundary_differences_vs_auxiliary_data"]} '
          'differences in page boundaries accounted for by the original artwork.')

if __name__=='__main__':
    main()
