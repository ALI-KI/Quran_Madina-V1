"""Build a single-file offline preview of the current Android WebView app UI.
All bundled CSS, JavaScript, fonts and decorative image assets are embedded.
"""
from pathlib import Path
import base64
root = Path(__file__).resolve().parents[1]
a = root / 'app/src/main/assets'
h = (a/'index.html').read_text(encoding='utf-8')
css = (a/'style.css').read_text(encoding='utf-8')
q = (a/'quran-data.js').read_text(encoding='utf-8')
app = (a/'app.js').read_text(encoding='utf-8')
for name in ('ornament-h.svg', 'ornament-v.svg', 'approved-ornament-h.png', 'approved-ornament-v.png', 'verse-medallion.svg', 'header-motif.svg'):
    mime = 'image/png' if name.endswith('png') else 'image/svg+xml'
    encoded = base64.b64encode((a/name).read_bytes()).decode('ascii')
    css = css.replace("url('" + name + "')", "url('data:" + mime + ';base64,' + encoded + "')")
b64font=base64.b64encode((a/'AmiriQuran.ttf').read_bytes()).decode('ascii')
css=css.replace("url('AmiriQuran.ttf')", "url('data:font/ttf;base64,"+b64font+"')")
h = h.replace('<link rel="stylesheet" href="style.css">', '<style>' + css + '</style>')
h = h.replace('<script src="quran-data.js"></script><script src="app.js"></script>', '<script>' + q + '</script><script>' + app + '</script>')
out = Path('/mnt/data/Quran_Madina_v0.4_Preview.html')
out.write_text(h, encoding='utf-8')
print('Preview:', out, 'bytes:',out.stat().st_size)
