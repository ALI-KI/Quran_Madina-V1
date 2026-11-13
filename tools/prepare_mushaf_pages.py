#!/usr/bin/env python3
"""Render the original, fixed-layout KFGQPC Hafs39 pages without text reflow.

The pinned archival .ai files are PDF-compatible (PDF 1.5) even though their
filename suffix is .ai. Render these PDFs directly with Poppler's pdftoppm:
unlike Inkscape's desktop command, pdftoppm does not contact GIO/D-Bus and is
safe on headless GitHub runners. No Quran characters are generated or altered.

Source: KFGQPC Hafs39, pinned mirrored commit below. Follow source rights.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from PIL import Image

EXPECTED_PAGES = 604
SOURCE_COMMIT = 'a6f52f8b05fa28cdffb637cbbab0ed30515bbeb2'


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def convert_one(item, output: Path, width: int, quality: int) -> dict:
    page, source = item
    target = output / f'{page:03}.webp'
    # An Adobe Illustrator file saved with PDF compatibility contains real PDF
    # objects at the beginning; Poppler handles these directly without a GUI.
    with source.open('rb') as file:
        header = file.read(8)
    if not header.startswith(b'%PDF-'):
        raise RuntimeError(
            f'page {page}: source .ai has no PDF header; do not substitute '
            're-typeset Quran text or produce incomplete APK')

    with tempfile.TemporaryDirectory(prefix=f'mushaf-{page:03}-') as workdir:
        prefix = Path(workdir) / f'page-{page:03}'
        png = prefix.with_suffix('.png')
        command = [
            'pdftoppm', '-f', '1', '-l', '1', '-singlefile',
            '-scale-to-x', str(width), '-scale-to-y', '-1',
            '-png', str(source), str(prefix)
        ]
        try:
            completed = subprocess.run(
                command, capture_output=True, text=True, timeout=150,
                check=False
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(f'page {page}: PDF render timed out') from error

        if completed.returncode or not png.is_file():
            raise RuntimeError(
                f'page {page}: Poppler PDF conversion failed '
                f'(exit={completed.returncode}): {completed.stderr[-1500:]}')

        with Image.open(png) as image:
            img = image.convert('RGB')
            if img.width < width - 5 or img.height < 500:
                raise RuntimeError(f'page {page}: unexpected dimensions {img.size}')
            # Detect failed/blank outputs rather than building a visually empty mushaf.
            sample = img.resize((100, 140)).getdata()
            ink_pixels = sum(1 for r, g, b in sample if min(r, g, b) < 195)
            if ink_pixels < 25:
                raise RuntimeError(f'page {page}: renderer output appears blank')
            img.save(target, format='WEBP', quality=quality, method=5)

    if target.stat().st_size < 4000:
        raise RuntimeError(f'page {page}: output suspiciously small')
    return {
        'page': page,
        'file': target.name,
        'size_bytes': target.stat().st_size,
        'sha256': sha256(target),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--width', type=int, default=1200)
    parser.add_argument('--quality', type=int, default=92)
    parser.add_argument('--jobs', type=int, default=2)
    args = parser.parse_args()

    if args.width < 850:
        raise ValueError('Source-page output resolution is too low')
    if not shutil.which('pdftoppm'):
        raise RuntimeError('pdftoppm is missing: install poppler-utils')
    if not 1 <= args.jobs <= 8:
        raise ValueError('--jobs must be between 1 and 8')
    if not 0 <= args.quality <= 100:
        raise ValueError('WebP --quality must be between 0 and 100')

    source_dir = args.source
    output_dir = args.output
    if not source_dir.is_dir():
        raise RuntimeError(f'Original Mushaf source directory not found: {source_dir}')
    output_dir.mkdir(parents=True, exist_ok=True)

    originals = []
    for page in range(1, EXPECTED_PAGES + 1):
        matches = list(source_dir.rglob(f'{page:03}___Hafs39__DM.ai'))
        if len(matches) != 1:
            raise RuntimeError(
                f'page {page}: expected exactly one original, found {len(matches)}')
        if matches[0].stat().st_size < 15000:
            raise RuntimeError(f'page {page}: original source file too small')
        originals.append((page, matches[0]))

    print(
        f'Rendering {len(originals)} PDF-compatible original Mushaf vector pages '
        f'with headless pdftoppm, concurrency={args.jobs}', flush=True)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(convert_one, item, output_dir, args.width,
                               args.quality): item[0] for item in originals}
        try:
            for future in concurrent.futures.as_completed(futures):
                result = future.result()  # Never ignore errors from a page.
                results.append(result)
                if len(results) % 20 == 0:
                    print(f'pages rendered: {len(results)}/{EXPECTED_PAGES}', flush=True)
        except BaseException:
            for future in futures:
                future.cancel()
            # Incomplete output must not be mistaken for a valid 604-page cache.
            (output_dir / 'manifest.json').unlink(missing_ok=True)
            raise

    results.sort(key=lambda row: row['page'])
    if [record['page'] for record in results] != list(range(1, EXPECTED_PAGES + 1)):
        raise RuntimeError('Incomplete or unordered pages; refusing to write manifest')

    manifest = {
        'edition': 'KFGQPC Hafs39, original fixed vector layout',
        'renderer': 'poppler-pdftoppm',
        'mirror_commit': SOURCE_COMMIT,
        'width_pixels': args.width,
        'quality': args.quality,
        'page_count': len(results),
        'pages': results,
    }
    (output_dir / 'manifest.json').write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    if len(list(output_dir.glob('[0-9][0-9][0-9].webp'))) != EXPECTED_PAGES:
        raise RuntimeError('Generated page count is not exactly 604')
    print('Success: rendered all 604 original-layout pages; no Quran text reflow.',
          flush=True)


if __name__ == '__main__':
    main()
