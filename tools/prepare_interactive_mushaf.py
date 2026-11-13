#!/usr/bin/env python3
"""Stage Hafs/KFQC SVG pages with verified SVG ayah polygons.

Source: quran-ws/quran-svg @ b4155f07e4aea087d2c458069acff9f7c7e749f6.
All page artwork stays immutable; XML is parsed only for validation.
Never generate missing page text or infer hit boxes.
"""
import argparse
from pathlib import Path
import json
import shutil
import xml.etree.ElementTree as ET

PAGES=604
SVG_NS='{http://www.w3.org/2000/svg}'
QURAN_SOURCE='window.QURAN_DATA='

def source_data(file):
    raw=Path(file).read_text(encoding='utf-8')
    return json.loads(raw.split(QURAN_SOURCE, 1)[1].strip().rstrip(';'))

def scan(page, svgfile, data):
    if svgfile.stat().st_size<20000:
        raise ValueError(f'Page {page}: SVG is suspiciously small')
    root=ET.parse(svgfile).getroot()
    if root.tag != SVG_NS+'svg':
        raise ValueError(f'Page {page}: not SVG content')
    # Reject executable or externally-loaded markup. The trusted source should contain only vector paths.
    for tag in root.iter():
        local=tag.tag.rsplit('}',1)[-1]
        if local in ('script','foreignObject','image','iframe'):
            raise ValueError(f'Page {page}: disallowed SVG element {local}')
        if any(k.startswith('on') or k.endswith('}href') for k in tag.attrib):
            raise ValueError(f'Page {page}: SVG includes executable or external references')
    polys=[node for node in root.iter() if node.tag==SVG_NS+'path' and 'ayahPolygon' in node.attrib.get('class','').split()]
    left,right=data['pages'][page-1]
    expected={(int(v[0]),int(v[1])) for v in data['verses'][left-1:right]}
    mapped=[]
    for node in polys:
        sur=int(node.attrib.get('surah','0')); ayah=int(node.attrib.get('ayah','0'))
        if not node.attrib.get('d'):
            raise ValueError(f'Page {page}: empty polygon for {sur}:{ayah}')
        mapped.append((sur,ayah))
    if len(polys)!=len(expected) or set(mapped)!=expected or len(set(mapped))!=len(mapped):
        extra=set(mapped)-expected; missing=expected-set(mapped)
        raise ValueError(f'Page {page}: verse polygon mismatch (expected {len(expected)}, found {len(polys)}); missing={missing}; extra={extra}')
    return len(polys)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--data',type=Path,required=True)
    args=parser.parse_args()
    data=source_data(args.data)
    assert len(data['pages'])==604 and len(data['verses'])==6236
    args.output.mkdir(parents=True,exist_ok=True)
    markers=0
    for page in range(1,PAGES+1):
        original=args.source/f'{page:03}.svg'
        if not original.is_file():raise FileNotFoundError(f'Missing original Hafs SVG page {page:03}')
        markers+=scan(page,original,data)
        shutil.copyfile(original,args.output/original.name)
        if page%100==0:print(f'Validated {page}/604 pages',flush=True)
    if markers!=6236:raise ValueError(f'Expected 6236 ayah polygons, found {markers}')
    manifest={'source':'quran-ws/quran-svg', 'edition':'hafs/kfqc',
       'source_commit':'b4155f07e4aea087d2c458069acff9f7c7e749f6',
       'pages':604,'ayah_polygons':markers,'format':'SVG: original art and per-ayah polygons'}
    (args.output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('OK: all 604 original-layout SVG pages and 6236 exact ayah regions verified')

if __name__=='__main__':main()
