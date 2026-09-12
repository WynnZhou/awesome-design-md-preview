#!/usr/bin/env python3
"""Fold <style>/preview_light.html + preview_dark.html into one preview.html + preview.css.

getdesign.md ships each style twice — the same document rendered light and rendered dark. The two
files are near-copies: <html>, <head> and <body> tags are byte-identical, the font stylesheet is
byte-identical, and the page stylesheet differs only in its :root values plus a handful of rules.
The bodies are identical for 41 of the 72 styles; the other 31 are hand-authored per theme, so they
carry different copy, different palette swatches and even different section headings.

So a merge has two shapes, chosen per style:

    same body   one <body>, one stylesheet — no theme layer, nothing to switch
    differs     both bodies kept, wrapped in .theme-layer[data-when], one hidden by the theme
                attribute; the two stylesheets scoped under html[data-theme="light"|"dark"]

Nothing is thrown away: every difference the dark page carries survives, including its prose.

Run:  python3 _generator/merge_themes.py [slug ...]     (no args = every style)
      python3 _generator/merge_themes.py --dry-run       (report, write nothing)
"""

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_previews as gen  # noqa: E402  — reuse _scoped / THEME_SCRIPT / THEME_TOGGLE / its CSS

OUT = Path(__file__).resolve().parent.parent

# The two layers are siblings in <body>; only the one the theme names is laid out. Both stay in the
# DOM so a theme flip is instant and nothing has to be re-fetched.
LAYER_CSS = '''.theme-layer { display: block; }
html[data-theme="light"] .theme-layer[data-when="dark"],
html[data-theme="dark"] .theme-layer[data-when="light"] { display: none; }
'''

# Duplicate `id`s are illegal and the dark layer is the one nobody can deep-link into first, so the
# ids live on the light layer and the dark layer carries data-sec instead. No stylesheet in any of
# these pages uses an `#id` selector, so nothing else depends on them.
# Runs in <head>, before the body is parsed. Without it the page paints the light theme written into
# the markup and only flips when THEME_SCRIPT runs at the end of <body> — a white flash on every dark
# load, and the viewer reloads the pane on every style change.
THEME_BOOT = '''<script>
(function () {
  var m = /[?&#]theme=(light|dark)/.exec(location.href), t = m && m[1];
  if (!t) { try { t = localStorage.getItem('design-md:theme'); } catch (e) {} }
  if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t;
})();
</script>'''

ID_RE = re.compile(r'\sid="([^"]+)"')


CANVAS_RE = re.compile(r'--canvas:\s*([^;]+);')

# preview.css is a separate file, so between the document starting and the stylesheet arriving the
# page has no styles at all — and an unstyled page is white. This inline block gives each theme its
# own canvas colour up front, so the first frame is the brand's own background, not a white flash.
CANVAS_FALLBACK = ('#ffffff', '#0b0b0c')


def canvas_boot(light_css, dark_css, same_css):
    light = (CANVAS_RE.search(light_css) or [None, CANVAS_FALLBACK[0]])[1]
    light = light.strip() if isinstance(light, str) else CANVAS_FALLBACK[0]
    if same_css:
        dark = light
    else:
        m = CANVAS_RE.search(dark_css)
        dark = m.group(1).strip() if m else CANVAS_FALLBACK[1]
    return (f'<style>html {{ background: {light}; }}'
            f' html[data-theme="dark"] {{ background: {dark}; }}</style>')
# kraken, lovable, spotify and tesla title their two files apart; the merged page needs one title
TITLE_RE = re.compile(r'(<title>[\s\S]*?)\s*(?:\((?:Light|Dark)\)|—\s*Dark Mode)\s*(</title>)')
ANCHOR_SCRIPT = '''<script>
(function () {
  // both layers carry the same sections; the ids sit on the light one, so a plain #anchor would
  // jump to a hidden element whenever the dark layer is the one showing. Resolve against whichever
  // layer is visible, falling back to the id when only one layer exists.
  function target(id) {
    var vis = document.querySelector('.theme-layer:not([data-when="__none__"])');
    var layers = [].slice.call(document.querySelectorAll('.theme-layer')).filter(function (l) {
      return getComputedStyle(l).display !== 'none';
    });
    for (var i = 0; i < layers.length; i++) {
      var hit = layers[i].querySelector('[data-sec="' + id + '"], #' + id);
      if (hit) return hit;
    }
    return document.getElementById(id);
  }
  function go(id, push) {
    var el = id && target(id);
    if (!el) return false;
    el.scrollIntoView();
    if (push) try { history.replaceState(null, '', '#' + id); } catch (e) {}
    return true;
  }
  addEventListener('click', function (e) {
    var a = e.target && e.target.closest && e.target.closest('a[href^="#"]');
    if (!a) return;
    var id = a.getAttribute('href').slice(1);
    if (!id) { e.preventDefault(); scrollTo(0, 0); return; }
    if (go(id, true)) e.preventDefault();
  });
  // arriving with #colors on a dark page, or flipping theme while parked on one
  addEventListener('hashchange', function () { go(decodeURIComponent(location.hash.slice(1)), false); });
  addEventListener('message', function () { setTimeout(function () { go(decodeURIComponent(location.hash.slice(1)), false); }, 0); });
  if (location.hash) setTimeout(function () { go(decodeURIComponent(location.hash.slice(1)), false); }, 0);
})();
</script>'''


