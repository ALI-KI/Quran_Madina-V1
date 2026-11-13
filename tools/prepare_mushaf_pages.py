#!/usr/bin/env python3
"""Produce fixed-layout Quran pages from KFGQPC Hafs vector AI originals.

This script *never* recreates Arabic letters or Quran text. Each AI page is rasterized
with its existing paths/diacritics intact into one immutable phone-friendly WebP.

Source: King Fahd Glorious Quran Printing Complex — Hafs 1439 vector edition.
Public mirror pin: MushafAlMadinahVector/MushafAlMadinahVector @ a6f52f8b05fa28cdffb637cbbab0ed30515bbeb2
Official permissions: https://dm.qurancomplex.gov.sa/rights/

Requires: inkscape, Pillow. Exits nonzero if any original or rendered page is missing.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from PIL import Image, ImageStat

EXPECTED_PAGES=604
SOURCE_COMMIT='a6f52f8b05fa28cdffb637cbbab0ed30515bbeb2'

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for buf in iter(lambda:f.read(1024*1024),b''):h.update(buf)
    return h.hexdigest()

def convert_one(item,output,width,quality):
    page,source=item
    target=output / f'{page:03}.webp'
    with tempfile.TemporaryDirectory() as tmp:
        png=Path(tmp)/f'{page:03}.png'
        cmd=['inkscape',str(source),'--export-type=png','--export-area-page',
             f'--export-width={width}',f'--export-filename={png}']
        done=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=130)
        if done.returncode!=0 or not png.is_file():
            raise RuntimeError(f'page {page}: conversion failed: {done.stderr[-1000:]}')
        with Image.open(png) as image:
            img=image.convert('RGBA')
            if img.width<width-5 or img.height<500:
                raise RuntimeError(f'page {page}: incorrect image dimensions {img.size}')
            # Avoid silent blank images caused by broken AI renderers.
            samples=img.resize((100,140)).convert('RGBA').getdata()
            nonblank=sum(1 for r,g,b,a in samples if a>90 and min(r,g,b)<195)
            if nonblank<25:
                raise RuntimeError(f'page {page}: rendered nearly blank, refusing to package')
            img.save(target,format='WEBP',quality=quality,method=5)
    if target.stat().st_size<4000:
        raise RuntimeError(f'page {page}: output suspiciously small')
    return {'page':page,'file':target.name,'size_bytes':target.stat().st_size,'sha256':sha256(target)}

def main():
    pa=argparse.ArgumentParser()
    pa.add_argument('--source',required=True,type=Path)
    pa.add_argument('--output',required=True,type=Path)
    pa.add_argument('--width',type=int,default=1200)
    pa.add_argument('--quality',type=int,default=92)
    pa.add_argument('--jobs',type=int,default=3)
    args=pa.parse_args()
    if args.width<850:raise ValueError('Mushaf glyphs need a high enough resolution')
    inp=args.source;out=args.output;out.mkdir(parents=True,exist_ok=True)
    found={}
    for page in range(1,EXPECTED_PAGES+1):
        matches=list(inp.rglob(f'{page:03}___Hafs39__DM.ai'))
        if len(matches)!=1:
            raise RuntimeError(f'Page {page}: expected one original Hafs39 AI, found {len(matches)}')
        if matches[0].stat().st_size<15000:
            raise RuntimeError(f'Page {page}: AI file too small')
        found[page]=matches[0]
    items=list(found.items())
    reports=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures={pool.submit(convert_one,item,out,args.width,args.quality):item[0] for item in items}
        for f in concurrent.futures.as_completed(futures):
            p=futures[f]
            report=f.result();reports.append(report)
            if len(reports)%50==0: print(f'{len(reports)}/604 pages rendered',flush=True)
    reports.sort(key=lambda x:x['page'])
    manifest={'edition':'KFGQPC Hafs39, fixed original vector layout',
              'mirror_commit':SOURCE_COMMIT,'width_pixels':args.width,'quality':args.quality,
              'page_count':len(reports),'pages':reports}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    assert len(list(out.glob('[0-9][0-9][0-9].webp')))==604
    print('Success: 604 actual fixed-layout pages; no synthetic text reflow.')

if __name__=='__main__':main()
