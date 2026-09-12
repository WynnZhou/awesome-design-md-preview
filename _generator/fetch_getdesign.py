#!/usr/bin/env python3
"""Fetch a style's two pages straight from getdesign.md, for a style whose saved copy we never had.

It renders the page in headless Chrome — the site is a JS app, so curl only ever returns an 8K
shell — and writes the shape `merge_themes.py` expects:

    <style>@font-face …</style>   the font faces, pointing at our ../fonts/ copies
    <style>…</style>              the page's own stylesheet, untouched

The families we self-host are repointed at our own copies; anything else keeps the system fallback
rather than a dead request.

    python3 _generator/fetch_getdesign.py mobbin
"""

import base64
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_previews as gen  # noqa: E402  — shares the font cache and its downloader

OUT = Path(__file__).resolve().parent.parent
FONTS = OUT / 'design-md' / 'fonts'
ICONS = OUT / 'icons'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
SITE = 'https://getdesign.md/design-md'
# The VoltAgent mark in the footer credit. Fetched, not read off disk: a path into whoever ran
# this last is one more thing a clone would have to reproduce, and github.com serves the same
# 1153-byte png the pages carry.
LOGO_URL = 'https://github.com/VoltAgent.png?size=32'

FONT_LINK = re.compile(r'<link[^>]*fonts\.googleapis\.com[^>]*>')
# both preconnects go first, or the stylesheet regex below swallows the googleapis one too
FONT_PRE = re.compile(r'<link[^>]*rel="preconnect"[^>]*fonts\.(?:googleapis|gstatic)\.com[^>]*>')
BEACON = re.compile(r'<script\b[^>]*cloudflareinsights[^>]*>\s*</script>')
REMOTE_LOGO = re.compile(r'src="https://github\.com/VoltAgent\.png\?size=\d+"')
FAMILY_RE = re.compile(r'family=([^:&]+)(?::wght@([^&]+))?')
# the preconnect points at the same host, so this has to name the stylesheet path
FONT_CSS_LINK = re.compile(r'<link[^>]*fonts\.googleapis\.com/css2[^>]*>')

# the families we keep locally, by the name the page uses -> the package under fonts/
FONT_PKG = {
    'inter': 'inter',
    'ibm plex sans': 'ibm-plex-sans',
    'dm sans': 'dm-sans',
    'rubik': 'rubik',
    'geist': 'geist-sans',
}


def render(url):
    """The page as the browser sees it. --dump-dom runs the JS and hands back the live DOM."""
    r = subprocess.run([CHROME, '--headless', '--disable-gpu', '--no-sandbox',
                        '--virtual-time-budget=12000', '--dump-dom', url],
                       capture_output=True, text=True)
    if r.returncode or '<html' not in r.stdout:
        raise SystemExit(f'{url}: headless render failed ({r.returncode})')
    return r.stdout


def face_css(doc):
    """The @font-face block the page's own Google Fonts link would have carried, cut down to the
    families we host. Weights come from the link, so a page asking for 300–700 gets those blocks
    and nothing else; a variable range ('400..700') becomes the individual weights inside it."""
    link = FONT_CSS_LINK.search(doc)
    if not link:
        raise SystemExit('no Google Fonts <link> to read the families from')
    out = []
    for name, weights in FAMILY_RE.findall(link.group(0)):
        pkg = FONT_PKG.get(name.strip().lower().replace('+', ' '))
        if not pkg:
            continue
        wanted = []
        for part in (weights or '400').split(';'):
            part = part.strip()
            if '..' in part:
                lo, hi = (int(x) for x in part.split('..'))
                wanted += list(range(lo, hi + 1, 100))
            elif part.isdigit():
                wanted.append(int(part))
        def have(w):
            return (FONTS / f'{pkg}/{pkg}-latin-{w}-normal.woff2').is_file()
        wanted = list(dict.fromkeys(wanted))
        # a weight the page asks for and we host but have never fetched: get it now. Referencing a
        # file that is not there would silently drop the face and fall back to the system stack.
        if any(not have(w) for w in wanted):
            gen.ensure_font(name.replace('+', ' '), wanted)
        weights = [w for w in wanted if have(w)]
        for w in weights:
            f = f'{pkg}/{pkg}-latin-{w}-normal.woff2'
            out.append("@font-face {\n  font-family: '%s';\n  font-style: normal;\n"
                       "  font-weight: %d;\n  font-display: swap;\n"
                       "  src: url(../fonts/%s) format('woff2');\n}" % (name.replace('+', ' '), w, f))
    return '\n'.join(out)


def tidy(doc):
    doc, n = BEACON.subn('', doc)
    if n != 1:
        raise SystemExit(f'expected 1 Cloudflare beacon, removed {n}')
    doc = FONT_PRE.sub('', doc)
    # the Google Fonts stylesheet becomes an inline block, the way the saved pages carry it
    faces = face_css(doc)
    doc, n = FONT_LINK.subn(lambda _: '<style>\n' + faces + '\n</style>', doc)
    if n != 1:
        raise SystemExit(f'expected 1 fonts <link>, replaced {n}')
    logo = base64.b64encode(gen._get(LOGO_URL, timeout=20)).decode()
    doc, n = REMOTE_LOGO.subn(f'src="data:image/png;base64,{logo}"', doc)
    if n < 1:
        raise SystemExit('no remote VoltAgent avatar to inline')
    # the render is a live DOM: whatever the page ticked itself is not a state we saved
    doc = re.sub(r'<html([^>]*)>', r'<html\1>', doc, count=1)
    left = re.search(r'(?:src|href)="https?://[^"]*(?:fonts\.|cloudflareinsights)[^"]*"', doc)
    if left:
        raise SystemExit(f'unresolved remote ref: {left.group(0)}')
    return doc


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__.strip().splitlines()[-1])
    slug = sys.argv[1]
    dest = OUT / 'design-md' / slug
    dest.mkdir(exist_ok=True)
    for theme, path in (('light', 'preview'), ('dark', 'preview-dark')):
        url = f'{SITE}/{slug}/{path}'
        doc = tidy(render(url))
        (dest / f'preview_{theme}.html').write_text(doc, encoding='utf-8')
        print(f'  {slug:12} {theme:5} {len(doc) // 1024:4}K  <- {url}')
    print(f'\nwrote {slug}/preview_light.html + preview_dark.html — now run merge_themes.py {slug}')


if __name__ == '__main__':
    main()