def split(doc):
    """-> (head up to the first <style>, font css, page css, <body …> tag, body inner html)"""
    styles = re.findall(r'<style>([\s\S]*?)</style>', doc)
    if not styles:
        raise ValueError('no <style> block')
    # the save banner records which of the two URLs this copy came from, so it is the one thing in
    # the head that is *supposed* to differ — and it describes a file that no longer exists
    head = re.sub(r'<!--\s*saved from url=\(\d+\)[^>]*?-->\s*', '', doc[:doc.index('<style>')])
    head = TITLE_RE.sub(r'\1\2', head)
    bodytag = re.search(r'<body[^>]*>', doc).group(0)
    body = doc[doc.index(bodytag) + len(bodytag):doc.rindex('</body>')]
    # the first block is Google's font CSS the importer inlined; a page saved without one (Dell
    # 1996) has a single block and it is the page's own
    return head, (styles[0] if len(styles) == 2 else ''), styles[-1], bodytag, body


def secify(body):
    """Dark layer: id="x" -> data-sec="x", so the light layer keeps the only ids."""
    return ID_RE.sub(lambda m: ' data-sec="%s"' % m.group(1), body), len(ID_RE.findall(body))


def merge(slug, dry=False):
    d = OUT / 'design-md' / slug
    light_p, dark_p = d / 'preview_light.html', d / 'preview_dark.html'
    L = light_p.read_text(encoding='utf-8')
    # BMW M and Lamborghini have no dark variant upstream; the light page stands alone and its
    # stylesheet must stay unscoped, or the viewer's ?theme=dark would leave it unstyled
    solo = not dark_p.is_file()
    D = L if solo else dark_p.read_text(encoding='utf-8')
    hl, fl, pl, btl, bl = split(L)
    hd, fd, pd, btd, bd = split(D)
    for name, a, b in (('head', hl, hd), ('body tag', btl, btd), ('font css', fl, fd)):
        if a != b:
            raise ValueError(f'{slug}: {name} differs between the light and dark file')

    layers_used = bl != bd
    if layers_used:
        dark_body, moved = secify(bd)
        layers = ('\n<div class="theme-layer" data-when="light">\n' + bl + '\n</div>\n'
                  '<div class="theme-layer" data-when="dark">\n' + dark_body + '\n</div>\n')
        shape = f'layers (dark ids -> data-sec: {moved})'
    else:
        layers = bl
        shape = 'one body' + (' (light only, no dark upstream)' if solo else '')

    # Three styles (framer, hashicorp, linear-app) were downloaded twice as the same page: one
    # stylesheet, one look. Scoping it under a single theme would leave the other theme bare, so it
    # ships unscoped and simply does not change.
    if pl == pd:
        css = fl + '\n' + pl + '\n'
    else:
        css = (fl + '\n' + gen._scoped(pl, 'html[data-theme="light"]') + '\n'
               + gen._scoped(pd, 'html[data-theme="dark"]') + '\n')
    css += (LAYER_CSS if layers_used else '') + gen.THEME_TOGGLE_CSS

    head = hl if 'data-theme' in hl else hl.replace('<html ', '<html data-native="light" data-theme="light" ', 1)
    if head == hl:
        raise ValueError(f'{slug}: <html> already carries a theme attribute')
    head = head.replace('</title>',
                        '</title>\n<link rel="stylesheet" href="preview.css">\n'
                        + THEME_BOOT + canvas_boot(pl, pd, pl == pd), 1)
    # the inlined stylesheet is gone, so close the head ourselves
    doc = (head + '\n</head>\n' + btl + layers + gen.THEME_TOGGLE + gen.THEME_SCRIPT
           + ANCHOR_SCRIPT + '\n</body>\n</html>\n')

    if not dry:
        (d / 'preview.html').write_text(doc, encoding='utf-8')
        (d / 'preview.css').write_text(css, encoding='utf-8')
    return shape, len(doc), len(css), len(re.findall(r'\sid="', doc))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    dry = '--dry-run' in sys.argv
    slugs = args or sorted(d.name for d in OUT.iterdir() if (d / 'preview_light.html').is_file())
    total = 0
    for slug in slugs:
        try:
            shape, n, c, ids = merge(slug, dry)
        except ValueError as e:
            print(f'  {slug:14} SKIP  {e}')
            continue
        total += 1
        print(f'  {slug:14} {n // 1024:4}K html  {c // 1024:4}K css  ids={ids:<3} {shape}')
    print(f'\n{total} styles {"checked" if dry else "merged"}')


if __name__ == '__main__':
    main()
