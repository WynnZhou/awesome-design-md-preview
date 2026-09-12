#!/usr/bin/env python3
"""DESIGN.md -> preview_auto.html + preview_auto.css for every style in awesome-design-md.

Writes the self-generated pages and the viewer that loads them. The pages are then superseded by
merge_themes.py, which folds getdesign.md's own light/dark pair into the same filenames — run it
after this one."""
import re, json, html, pathlib, traceback, hashlib, base64, urllib.request

SRC = pathlib.Path('/tmp/awesome-design-md/design-md')
# Derived from this file, not a hard-coded home path: running a *copy* of this script must write
# into that copy, or a scratch run silently regenerates the real project. (It did.)
OUT = pathlib.Path(__file__).resolve().parent.parent


# awesome-design-md-cn ships a hand-authored preview.html + preview-dark.html per style. Those are
# truer to the brand than anything derived from DESIGN.md prose, so styles named here are ported
# from that repo instead of generated. Everything else keeps the generated path.
# Kept inside the output folder rather than /tmp, which macOS reaps.
NAV_PROSE = ('**`global-nav`** — Persistent, ultra-thin nav bar pinned to the top of every page. It has two\n'
             'variants, both translucent over a `saturate(180%) blur(20px)` backdrop, and a page uses\n'
             'whichever suits its canvas: on light pages the background is `rgba(250, 250, 252, .8)` with\n'
             '`rgba(0, 0, 0, .8)` labels, on dark pages `rgba(22, 22, 23, .8)` with `rgba(255, 255, 255, .8)`\n'
             'labels. Height 44px (48px on the taller variant), labels in `{typography.nav-link}`\n'
             '(12px / 400 / -0.12px tracking). Links are quiet, spaced ~20px apart, running edge-to-edge\n'
             'across the top. Right-aligned cluster: Search, Bag icons — always visible. On mobile,\n'
             'collapses to hamburger at ~834px and the Apple logo centers.')

DESIGN_PATCHES = {
    'apple': [
        # the product-tile badge ink, straight from apple.com's store CSS
        (r'(  on-dark: "#ffffff"\n)',
         '\\1  badge-text: "#b64400"\n'),
        (r'\*\*`global-nav`\*\* — Persistent, ultra-thin black nav bar[^\n]*', NAV_PROSE),
        (r'- Keep the global nav `\{colors\.surface-black\}` \(true black\)[^\n]*',
         '- Reserve `{colors.surface-black}` for the dark-page global nav and true void — the light-page\n'
         '  nav is `rgba(250, 250, 252, .8)` over a blur, not black.'),
        (r'(overlays,) the global nav bar background\.',
         r'\1 the global nav bar background on dark pages.'),
        (r'(All text on dark tiles and) on the global nav bar\.',
         r'\1 on the dark-page global nav bar.'),
        # …and the same correction in the frontmatter, so the Component Reference row stops
        # presenting the dark bar as the only one. Apple's two backgrounds are the values above.
        (r'(  global-nav:\n    backgroundColor: )"\{colors\.surface-black\}"\n'
         r'(    textColor: )"\{colors\.on-dark\}"\n',
         r'\1"{colors.surface-black} on dark pages, rgba(250, 250, 252, .8) on light pages"\n'
         r'\2"{colors.on-dark} on dark pages, rgba(0, 0, 0, .8) on light pages"\n'),
    ],
}

DESIGN_NOTE = '''
---

> **Local note — awesome-design-md-previews.** Everything above came from
> [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) byte-for-byte,
> except {n} passage(s) about the global nav, corrected against apple.com's own
> `globalheader.css`, which ships a light bar as well as the dark one. See `RULES.md`
> ("导航栏背景（跟随主题）").
'''


def patch_design_md(slug, text):
    """Apply this style's local corrections; returns (text, patches_applied)."""
    applied = 0
    for pat, rep in DESIGN_PATCHES.get(slug, []):
        text, n = re.subn(pat, rep, text, count=1)
        applied += n
    if applied:
        text = text.rstrip('\n') + '\n' + DESIGN_NOTE.format(n=applied)
    return text, applied

GOOGLE_FONTS = {
    'inter', 'dm sans', 'roboto', 'poppins', 'space grotesk', 'ibm plex sans',
    'manrope', 'work sans', 'public sans', 'figtree', 'outfit', 'sora',
    'plus jakarta sans', 'noto sans', 'open sans', 'lato', 'montserrat',
    'geist', 'instrument sans', 'bricolage grotesque', 'archivo', 'epilogue',
    'red hat display', 'rubik', 'karla', 'nunito sans', 'source sans 3',
    'jetbrains mono', 'ibm plex mono', 'space mono', 'roboto mono', 'fira code',
}

# ---------------------------------------------------------------- webfonts
# Google's own host drops packets from this network rather than refusing them, so the woff2 files
# come from the fontsource packages on jsDelivr: same upstream fonts, latin subset, one file per
# weight. They are cached in fonts/ once and then base64-inlined into each page's CSS, which keeps
# index.html a single self-contained file that also shows the brand type with no network at all.
FONTS = OUT / 'design-md' / 'fonts'
FONT_PKG = {'inter': 'inter', 'ibm plex sans': 'ibm-plex-sans', 'dm sans': 'dm-sans',
            'rubik': 'rubik', 'geist': 'geist-sans', 'nunito sans': 'nunito-sans'}
FONT_WEIGHTS = (400, 500, 600, 700, 800)
FONTSOURCE = 'https://cdn.jsdelivr.net/npm/@fontsource/{pkg}/files/{pkg}-latin-{w}-normal.woff2'
_font_css_cache = {}


def ensure_font(family, weights=None, log=None):
    """Cache the family's latin woff2 files in fonts/<pkg>/; return {weight: bytes}.

    Only the weights asked for are fetched. Pulling the whole 400–800 ladder regardless left
    files in fonts/ that no stylesheet referenced — and deleting them gained nothing, because the
    next run downloaded them straight back."""
    pkg = FONT_PKG.get(family.lower().strip())
    if not pkg:
        return {}
    got = {}
    for w in (weights or FONT_WEIGHTS):
        f = FONTS / pkg / f'{pkg}-latin-{w}-normal.woff2'
        if not f.is_file():
            f.parent.mkdir(parents=True, exist_ok=True)
            try:
                data = _get(FONTSOURCE.format(pkg=pkg, w=w))
            except Exception as e:
                if log:
                    log(f'font {pkg} {w}: {e}')
                continue
            if len(data) < 1000:      # a redirect body or an error page, not a woff2
                continue
            f.write_bytes(data)
            if log:
                log(f'font {pkg} {w}: {len(data)} B')
        got[w] = f.read_bytes()
    return got


def used_font_weights(css):
    """The weights a stylesheet actually asks for — embedding only these keeps fonts/ to what the
    pages use. Intersected with the ladder we host: a stylesheet asking for 480 or 300 has no file
    to fetch, and asking for one anyway is a 404 per page."""
    asked = {int(n) for n in re.findall(r'font-weight:\s*(\d{3})', css)}
    return (asked | {400}) & set(FONT_WEIGHTS)


def font_face_css(family, weights=None, linked=False):
    """@font-face rules for a family we host, or '' for one we do not.

    linked=False inlines the woff2 as a data URI, which is what makes index.html a single portable
    file. linked=True points at the cached copies in fonts/ instead — that is for preview_auto.css,
    where a stylesheet next to a fonts/ folder has no reason to carry a second copy of every face.
    """
    family = family.strip()
    want = tuple(sorted(weights)) if weights else None
    key = (family.lower(), want, linked)
    if key not in _font_css_cache:
        pkg = FONT_PKG.get(family.lower())
        faces = []
        for w, data in sorted(ensure_font(family, want).items()):
            if want and w not in want:
                continue
            if linked and pkg:
                src = f"url(../fonts/{pkg}/{pkg}-latin-{w}-normal.woff2)"
            else:
                src = 'url(data:font/woff2;base64,' + base64.b64encode(data).decode('ascii') + ')'
            faces.append(f"@font-face{{font-family:'{family}';font-style:normal;font-weight:{w};"
                         f"font-display:swap;src:{src} format('woff2');}}")
        _font_css_cache[key] = ('/* brand webfont, self-hosted */\n' + '\n'.join(faces) + '\n') if faces else ''
    return _font_css_cache[key]

# ---------------------------------------------------------------- yaml subset
KEY_RE = re.compile(r'^([^\s:][^:]*?):\s?(.*)$')


def unquote(v):
    v = v.strip()
    m = re.match(r'^(["\'])(.*?)\1(?:\s{2,}#.*)?$', v)      # "value"   # trailing comment
    if m:
        return m.group(2)
    return re.sub(r'\s{2,}#\s.*$', '', v)                    # bare value  # trailing comment


def parse_block(lines, i, indent):
    out = {}
    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith('#'):
            i += 1
            continue
        ind = len(raw) - len(raw.lstrip(' '))
        if ind < indent:
            break
        if ind > indent:
            i += 1
            continue
        m = KEY_RE.match(raw.strip())
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if val == '':
            sub, i = parse_block(lines, i + 1, indent + 2)
            out[key] = sub
        else:
            out[key] = unquote(val)
            i += 1
    return out, i


def parse_frontmatter(text):
    lines = text.split('\n')
    if not lines or lines[0].strip() != '---':
        return None
    try:
        end = [n for n in range(1, len(lines)) if lines[n].strip() == '---'][0]
    except IndexError:
        return None
    data, _ = parse_block(lines[1:end], 0, 0)
    return data or None


# ---------------------------------------------------------------- md helpers
def sections(text):
    """[(level, title, body)] for ## / ### headings."""
    out, cur = [], None
    for line in text.split('\n'):
        m = re.match(r'^(#{2,3})\s+(.*)$', line)
        if m:
            if cur:
                out.append(cur)
            cur = [len(m.group(1)), m.group(2).strip(), []]
        elif cur:
            cur[2].append(line)
    if cur:
        out.append(cur)
    return [(lvl, title, '\n'.join(body)) for lvl, title, body in out]


def tree(text):
    """Nested heading tree: node = {level, title, body(str), children}."""
    root = {'level': 0, 'title': '', 'body': [], 'children': []}
    stack = [root]
    for line in text.split('\n'):
        m = re.match(r'^(#{1,4})\s+(.*)$', line)
        if m:
            node = {'level': len(m.group(1)), 'title': m.group(2).strip(),
                    'body': [], 'children': []}
            while len(stack) > 1 and stack[-1]['level'] >= node['level']:
                stack.pop()
            stack[-1]['children'].append(node)
            stack.append(node)
        else:
            stack[-1]['body'].append(line)
    def fin(n):
        n['body'] = '\n'.join(n['body'])
        for c in n['children']:
            fin(c)
        return n
    return fin(root)


def walk(node):
    for c in node['children']:
        yield c
        yield from walk(c)


def find_node(root, *needles, level=None):
    for n in node_iter(root):
        if level and n['level'] != level:
            continue
        low = n['title'].lower()
        if any(x.lower() in low for x in needles):
            return n
    return None


def node_iter(node):
    for c in node['children']:
        yield c
        yield from node_iter(c)


def find_sec(secs, *needles, level=None):
    for lvl, title, body in secs:
        if level and lvl != level:
            continue
        low = title.lower()
        if any(n.lower() in low for n in needles):
            return lvl, title, body
    return None


def bullets(body):
    return re.findall(r'^\s*[-*]\s+(.*)$', body, re.M)


def md_table(body):
    rows = []
    for line in body.split('\n'):
        line = line.strip()
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if all(re.fullmatch(r':?-{2,}:?', c or '-') for c in cells):
            continue
        rows.append(cells)
    return rows


def clean(v):
    return (v or '').replace('`', '').strip()


# Values in prose sources carry editorial noise: "9999px (full pill)", "#181818 or #1f1f1f",
# "50% (circle)". The first alternative of an "or" is the one the spec means, and a trailing
# parenthetical is a note rather than part of the value.
CSS_FN = re.compile(r'^(?:color-mix|rgba?|hsla?|oklch|var|calc|clamp|min|max|linear-gradient|'
                    r'radial-gradient|conic-gradient|url)\(')


def tidy_value(v):
    """Strip editorial noise from a token value, leaving something a browser can use."""
    v = clean(v)
    if not v or CSS_FN.match(v):      # a function call may legitimately end in ")"
        return v
    v = re.sub(r'^(?:approximately|approx\.?|about|roughly|nearly|around|up to|just|'
               r'[~≈≥≤])\s*', '', v, flags=re.I)
    v = re.split(r'\s+or\s+', v, maxsplit=1, flags=re.I)[0]
    v = re.sub(r'\s*\([^()]*\)\s*$', '', v)        # trailing parenthetical note
    v = re.sub(r'\s+[—–]\s+[^—–]*$', '', v)         # trailing em-dash note
    return v.strip().strip(',;').strip()


V_PAD, H_PAD = 40.0, 64.0


def clamp_padding(style):
    """Cap the demo box's padding: a hero band's 200px would swamp the whole grid.

    Display only — the untouched values stay in the Component Reference table, and the demo box
    carries the original string in its title attribute.
    """
    m = re.search(r'padding:([^;]+)', style)
    if not m:
        return style
    parts = m.group(1).split()
    if len(parts) not in (1, 2, 4):
        return style
    vals = []
    for i, p in enumerate(parts):
        n = px(p, None)
        vals.append(p if n is None else f'{min(n, V_PAD if i % 2 == 0 else H_PAD):g}px')
    return style[:m.start(1)] + ' '.join(vals) + style[m.end(1):]


def has_visible_border(style):
    for decl in style.split(';'):
        if ':' not in decl or not decl.lstrip().startswith('border'):
            continue
        v = decl.split(':', 1)[1].strip()
        if v and not re.match(r'^(?:none|0)\b', v) and not v.endswith('transparent'):
            return True
    return False


def colour_of(v, t):
    """Best-effort hex for a colour-ish value, following one {colors.x} reference."""
    m = re.fullmatch(r'\{colors\.([^}]+)\}', str(v).strip())
    if m:
        for name, val, *_ in t.get('colors', []):
            if slugify(name) == slugify(m.group(1)):
                return val if hex_to_rgb(val) else None
        return None
    s = tidy_value(v)
    return s if hex_to_rgb(s) else None


GENERIC_HEAD = {
    'button', 'buttons', 'btn', 'badge', 'badges', 'pill', 'pills', 'tag', 'tags', 'chip',
    'chips', 'card', 'cards', 'input', 'inputs', 'form', 'forms', 'nav', 'navbar', 'link',
    'links', 'panel', 'banner', 'tooltip', 'menu', 'surface', 'component', 'components',
    'ex', 'example',
}


KEEP_TAIL = {'bar', 'on', 'in', 'for', 'with', 'at', 'of'}


def comp_label(k):
    """'buttons-dark-large-pill' -> 'Dark Large Pill'; 'text-input' -> 'Text Input'."""
    s = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', re.sub(r'[-_]+', ' ', k))
    words = s.split()
    # The leading noun just repeats the section heading — unless what follows is a preposition
    # or "bar", where it is part of the name ("Nav Bar", "Link On Light").
    if len(words) > 1 and words[0].lower() in GENERIC_HEAD and words[1].lower() not in KEEP_TAIL:
        words = words[1:]
    out = []
    for w in words:
        if w.isupper() or (w[:1].isupper() and any(c.isupper() for c in w[1:])):
            out.append(w)             # keep acronyms and camelCase tails as authored
        else:
            out.append(w[:1].upper() + w[1:])
    return ' '.join(out).strip()


COLOR_LIKE = re.compile(r'^(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|hsla?\([^)]*\)|oklch\([^)]*\))$')

INLINE_PROP_RE = {
    'backgroundColor': r'\bbg(?:-color)?\s*[:=]?\s*(`?\s*(?:#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|transparent|white|black)[^,;\n]*)',
    'textColor': r'\b(?:text|color|fg|foreground)\s*[:=]?\s*(`?\s*(?:#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|transparent|white|black)[^,;\n]*)',
    'padding': r'\bpadding\s*[:=]?\s*(\d+(?:\.\d+)?(?:px|rem)(?:\s+\d+(?:\.\d+)?(?:px|rem|%))*[^,;\n]*)',
    'fontSize': r'\bfont-?size\s*[:=]?\s*(\d+(?:\.\d+)?(?:px|rem|em))',
    'fontWeight': r'\bfont-?weight\s*[:=]?\s*(\d{3})',
    'rounded': r'\b(?:border-?radius|radius)\b\s*[:=]?\s*[^,;\n()]*?\(?(\d+(?:\.\d+)?(?:px|rem|%))',
    'border': r'\bborder\s*[:=]?\s*(\d+px\s+solid\s+[^,;\n]+)',
    'opacity': r'\bopacity\s*[:=]?\s*(\d+(?:\.\d+)?)',
}


def inline_props(text):
    """Pull CSS-ish properties out of free-form prose bullets."""
    out = {}
    for prop, pat in INLINE_PROP_RE.items():
        m = re.search(pat, text, re.I)
        if m:
            val = clean(m.group(1)).strip()
            val = re.sub(r'^\(|\)$', '', val).strip()
            if val:
                out[prop] = val
    return out


def parse_md_tokens(text):
    """Best-effort token extraction for DESIGN.md files without YAML frontmatter."""
    secs = sections(text)
    root = tree(text)
    tok = {'colors': [], 'typography': {}, 'rounded': {}, 'spacing': {},
           'components': {}, 'shadows': [], 'fonts': [], 'groups': [], 'do': [], 'dont': []}

    # ---- colors (grouped by ### heading inside the colour section)
    cnode = find_node(root, 'color palette', 'color system', 'color', level=2)
    if cnode:
        groups = [c for c in cnode['children'] if c['children'] or c['body'].strip()]
        if not groups:
            groups = [cnode]
        for gnode in groups:
            title = re.sub(r'^\d+[.)]\s*', '', gnode['title']).strip()
            group = []
            for b in bullets(gnode['body']):
                # prefer a backticked value: it may itself contain parentheses ("rgba(0,0,0,.5) 0px 8px 24px"),
                # which the plain [^)]* form would cut at the first one
                m = (re.match(r'^\*\*(?P<name>[^*]+)\*\*\s*(?:\(`(?P<val>[^`]*)`\))?\s*[:—-]?\s*(?P<desc>.*)$', b)
                     or re.match(r'^\*\*(?P<name>[^*]+)\*\*\s*(?:\((?P<val>[^)]*)\))?\s*[:—-]?\s*(?P<desc>.*)$', b))
                if not m:
                    m = re.match(r'^(?P<name>[^(:]+?)\s*\((?:`)?(?P<val>[^)`]+)(?:`)?\)\s*:?\s*(?P<desc>.*)$', b)
                if not m:
                    continue
                name, val, desc = clean(m.group('name')), clean(m.group('val')), clean(m.group('desc'))
                if not val:
                    continue
                if COLOR_LIKE.match(val):
                    group.append((name, val, desc))
                elif re.search(r'\d+px', val) or 'rgba' in val or 'rgb(' in val:
                    tok['shadows'].append((name, val, desc))
            if group:
                tok['groups'].append((title, group))
                tok['colors'].extend(group)

    # ---- typography table (column layout varies: with/without a Font column)
    ts = find_sec(secs, 'hierarchy', 'typography scale', 'type scale', level=3) or find_sec(secs, 'typography', level=2)
    if ts:
        rows = md_table(ts[2])
        if rows:
            hdr = [c.lower() for c in rows[0]]

            def col(*names):
                for n in names:
                    for i, h in enumerate(hdr):
                        if n in h:
                            return i
                return None

            def cell(row, idx):
                return clean(row[idx]) if idx is not None and idx < len(row) else ''

            i_role, i_font = col('role', 'name', 'style', 'token'), col('font', 'family', 'typeface')
            i_size, i_w = col('size', 'px', 'scale'), col('weight')
            i_lh, i_ls = col('line', 'leading'), col('letter', 'tracking')
            unknown_hdr = not any(x in hdr[0] for x in ('role', 'name', 'token', 'style', 'level'))
            for row in rows if unknown_hdr else rows[1:]:
                role, size = cell(row, i_role) or cell(row, 0), cell(row, i_size)
                if not role or not size:
                    continue
                mm = re.search(r'(\d+(?:\.\d+)?)\s*px', size)
                if mm:
                    size_px = float(mm.group(1))
                else:
                    mm = re.search(r'(\d+(?:\.\d+)?)\s*rem', size)
                    if not mm:
                        continue
                    size_px = float(mm.group(1)) * 16
                w = re.search(r'\d+', cell(row, i_w))
                lh = cell(row, i_lh)
                lhn = re.search(r'(\d+(?:\.\d+)?)\s*(?:px)?', lh)
                if lh and lhn and 'px' in lh and size_px:
                    lh = f'{float(lhn.group(1)) / size_px:.2f}'
                tok['typography'][slugify(role)] = {
                    'name': role,
                    'fontFamily': cell(row, i_font).split(',')[0] or '',
                    'fontSize': f'{size_px:g}px',
                    'fontWeight': w.group(0) if w else '400',
                    'lineHeight': lh if lh and lh != '—' else '1.4',
                    'letterSpacing': cell(row, i_ls) or 'normal',
                }
        # font families
        fs = find_sec(sections(ts[2]), 'font famil', 'font', level=3)
        if fs:
            for b in bullets(fs[2]):
                m = re.search(r'`([^`]+)`', b)
                if m:
                    tok['fonts'].append(m.group(1))

    # ---- radius (list may live in the heading itself: "Border Radius: 3px, 6px, ...")
    rnode = find_node(root, 'border radius', 'radius scale', 'radius')
    if rnode:
        head_vals = re.search(r'[:—-]\s*((?:\d+(?:\.\d+)?(?:px|rem|%)\s*,\s*)+\S+)', rnode['title'])
        if head_vals:
            for idx, v in enumerate(x.strip() for x in head_vals.group(1).split(',')):
                if v:
                    tok['rounded'][slugify(f'r{idx}-{v}')] = v
        for b in bullets(rnode['body']):
            m = re.match(r'^\*\*(?P<name>[^*]+)\*\*\s*\((?P<val>[^)]*)\)', b) or \
                re.match(r'^(?P<name>[^(:]+?)\s*\((?P<val>[^)]*)\)', b)
            if m:
                tok['rounded'][slugify(clean(m.group('name')))] = clean(m.group('val'))
        if not tok['rounded']:           # table form: | Value | Context | / | Token | Value | Usage |
            rows = md_table(rnode['body'])
            if rows:
                hdr = [c.lower() for c in rows[0]]
                vi = next((i for i, h in enumerate(hdr)
                           if 'value' in h or 'radius' in h or 'token' in h and len(hdr) == 2), None)
                ni = next((i for i, h in enumerate(hdr) if 'token' in h or 'name' in h), None)
                ci = next((i for i, h in enumerate(hdr) if 'context' in h or 'use' in h or 'usage' in h), None)
                for row in rows[1:]:
                    if vi is None or vi >= len(row):
                        continue
                    vcell = clean(row[vi])
                    m = re.search(r'(\d+(?:\.\d+)?(?:px|%)(?:\s+\d+(?:\.\d+)?(?:px|%))*)', vcell)
                    val = m.group(1) if m else vcell
                    if ni is not None and ni < len(row):
                        nm = clean(row[ni])
                    elif ci is not None and ci < len(row) and len(clean(row[ci])) < 28:
                        nm = clean(row[ci])
                    else:
                        nm = f'radius-{val}'
                    tok['rounded'][slugify(nm)] = val

    # ---- spacing
    snode = find_node(root, 'spacing')
    if snode:
        head_vals = re.search(r'[:—-]\s*((?:\d+(?:\.\d+)?(?:px|rem)\s*,\s*)+\S+)', snode['title'])
        if head_vals:
            for idx, v in enumerate(x.strip() for x in head_vals.group(1).split(',')):
                if v:
                    tok['spacing'][slugify(f's{idx}-{v}')] = v
        for b in bullets(snode['body']):
            m = re.search(r'[Ss]cale:?\s*(.+)$', b)
            if m:
                for idx, v in enumerate(clean(x) for x in m.group(1).split(',') if clean(x)):
                    tok['spacing'][slugify(f's{idx}-{v}')] = v
            m2 = re.match(r'^\*\*(?P<name>[^*]+)\*\*\s*[:—-]\s*(?P<val>\d+(?:\.\d+)?(?:px|rem))', b)
            if m2:
                tok['spacing'][slugify(clean(m2.group('name')))] = clean(m2.group('val'))
        if not tok['spacing']:           # table form: | Token | Value | Usage | / | Token | Rem | Pixels |
            rows = md_table(snode['body'])
            if rows:
                hdr = [c.lower() for c in rows[0]]
                ni = next((i for i, h in enumerate(hdr) if 'token' in h or 'name' in h), 0)
                vi = next((i for i, h in enumerate(hdr)
                           if 'pixel' in h or 'value' in h or 'px' in h), None)
                if vi is None:
                    vi = next((i for i, h in enumerate(hdr) if 'rem' in h), None)
                for row in rows[1:]:
                    if vi is None or vi >= len(row) or ni >= len(row):
                        continue
                    nm, vcell = clean(row[ni]), clean(row[vi])
                    m = re.search(r'(\d+(?:\.\d+)?(?:px|rem))', vcell)
                    if nm and m:
                        tok['spacing'][slugify(nm)] = m.group(1)
        if not tok['spacing']:
            m = re.search(r'[Bb]ase unit:?\s*\**\s*(\d+(?:\.\d+)?px)', snode['body'])
            if m:
                tok['spacing']['base'] = m.group(1)

    # ---- depth & elevation table
    ds = find_sec(secs, 'depth', 'elevation', level=2)
    if ds:
        for row in md_table(ds[2]):
            if len(row) < 2:
                continue
            if row[0].lower() in ('level', 'name'):
                continue
            tok['shadows'].append((row[0], clean(row[1]), clean(row[2]) if len(row) > 2 else ''))

    # ---- components
    cnode = find_node(root, 'component styl', 'components', level=2)
    if cnode:
        gnames = [c for c in cnode['children']]
        if not gnames:
            gnames = [cnode]
        for gnode in gnames:
            title = re.sub(r'^\d+[.)]\s*', '', gnode['title']).strip()
            body = gnode['body']
            # Whitespace is pinned to [ \t] and $ to the same line: with \s* the trailing
            # "— description" group could reach across the newline, match the following
            # "- Prop: value" bullet and eat it, silently dropping each component's first property.
            items = list(re.finditer(
                r'^[ \t]*\*\*(?P<name>[^*:]{2,42})\*\*[ \t]*(?:[:：][ \t]*)?'
                r'(?:[—–-][ \t]*[^—–\n]{0,70}?[:：]?)?[ \t]*$',
                body, re.M))
            if not items and bullets(body):   # prose group: synthesise one entry from its bullets
                props = inline_props(' '.join(bullets(body)))
                for b in bullets(body):
                    km = re.match(r'^(?P<k>[A-Za-z][A-Za-z /-]*?)\s*:\s*(?P<v>.+)$', b)
                    if km:
                        props.setdefault(km.group('k').strip(), clean(km.group('v')))
                props = {k: tidy_value(v) for k, v in props.items()}
                if props:
                    tok['components'][slugify(title)] = {
                        k: v for k, v in props.items() if css_safe(k, v)}
                continue
            for idx, m in enumerate(items):
                stop = items[idx + 1].start() if idx + 1 < len(items) else len(body)
                chunk = body[m.end():stop]
                props = {}
                for b in bullets(chunk):
                    km = re.match(r'^\*\*(?P<k>[^*]+)\*\*\s*[:—-]\s*(?P<v>.+)$', b) or \
                        re.match(r'^(?P<k>[A-Za-z][A-Za-z /-]*?)\s*:\s*(?P<v>.+)$', b)
                    if km:
                        props[km.group('k').strip()] = clean(km.group('v'))
                    else:
                        props.setdefault('_raw', '')
                        props['_raw'] += ' ' + clean(b)
                props.update(inline_props(props.pop('_raw', '')))
                props = {k: tidy_value(v) for k, v in props.items() if not k.startswith('_')}
                props = {k: v for k, v in props.items() if css_safe(k, v)}
                if props:
                    tok['components'][slugify(f'{title}-{m.group("name")}')] = props

    # ---- guidelines
    for lvl, title, body in secs:
        if lvl != 3:
            continue
        low = title.lower()
        if low.startswith("don't") or low.startswith('dont'):
            tok['dont'] = [clean(b) for b in bullets(body)][:6]
        elif low.startswith('do'):
            tok['do'] = [clean(b) for b in bullets(body)][:6]
    return tok


# ---------------------------------------------------------------- helpers
def slugify(s):
    s = re.sub(r'[^a-zA-Z0-9]+', '-', str(s)).strip('-').lower()
    return s or 'x'


def px(v, default=0.0):
    m = re.search(r'(-?\d+(?:\.\d+)?)', str(v))
    return float(m.group(1)) if m else default


def hex_to_rgb(c):
    c = c.strip()
    m = re.fullmatch(r'#([0-9a-fA-F]{3,8})', c)
    if not m:
        m = re.search(r'rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)', c)
        return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None
    h = m.group(1)
    if len(h) == 3:
        h = ''.join(ch * 2 for ch in h)
    if len(h) < 6:
        return None
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminance(c):
    rgb = hex_to_rgb(c)
    if not rgb:
        return None
    r, g, b = [x / 255 for x in rgb]
    f = lambda u: u / 12.92 if u <= 0.03928 else ((u + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast_ratio(a, b):
    la, lb = luminance(a), luminance(b)
    if la is None or lb is None:
        return 21.0
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def contrast_on(c, dark='#0a0a0a', light='#ffffff'):
    l = luminance(c)
    if l is None:
        return light
    return dark if l > 0.45 else light


def resolve(v, t):
    """{colors.primary} -> var(--c-primary)"""
    if not isinstance(v, str):
        return str(v)
    def rep(m):
        path = m.group(1).split('.')
        if path[0] == 'colors':
            return f'var(--c-{slugify(path[1])})'
        if path[0] == 'rounded':
            return f'var(--r-{slugify(path[1])})'
        if path[0] == 'spacing':
            return f'var(--s-{slugify(path[1])})'
        if path[0] == 'typography':
            return f'var(--t-{slugify(path[1])}-size)'
        return m.group(0)
    return re.sub(r'\{([^}]+)\}', rep, v)


PROP_MAP = {
    'backgroundcolor': 'background', 'background': 'background', 'fill': 'background',
    'textcolor': 'color', 'color': 'color', 'foreground': 'color',
    'rounded': 'border-radius', 'borderradius': 'border-radius', 'radius': 'border-radius',
    'padding': 'padding', 'border': 'border', 'size': 'size', 'width': 'width',
    'height': 'height', 'shadow': 'box-shadow', 'boxshadow': 'box-shadow',
    'fontsize': 'font-size', 'fontweight': 'font-weight', 'lineheight': 'line-height',
    'letterspacing': 'letter-spacing', 'fontfamily': 'font-family',
    'texttransform': 'text-transform', 'gap': 'gap', 'opacity': 'opacity',
}


def css_safe(prop, val):
    """Reject prose that slipped into a property slot."""
    # {colors.primary} is our own token syntax, never prose — blank it out before sniffing.
    v = re.sub(r'\{[^{}]*\}', 'X', str(val)).strip()
    if not v or len(v) > 90:
        return False
    if re.search(r'[(){}\[\]]', v) and not re.match(r'^(rgba?|hsla?|var|color-mix|clamp|min|max|calc)\(', v):
        return False
    if re.search(r'[^0-9a-zA-Z\s#.,%()\-+*/"\']', v):
        return False
    if len(v.split()) > 4:
        return False
    return True


def props_to_style(props, t):
    pairs, bg_val, fg_seen = [], None, False
    for k, v in props.items():
        key = slugify(k).replace('-', '')
        tgt = PROP_MAP.get(key)
        if not tgt:
            continue
        raw = tidy_value(v)
        # Check the resolved value: a {colors.primary} reference is our syntax, not prose, and
        # testing it before resolve() rejected every token-driven property on the 61 frontmatter
        # styles — their buttons and cards came out as bare unpadded text.
        val = resolve(raw, t)
        if not css_safe(k, val):
            continue
        if tgt == 'size':
            pairs += [('width', val), ('height', val)]
        elif tgt == 'border':
            pairs.append(('border', val))
        else:
            pairs.append((tgt, val))
        if tgt == 'background':
            bg_val = raw
        elif tgt == 'color':
            fg_seen = True
    # A component that names a background but no text colour would inherit the page ink and
    # disappear against it, so pick whichever end of the ramp reads on that background.
    if bg_val and not fg_seen:
        flat = colour_of(bg_val, t)
        if flat:
            pairs.append(('color', contrast_on(flat)))
    dedup = {}                      # a source may name the same property twice ("rounded" and "Radius")
    for a, b in pairs:
        dedup[a] = b
    return ';'.join(f'{a}:{b}' for a, b in dedup.items())


def typo_lookup(props, t):
    for k, v in props.items():
        m = re.fullmatch(r'\{typography\.([^}]+)\}', str(v).strip())
        if m:
            return t.get('typography', {}).get(m.group(1))
    return None


# ---------------------------------------------------------------- tokens
def load_tokens(d, design_md=None):
    # design_md lets the caller pass the locally corrected text, so a patch lands in the tokens too
    text = design_md if design_md is not None else (d / 'DESIGN.md').read_text(encoding='utf-8')
    fm = parse_frontmatter(text)
    if fm and isinstance(fm.get('colors'), dict):
        body = text.split('\n---\n', 1)[-1]
        t = {
            'name': fm.get('name') or d.name,
            'description': fm.get('description') or '',
            'colors': [(k, v, '') for k, v in fm['colors'].items() if isinstance(v, str)],
            'typography': {k: dict(v, name=k) for k, v in (fm.get('typography') or {}).items() if isinstance(v, dict)},
            'rounded': {k: str(v) for k, v in (fm.get('rounded') or {}).items()},
            'spacing': {k: str(v) for k, v in (fm.get('spacing') or {}).items()},
            'components': {k: {kk: str(vv) for kk, vv in v.items()} for k, v in (fm.get('components') or {}).items() if isinstance(v, dict)},
            'shadows': [], 'fonts': [], 'groups': [], 'do': [], 'dont': [],
            'source': 'frontmatter',
        }
        md = parse_md_tokens(body)
        t['do'], t['dont'] = md['do'], md['dont']
        if not t['fonts']:
            t['fonts'] = md['fonts']
        # brand-specific shadows sometimes live in the markdown body
        for nm, val, desc in md['shadows']:
            if re.search(r'\d+px', val):
                t['shadows'].append((nm, val, desc))
        seen = set()
        t['shadows'] = [s for s in t['shadows'] if not (s[1] in seen or seen.add(s[1]))]
        return t

    md = parse_md_tokens(text)
    name = d.name
    m = re.match(r'^#\s*(.+)$', text, re.M)
    if m:
        name = re.sub(r'^Design System (Inspired by|Analysis of)?\s*', '', m.group(1)).strip()
    md.update({'name': name, 'description': '', 'source': 'markdown'})
    desc = []
    for line in text.split('\n')[2:14]:
        if line.strip() and not line.startswith('#'):
            desc.append(line.strip())
        elif desc:
            break
    md['description'] = ' '.join(desc)
    if not md['groups'] and md['colors']:
        md['groups'] = [('Colors', md['colors'])]
    return md


def derive_base(t):
    """canvas / ink / surface / hairline / primary / on-primary"""
    colors = {slugify(k): v for k, v, *_ in t['colors']}

    def pick(*pats, exclude=()):
        """Exact name match beats prefix beats substring."""
        for match in (lambda k, p: k == p, lambda k, p: k.startswith(p), lambda k, p: p in k):
            for p in pats:
                for k, v in colors.items():
                    if match(k, p) and not any(e in k for e in exclude):
                        return v
        return None

    canvas = pick('canvas', 'background', 'bg', 'page', 'base', exclude=('on-',))
    ink = pick('ink', 'text-base', 'text-primary', 'foreground', 'fg', exclude=('on-', 'inverse'))
    surface = pick('surface', 'panel', 'card', 'elevated')
    hairline = pick('hairline', 'border', 'divider', 'separator')
    primary = pick('primary', exclude=('on-', 'soft', 'hover', 'pressed', 'text', 'bg', 'border', 'deep', 'subdued'))

    # descriptions carry the semantics for markdown-sourced styles ("Deepest background surface")
    def scored(pos_patterns, neg_patterns=(), require=None):
        """Score colour descriptions; `require` gates which colours are even candidates."""
        best = None
        for item in t['colors']:
            desc = (item[2] if len(item) > 2 else '').lower()
            if not desc or (require and not re.search(require, desc)):
                continue
            s = sum(w for pat, w in pos_patterns if re.search(pat, desc)) \
                - sum(w for pat, w in neg_patterns if re.search(pat, desc))
            if s > 0 and (best is None or s > best[0]):
                best = (s, item[1])
        return best[1] if best else None

    if canvas is None:
        canvas = scored([(r'deepest|default|entire|page|base', 3), (r'background', 2),
                         (r'surface|canvas', 1)],
                        [(r'card|secondary|elevated|hover|text', 2)],
                        require=r'background|canvas|surface|page')
    if ink is None:
        ink = scored([(r'primary text|text-base|body text|display', 4), (r'\btext\b|ink', 1),
                      (r'foreground|headline', 2)],
                     [(r'inverted|on dark|on light|muted|secondary|subtle|disabled|link', 3),
                      (r'background|surface', 2)],
                     require=r'text|ink|foreground|headline')
    if primary is None:
        primary = scored([(r'primary brand|brand accent|primary accent|primary action', 4),
                          (r'\bcta\b|accent|brand', 2)],
                         [(r'hover|border|focus', 2)])

    lums = [(luminance(v), v) for _, v, *_ in t['colors'] if luminance(v) is not None]
    if canvas is None and lums:
        canvas = max(lums)[1]
    # ink must actually contrast with the canvas: on a dark page the text is the light end, not the dark one
    if lums:
        clum = luminance(canvas)
        ranked = sorted(lums, reverse=(clum is not None and clum < 0.5))
        if ink is None or slugify(ink) == slugify(canvas) or contrast_ratio(ink, canvas) < 4.5:
            ink = next((v for _, v in ranked
                        if slugify(v) != slugify(canvas) and contrast_ratio(v, canvas) >= 4.5),
                       ranked[0][1])
    if primary is None:
        used = {slugify(canvas), slugify(ink)}
        cands = [(luminance(v), v) for _, v, *_ in t['colors']
                 if luminance(v) is not None and slugify(v) not in used]
        picked = None
        for l, v in cands:
            if 0.02 < l < 0.6:
                picked = v
                break
        primary = picked or (cands[0][1] if cands else None)
    primary = primary or '#111111'
    canvas = canvas or '#ffffff'
    ink = ink or '#0a0a0a'
    surface = surface or canvas
    if slugify(surface) == slugify(canvas):
        surface = canvas          # styled in CSS via color-mix against the canvas
    hairline = hairline or ink
    on_primary = pick('on-primary') or contrast_on(primary)
    cl = luminance(canvas)
    dark = cl is not None and cl < 0.35
    return dict(canvas=canvas, ink=ink, surface=surface, hairline=hairline,
                primary=primary, on_primary=on_primary, dark=dark)


def derive_opposite(t, b):
    """Counterpart palette for the flip side of the brand's own canvas."""
    lums = [(luminance(v), v) for _, v, *_ in t['colors'] if luminance(v) is not None]
    if not lums:
        return None
    want_dark = not b['dark']

    def opaque(v):                       # a translucent overlay can never be the page canvas
        m = re.match(r'(?:rgba|hsla)\(\s*[\d.]+%?\s*[, ]\s*[\d.]+%?\s*[, ]\s*[\d.]+%?\s*[,/]\s*([\d.]+%?)', v.strip())
        if not m:
            return True
        a = m.group(1)
        return (float(a.rstrip('%')) / 100 if a.endswith('%') else float(a)) >= 0.95

    solid = [(l, v) for l, v in lums if opaque(v)] or lums
    lums = solid

    def neutral(v):
        rgb = hex_to_rgb(v)
        return rgb is not None and (max(rgb) - min(rgb)) < 28

    # the flipped canvas has to actually land on the wanted side; brands with only light
    # neutrals get a synthetic dark rather than a washed-out "darkest" grey
    pool = [v for _, v in lums if neutral(v)] or [v for _, v in lums]
    if want_dark:
        canvas = next((v for v in sorted(pool, key=luminance) if luminance(v) < 0.22), '#0b0b0c')
    else:
        canvas = next((v for v in sorted(pool, key=luminance, reverse=True)
                       if luminance(v) > 0.78), '#ffffff')
    ranked = sorted(((contrast_ratio(v, canvas), v) for _, v in lums
                     if slugify(v) != slugify(canvas)), reverse=True)
    neutrals = [v for r, v in ranked if r >= 4.5 and neutral(v)]
    ink = (neutrals or [v for r, v in ranked if r >= 4.5]
           or (['#f5f5f7'] if want_dark else ['#0a0a0a']))[0]
    return {'canvas': canvas, 'ink': ink, 'surface': None, 'hairline': None,
            'dark': want_dark}


def chrome_vars(canvas, ink, surface=None, hairline=None):
    """The four page-chrome variables, with mixes used whenever the brand gives no explicit token."""
    surface = surface if surface and slugify(surface) != slugify(canvas) \
        else f'color-mix(in srgb, {canvas} 82%, {ink} 18%)'
    hairline = hairline or f'color-mix(in srgb, {canvas} 74%, {ink} 26%)'
    return [('canvas', canvas), ('ink', ink), ('surface', surface), ('hairline', hairline)]


def base_font(t):
    counts = {}
    for v in t['typography'].values():
        f = (v.get('fontFamily') or '').split(',')[0].strip()
        if f:
            counts[f] = counts.get(f, 0) + 1
    if counts:
        return max(counts.items(), key=lambda kv: kv[1])[0]
    if t['fonts']:
        return t['fonts'][0]
    return 'system-ui'


# ---------------------------------------------------------------- rendering
def esc(s):
    return html.escape(str(s or ''))


# Shared by every page, generated or ported: the corner toggle and the theme plumbing that keeps
# the gallery, the ?theme= query and the iframe in sync.
THEME_TOGGLE = ('<button class="theme-toggle" id="themeToggle" type="button" '
                'aria-label="Switch light or dark">☾</button>')
THEME_SCRIPT = '''<script>
(function () {
  var root = document.documentElement, btn = document.getElementById('themeToggle');
  var chip = document.getElementById('themeChip');
  var native = root.dataset.native || 'light';
  // two controls, one state: the generated pages carry the corner button, the ported ones carry
  // the hero chip, and each is labelled with what a click gets you
  function paint(t) {
    if (btn) btn.textContent = t === 'dark' ? '\\u2600' : '\\u263e';
    if (chip) chip.textContent = t === 'dark' ? 'Light Preview' : 'Dark Preview';
  }
  function apply(t, persist) {
    if (t !== 'light' && t !== 'dark') t = native;
    root.dataset.theme = t;
    paint(t);
    if (persist) { try { localStorage.setItem('design-md:theme', t); } catch (e) {} }
    try {
      if (window.parent && window.parent !== window)
        window.parent.postMessage({ type: 'design-md:theme', theme: t, from: 'preview' }, '*');
    } catch (e) {}
  }
  var m = /[?&#]theme=(light|dark)/.exec(location.href);
  var s = null;
  try { s = localStorage.getItem('design-md:theme'); } catch (e) {}
  apply(m ? m[1] : (s || native), false);
  function flip() { apply(root.dataset.theme === 'dark' ? 'light' : 'dark', true); }
  btn && btn.addEventListener('click', flip);
  chip && chip.addEventListener('click', flip);
  addEventListener('keydown', function (e) {
    var el = e.target || {};
    if (e.key === 't' && !/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName || '')) {
      e.preventDefault();
      apply(root.dataset.theme === 'dark' ? 'light' : 'dark', true);
    }
  });
  addEventListener('message', function (e) {
    var d = e.data;
    if (d && d.type === 'design-md:theme' && d.from !== 'preview') apply(d.theme, false);
  });
})();
</script>'''
NAV_SCRIPT = '''<script>
(function () {
  var nav = document.querySelector('.nav');
  var panel = document.getElementById('navPanel');
  if (!nav || !panel) return;
  var menus = {};
  [].slice.call(panel.querySelectorAll('.flyout-menu')).forEach(function (m) {
    menus[m.getAttribute('data-for')] = m;
  });
  function show(id) {
    [].slice.call(panel.querySelectorAll('.flyout-menu')).forEach(function (m) {
      if (m.getAttribute('data-for') === id) { m.removeAttribute('hidden'); }
      else { m.setAttribute('hidden', ''); }
    });
    nav.classList.add('nav-open');
  }
  function close() { nav.classList.remove('nav-open'); }
  [].slice.call(nav.querySelectorAll('.nav-item')).forEach(function (li) {
    var id = li.getAttribute('data-menu');
    if (!menus[id]) return;
    li.addEventListener('mouseenter', function () { show(id); });
    li.addEventListener('focusin', function () { show(id); });
  });
  nav.addEventListener('mouseleave', close);
  // a click on a menu entry is the end of the interaction: close, then let the anchor jump
  panel.addEventListener('click', function (e) { if (e.target.closest('a')) close(); });
  addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
})();
</script>'''
THEME_TOGGLE_CSS = '''.theme-toggle {
  position: fixed; right: 20px; bottom: 20px; z-index: 90;
  width: 38px; height: 38px; display: flex; align-items: center; justify-content: center;
  font: inherit; font-size: 15px; line-height: 1; cursor: pointer;
  color: var(--ink); background: var(--surface);
  border: 1px solid var(--hairline); border-radius: 999px;
  box-shadow: var(--elev); opacity: .7;
  transition: opacity 200ms ease, transform 200ms ease;
}
.theme-toggle:hover { opacity: 1; transform: translateY(-1px); }
'''

# Rules for the sections our pages have and theirs do not (component specimens, guidelines,
# the reference table, the hero's token chips). Two variables per theme bridge the gap, so the
# adapter follows whichever skin is active without repeating itself.
#
# Split in two on purpose: the variable blocks are already theme-scoped, while the rules have to be
# emitted once under each theme prefix. Their skin selectors are scoped too, so an unscoped
# `.color-swatch-block` here loses to `html[data-theme="light"] .color-swatch-block` and the
# override silently does nothing — only properties they never set would appear to apply.
# The variable half of the adapter, per brand. `--ad-ink` and `--ad-font` exist because the
# rules below are shared: apple's own ink/font variables are --gray-80 and --font-text, binance's
# are --text and --font-sans, so the rules name the adapter's pair and each brand fills them in
# with the variable it actually has. Every value is that brand's own — nothing is invented here.
def verify_palette(slug, html, tokens):
    """Every colour token in the DESIGN.md has to be on the page, exactly once.

    Restructuring the palette is exactly the edit that drops one silently — twenty-four swatches
    look like twenty-three — so it is asserted at build time instead of eyeballed. The check reads
    the emitted markup rather than the loop that wrote it, so it catches a lost colour whichever
    way it was lost.
    """
    if len(re.findall(r'<div class="swatch">', html)) != len(tokens):
        raise ValueError(f'{slug}: palette drew '
                         f'{len(re.findall(r"<div class=.swatch.>", html))} swatches for '
                         f'{len(tokens)} tokens')


BUCKET_PAT = {
    'buttons': r'(?:^|-)(?:button|btn|cta)(?:-|$)',
    'forms': r'(?:^|-)(?:input|field|form|search|select|picker|checkbox|radio|toggle|'
             r'textarea|combobox|slider|switch)(?:-|$)',
    'badges': r'(?:^|-)(?:badge|pill|tag|chip|ribbon|label)(?:-|$)',
    'cards': r'(?:^|-)(?:card|panel|pricing|hero|feature|product|testimonial|tile|mockup|'
             r'promo|banner)(?:-|$)',
    'nav': r'(?:^|-)(?:nav|tab|segmented|link|menu|side|header|breadcrumb|toolbar|footer)(?:-|$)',
}
# Earlier buckets win a key that fits several, so the most specific noun is listed first.
BUCKET_TITLES = [('buttons', 'Button Variants'), ('badges', 'Badges & Pills'),
                 ('cards', 'Cards & Containers'), ('forms', 'Forms & Inputs'),
                 ('nav', 'Navigation & Tabs'), ('other', 'Other Components')]


def component_buckets(comps):
    buckets = {bid: [(k, v) for k, v in comps.items() if re.search(pat, k.lower())]
               for bid, pat in BUCKET_PAT.items()}
    used = set(sum(([k for k, _ in v] for v in buckets.values()), []))
    buckets['other'] = [(k, v) for k, v in comps.items() if k not in used]
    return buckets


def token_vars(t):
    """Brand tokens as custom properties — component specimens reference these from inline styles."""
    out = [f'  --c-{slugify(k)}: {v};' for k, v, *_ in t['colors']]
    for k, v in t['typography'].items():
        out += [f'  --t-{slugify(k)}-size: {v.get("fontSize", "16px")};',
                f'  --t-{slugify(k)}-weight: {v.get("fontWeight", "400")};',
                f'  --t-{slugify(k)}-lh: {v.get("lineHeight", "1.5")};',
                f'  --t-{slugify(k)}-ls: {v.get("letterSpacing", "normal")};']
    out += [f'  --r-{slugify(k)}: {v};' for k, v in t['rounded'].items()]
    out += [f'  --s-{slugify(k)}: {v};' for k, v in t['spacing'].items()]
    return out


def resolve_literal(v, t):
    """Like resolve(), but substitutes the token's actual value — for prose, not for CSS."""
    def rep(m):
        parts = m.group(1).split('.', 1)
        kind, key = parts[0], (parts[1] if len(parts) > 1 else '')
        if kind == 'colors':
            for name, val, *_ in t['colors']:
                if slugify(name) == slugify(key):
                    return val
        elif kind == 'rounded':
            for name, val in t['rounded'].items():
                if slugify(name) == slugify(key):
                    return val
        elif kind == 'spacing':
            for name, val in t['spacing'].items():
                if slugify(name) == slugify(key):
                    return val
        elif kind == 'typography':
            for name, spec in t['typography'].items():
                if slugify(name) == slugify(key):
                    return f"{spec.get('fontSize', '')}/{spec.get('fontWeight', '')}"
        return m.group(0)
    return re.sub(r'\{([^}]+)\}', rep, str(v))


SUMMARY_LABEL = {'background': 'bg', 'color': 'text', 'border-radius': 'radius',
                 'padding': 'padding', 'border': 'border', 'box-shadow': 'shadow',
                 'font-size': 'font-size', 'width': 'size', 'height': 'size'}


SWATCH_RE = re.compile(
    r'<div class="color-group-label">([^<]+)</div>'
    r'|<div class="color-swatch-block" style="background:([^";]+)[^"]*"></div>'
    r'<div class="color-swatch-info"><div class="color-swatch-name">([^<]*)</div>'
    r'<div class="color-swatch-hex">([^<]*)</div><div class="color-swatch-role">([^<]*)</div>')


COLOUR_CATS = [
    ('Text', r'^on-'),          # "on-dark" is text that sits on a colour, not a dark surface
    # A status label is semantic whatever else its name says, so this is anchored at the start:
    # badge-text is a status, surface-chip-translucent is a surface.
    ('Semantic', r'^(?:badge|tag|pill|chip|ribbon|status)(?:$|-)'),
    ('Primary', r'(^|-)primary(?:$|-)'),
    ('Body', r'(^|-)body(?:$|-)'),
    # A line is a line whatever it is a line on, so this is tested before Text — otherwise the
    # on-dark/on-light rule below reads hairline-on-dark as text. Its "line" also covers hairline,
    # which is why there is no separate Hairline bucket.
    ('Border', r'border|divider|stroke|separator|outline|rule|line'),
    # body-on-dark is dark-page *text*, not a dark surface — ahead of the dark rule for that reason
    ('Text', r'ink|text|foreground|copy|caption|label|muted|faded|subtle|dim'
             r'|(^|-)on-(?:dark|light)(?:$|-)'),
    # One surface bucket here — canvas included, dark words included — because the light/dark
    # split is by the colour's own lightness, not by its name (binance names canvas-dark, apple's
    # surface-tile-1 is dark without saying so). colour_category() makes that split.
    ('Surface', r'canvas|background|(^|-)bg(?:$|-)|surface|card|panel|tile|parchment|pearl'
                r'|elevation|sheet|dark|black|night|deep|shadow|scrim|overlay|void'),
    ('Accent', r'accent|brand|turquoise'),
    ('Semantic', r'error|danger|negative|critical|success|positive|warning|caution|info|announce'
                 r'|trading|(^|-)up(?:$|-)|(^|-)down(?:$|-)'
                 r'|link|focus|hover|active|press|visited|selected|disabled'),
]
CAT_ORDER = ['Primary', 'Body', 'Text', 'Surface Light', 'Surface Dark', 'Border', 'Accent',
             'Semantic']

ROLE_HINTS = [
    (r'^on-', 'Text and icons placed on this colour'),
    (r'hairline|border|divider|stroke|separator|outline', 'Borders, dividers and separators'),
    (r'error|danger|negative|critical', 'Errors and destructive actions'),
    (r'success|positive', 'Success and confirmation'),
    (r'warning|caution', 'Warnings and caution'),
    (r'info|announce', 'Informational states'),
    (r'trading-up|(^|-)up(?:$|-)', 'Price-up and positive movement'),
    (r'trading-down|(^|-)down(?:$|-)', 'Price-down and negative movement'),
    (r'(^|-)disabled', 'Disabled and inactive states'),
    # anchored like the category rule above, so surface-chip-translucent reads as the surface it
    # is rather than as a badge
    (r'^(?:badge|tag|pill|chip|ribbon)', 'Product-tile badges and status labels'),
    (r'link|focus|hover|active|press|selected', 'Interactive, focus and press states'),
    (r'primary|brand|accent|cta', 'Primary actions and brand accents'),
    (r'canvas|background|(^|-)bg', 'Page and section background'),
    (r'surface|card|panel|tile|parchment|pearl', 'Cards, panels and elevated surfaces'),
    (r'dark|black|night|deep', 'Dark sections and deep surfaces'),
    (r'muted|faded|subtle|dim', 'Secondary and subdued text'),
    (r'ink|text|body|foreground|copy|caption|label', 'Text and content'),
]


def colour_category(name, val=None):
    """Which group a token's colour belongs to — the page's group name, ready to print.

    No 'Other' bucket: a colour we cannot place is a colour we have not understood yet, and it
    belongs with the semantics rather than parked off the end of the palette.

    The two surface groups are split by the colour's own lightness rather than by its name, so
    that a brand which does not spell it out still lands right: apple's `surface-tile-1` is #272729
    and reads as dark, while binance's `canvas-light` says so and is #ffffff.
    """
    n = slugify(name)
    for cat, pat in COLOUR_CATS:
        if re.search(pat, n):
            if cat != 'Surface':
                return cat
            lum = luminance(val) if val else None
            if lum is None:                       # rgba() / color-mix(): fall back to the name
                return ('Surface Dark' if re.search(r'dark|black|night', n)
                        else 'Surface Light')
            return 'Surface Dark' if lum < 0.4 else 'Surface Light'
    return 'Semantic'


def role_hint(name):
    n = slugify(name)
    for pat, txt in ROLE_HINTS:
        if re.search(pat, n):
            return txt
    return 'System colour'


def pretty_name(name):
    """'ink-muted-80' -> 'Ink Muted 80'."""
    out = []
    for w in re.split(r'[-_\s]+', str(name)):
        if not w:
            continue
        out.append(w if '0' <= w[0] <= '9' else w.capitalize())
    return ' '.join(out)


def display_name(t):
    """DESIGN.md titles carry boilerplate ("Apple-design-analysis"); the brand name is the point."""
    return re.sub(r'[-\s]*(?:inspired[-\s]*)?(?:design[-\s]?(?:analysis|system|md))\s*$', '',
                  t['name'], flags=re.I).strip() or t['name']


def spec_style(props, t):
    """Inline CSS for a specimen: the component's own properties plus a readable box."""
    style = clamp_padding(props_to_style(props, t))
    tspec = typo_lookup(props, t)
    if tspec:
        style += (f';font-size:{min(px(tspec.get("fontSize", "14px"), 14), 28):g}px'
                  f';font-weight:{tspec.get("fontWeight", "500")}')
    boxed = bool(re.search(r'background:(?!\s*transparent)', style)) or has_visible_border(style)
    return style, props_summary(props, t), boxed


def props_summary(props, t, limit=3):
    """A one-line, human-readable digest of a component's properties for a card or state label.

    Values are resolved to what the token actually is ("bg #0066cc"), not to the var() that the
    inline style uses — the summary is read, the inline style is executed.
    """
    bits = []
    for k, v in props.items():
        key = slugify(k).replace('-', '')
        tgt = PROP_MAP.get(key)
        if tgt == 'size':
            tgt = 'width'
        label = SUMMARY_LABEL.get(tgt)
        if not label:
            continue
        val = resolve_literal(tidy_value(v), t)
        if not css_safe(k, val):
            continue
        bits.append(f'{label} {val}')
        if len(bits) >= limit:
            break
    return ' · '.join(bits)


def type_class_css(t):
    """A class per typography token, so a sample carries `.type-<token>` instead of a long style.

    The sample size is clamped the same way the two builders clamp it, so the classes reproduce
    exactly what the inline styles did.
    """
    out = []
    for k, v in t['typography'].items():
        sample = min(px(v.get('fontSize', '16px'), 16), 60)
        fam = v.get('fontFamily') or 'var(--font)'
        out.append(f'.type-{slugify(k)} {{ font-family: {fam}; font-size: {sample:g}px; '
                   f'font-weight: {v.get("fontWeight", "400")}; '
                   f'line-height: {v.get("lineHeight", "1.4")}; '
                   f'letter-spacing: {v.get("letterSpacing", "normal")}; }}')
    return out


# ------------------------------------------------- what used to be inline styles
# Every declaration our markup carries is a class instead, so a page has no bare style="" left.
STYLE_ATTR_RE = re.compile(r'\sstyle="([^"]*)"')


def specimen_classes(t, comps):
    """One class per component specimen. Returns (rules, {component: class})."""
    rules, names = [], {}
    for k, props in comps.items():
        style, _, _ = spec_style(props, t)
        names[k] = f'spec-{slugify(k)}'
        if style:
            rules.append(f'.{names[k]} {{ {style} }}')
    return rules, names


def shadow_is_css(v):
    """Whether a DESIGN.md "shadow" is actually a shadow.

    Some files describe the level instead of specifying it — airtable's are "1px {colors.hairline}
    border" and "Outer 2px blue ring at higher alpha". A browser drops an invalid box-shadow
    silently, so those levels are drawn flat and their description carries the meaning.
    """
    v = str(v)
    v = re.sub(r'var\(--[a-z0-9-]+\)', ' ', v)
    v = re.sub(r'#[0-9a-fA-F]{3,8}', ' ', v)
    v = re.sub(r'\b(?:rgba?|hsla?|color-mix|inset|none|solid)\b', ' ', v)
    v = re.sub(r'\b\d*\.?\d+(?:px|rem|em|%|vw|vh)?\b', ' ', v)
    return not re.search(r'[a-zA-Z]{2,}', v)


def style_classes(t, b):
    """Colour swatches, spacing widths and radius boxes as classes, for both build paths."""
    out = []
    for k, v, *_ in t['colors']:
        out.append(f'.sw-{slugify(k)} {{ background: {v}; color: {contrast_on(v)}; }}')
    items = sorted(t['spacing'].items(), key=lambda kv: px(kv[1]))
    mx = max((px(v) for _, v in items), default=1) or 1
    for k, v in items:
        out.append(f'.bar-{slugify(k)} {{ width: {max(px(v) / mx * 100, 1):.1f}%; }}')
    for k, v in t['rounded'].items():
        r = v if 'px' in v or '%' in v else v + 'px'
        out.append(f'.rd-{slugify(k)} {{ border-radius: {r}; }}')
    for nm, val, _ in t['shadows'][:12]:
        out.append(f'.elev-{slugify(nm)} {{ box-shadow: {val}; }}')
    return out


def build_css(t, b, font):
    L = []
    A = L.append
    A('/* tokens */')
    A(':root {')
    for line in token_vars(t):
        A(line)
    A(f'  --font: {font}, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;')
    for name, val in chrome_vars(b['canvas'], b['ink'], b['surface'], b['hairline']):
        A(f'  --{name}: {val};')
    A(f'  --primary: {b["primary"]};')
    A(f'  --on-primary: {b["on_primary"]};')
    A(f'  --elev: {"0 1px 2px rgba(255,255,255,.06)" if b["dark"] else "0 1px 2px rgba(16,24,40,.06)"};')
    A('}')

    # the same four chrome variables, resolved for whichever side of the brand palette is not native
    opp = derive_opposite(t, b)
    A('')

    A('/* page chrome per theme — the brand palette itself is never altered */')
    for mode, c in (('light', b if not b['dark'] else opp), ('dark', b if b['dark'] else opp)):
        if not c:
            continue
        A(f'html[data-theme="{mode}"] {{')
        for name, val in chrome_vars(c['canvas'], c['ink'], c.get('surface'), c.get('hairline')):
            A(f'  --{name}: {val};')
        A(f'  --elev: {"0 1px 2px rgba(255,255,255,.06)" if c["dark"] else "0 1px 2px rgba(16,24,40,.06)"};')
        A('}')

    A('''
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: var(--font); background: var(--canvas); color: var(--ink);
  line-height: 1.5; -webkit-font-smoothing: antialiased;
}
a { color: inherit; }
.page { max-width: 1200px; margin: 0 auto; padding: 0 32px 96px; }

.topbar {
  position: sticky; top: 0; z-index: 50; display: flex; align-items: center;
  justify-content: space-between; gap: 24px; padding: 14px 0; margin-bottom: 8px;
  background: color-mix(in srgb, var(--canvas) 88%, transparent);
  backdrop-filter: blur(12px); border-bottom: 1px solid var(--hairline);
}
.topbar-name { font-weight: 700; font-size: 15px; letter-spacing: -.2px; }
.topbar-meta { font-size: 12px; opacity: .6; }
.topbar-links { display: flex; gap: 14px; font-size: 12px; font-weight: 600; opacity: .75; flex-wrap: wrap; }
.topbar-links a { text-decoration: none; }

.hero { padding: 72px 0 56px; }
.hero h1 { font-size: clamp(34px, 5vw, 64px); font-weight: 700; letter-spacing: -1.6px; line-height: 1.06; }
.hero .lede { margin-top: 20px; max-width: 72ch; font-size: 17px; line-height: 1.62; opacity: .78; }
.hero .meta { margin-top: 28px; display: flex; flex-wrap: wrap; gap: 10px; }
.chip {
  font-size: 12px; font-weight: 600; padding: 6px 12px; border-radius: 999px;
  border: 1px solid var(--hairline); background: var(--surface);
}
.chip.solid { background: var(--primary); color: var(--on-primary); border-color: transparent; }

section { padding: 56px 0 8px; border-top: 1px solid var(--hairline); margin-top: 24px; }
section:first-of-type { border-top: none; }
.sec-head { display: flex; align-items: baseline; justify-content: space-between; gap: 20px; margin-bottom: 28px; }
.sec-head h2 { font-size: 26px; font-weight: 700; letter-spacing: -.7px; }
.sec-head .count { font-size: 12px; opacity: .55; font-weight: 600; }
.sec-note { font-size: 14px; opacity: .65; margin: -14px 0 24px; max-width: 70ch; }

.grid { display: grid; gap: 16px; }
.g-colors { grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); }
.g-cards { grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }
.g-3 { grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); }

.swatch { border: 1px solid var(--hairline); border-radius: 12px; overflow: hidden; background: var(--surface); }
.swatch .fill { height: 92px; display: flex; align-items: flex-end; padding: 10px; font-size: 11px; font-weight: 700; }
.swatch .info { padding: 10px 12px 12px; }
.swatch .nm { font-size: 13px; font-weight: 600; letter-spacing: -.1px; }
.swatch .hx { font-size: 11px; opacity: .6; margin-top: 3px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.swatch .hx.dim { opacity: .5; }
.group-title { font-size: 13px; font-weight: 700; opacity: .6; text-transform: uppercase; letter-spacing: .08em; margin: 26px 0 12px; }

.type-row { display: grid; grid-template-columns: 220px 1fr; gap: 20px; align-items: baseline; padding: 16px 0; border-bottom: 1px solid var(--hairline); }
.type-row:last-child { border-bottom: none; }
.type-meta { font-size: 11px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; opacity: .62; line-height: 1.7; }
.type-meta b { display: block; font-family: var(--font); font-size: 13px; letter-spacing: -.1px; opacity: .95; }
.type-sample { overflow: hidden; text-overflow: ellipsis; }

.bar-row { display: grid; grid-template-columns: 150px 90px 1fr; gap: 16px; align-items: center; padding: 7px 0; font-size: 12px; }
.bar-row .bar { height: 14px; border-radius: 3px; background: var(--primary); opacity: .85; }
.bar-row .val { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; opacity: .65; }

.radius-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 14px; }
.radius-cell { text-align: center; }
.radius-cell .box { height: 84px; background: var(--surface); border: 1px solid var(--hairline); margin-bottom: 8px; }
.radius-cell .lb { font-size: 11px; opacity: .7; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }

.elev-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 20px; }
.elev-cell { background: var(--canvas); border-radius: 12px; padding: 20px; min-height: 104px; display: flex; flex-direction: column; justify-content: flex-end; font-size: 12px; }
.elev-cell .lb { font-weight: 600; }
.elev-cell .vl { opacity: .6; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 10px; margin-top: 4px; word-break: break-word; }

.demo { border: 1px solid var(--hairline); border-radius: 14px; background: var(--surface); padding: 20px; }
.demo-row { display: flex; flex-wrap: wrap; gap: 14px; align-items: flex-start; }
.demo-col { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.demo-col .lb { font-size: 11px; opacity: .6; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
/* Neutral stand-in so a component reads as a component; every inline property from the source
   overrides the matching declaration here. */
.demo-el { display: inline-block; box-sizing: border-box; font-family: var(--font); font-size: 13px;
           line-height: 1.35; text-align: left; background: var(--canvas); color: var(--ink);
           border: 1px solid var(--hairline); border-radius: 8px; padding: 9px 16px; }
.demo-el-h { font-weight: 600; font-size: 13px; }
.demo-el-b { opacity: .6; font-size: 11px; }
div.demo-el-b { margin-top: 4px; }
button.demo-el { cursor: default; appearance: none; }
.demo-el-ghost { outline: 1px dashed var(--hairline); outline-offset: 0; }
.comp-name { font-size: 11px; font-weight: 600; opacity: .55; margin-bottom: 8px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }

table.ref { width: 100%; border-collapse: collapse; font-size: 12px; }
table.ref th, table.ref td { text-align: left; padding: 9px 12px; border-bottom: 1px solid var(--hairline); vertical-align: top; }
table.ref th { font-size: 10px; text-transform: uppercase; letter-spacing: .08em; opacity: .55; font-weight: 700; }
table.ref td { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; opacity: .85; }
table.ref td.k { font-family: var(--font); font-weight: 600; opacity: 1; }

.guide { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.guide ul { list-style: none; }
.guide li { position: relative; padding-left: 18px; margin-bottom: 10px; font-size: 14px; line-height: 1.55; opacity: .85; }
.guide li::before { position: absolute; left: 0; font-weight: 700; }
.guide .yes li::before { content: "+"; }
.guide .no li::before { content: "\\2212"; }

footer { margin-top: 64px; padding-top: 24px; border-top: 1px solid var(--hairline); font-size: 12px; opacity: .6; display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; }

''' + THEME_TOGGLE_CSS + '''

@media (max-width: 760px) {
  .page { padding: 0 20px 64px; }
  .type-row { grid-template-columns: 1fr; gap: 6px; }
  .bar-row { grid-template-columns: 96px 70px 1fr; }
  .guide { grid-template-columns: 1fr; }
  .hero { padding: 48px 0 40px; }
}
''')
    A('')
    A('/* one class each for the type scale, swatches, bars, radius boxes, elevation and specimens */')
    for rule in type_class_css(t) + style_classes(t, b) + specimen_classes(t, t['components'])[0]:
        A(rule)
    return '\n'.join(L)


def build_html(t, b, font, slug):
    A = []
    A.append('')
    A.append('<div class="page">')
    A.append('  <header class="topbar">')
    A.append(f'    <div><div class="topbar-name">{esc(t["name"])}</div>'
             f'<div class="topbar-meta">design tokens · {len(t["colors"])} colors · '
             f'{len(t["typography"])} type styles · {len(t["components"])} components</div></div>')
    # Filled in once the sections are built: a hardcoded list left dead anchors on the 29 pages
    # that have no forms / cards / elevation section for it to point at.
    A.append('    <nav class="topbar-links">@@NAV@@</nav>')
    A.append('  </header>')

    A.append('  <section class="hero">')
    A.append(f'    <h1>{esc(t["name"])}</h1>')
    if t['description']:
        A.append(f'    <p class="lede">{esc(t["description"])}</p>')
    A.append('    <div class="meta">')
    A.append(f'      <span class="chip solid">{esc(b["primary"])}</span>')
    A.append(f'      <span class="chip">{esc(font)}</span>')
    A.append(f'      <span class="chip">{"dark" if b["dark"] else "light"} canvas</span>')
    A.append(f'      <span class="chip">source: DESIGN.md ({esc(t.get("source", ""))})</span>')
    A.append('    </div>')
    A.append('  </section>')

    # -------- colors
    if t['colors']:
        A.append('  <section id="colors">')
        A.append('    <div class="sec-head"><h2>Color Palette</h2>'
                 f'<span class="count">{len(t["colors"])} tokens</span></div>')
        groups = t['groups'] or [('Colors', t['colors'])]
        first = True
        for gname, gitems in groups:
            if not gitems:
                continue
            if not first:
                A.append(f'    <div class="group-title">{esc(gname)}</div>')
            first = False
            A.append('    <div class="grid g-colors">')
            for item in gitems:
                nm, val = item[0], item[1]
                desc = item[2] if len(item) > 2 else ''
                A.append(f'      <div class="swatch"><div class="fill sw-{slugify(nm)}">{esc(val)}</div>'
                         f'<div class="info"><div class="nm">{esc(nm)}</div>'
                         f'<div class="hx">{esc(slugify(nm))}</div>'
                         + (f'<div class="hx dim">{esc(desc[:70])}</div>' if desc else '')
                         + '</div></div>')
            A.append('    </div>')
        A.append('  </section>')
        verify_palette(slug, '\n'.join(A), t['colors'])

    # -------- typography
    if t['typography']:
        A.append('  <section id="typography">')
        A.append('    <div class="sec-head"><h2>Typography Scale</h2>'
                 f'<span class="count">{len(t["typography"])} styles</span></div>')
        for k, v in t['typography'].items():
            size = v.get('fontSize', '16px')
            A.append('    <div class="type-row">')
            A.append(f'      <div class="type-meta"><b>{esc(v.get("name", k))}</b>'
                     f'{esc(size)} / {esc(v.get("fontWeight", "400"))}<br>'
                     f'lh {esc(v.get("lineHeight", "1.4"))} · ls {esc(v.get("letterSpacing", "normal"))}<br>'
                     f'{esc(v.get("fontFamily", ""))}</div>')
            A.append(f'      <div class="type-sample type-{slugify(k)}">'
                     f'{esc(v.get("name", k))} — The quick brown fox jumps over the lazy dog</div>')
            A.append('    </div>')
        A.append('  </section>')

    comps = t['components']
    buckets = component_buckets(comps)

    def comp_cell(k, props, bid):
        """One component: caption = its name, box = something shaped like the thing itself."""
        style = clamp_padding(props_to_style(props, t))
        tspec = typo_lookup(props, t)
        if tspec:
            style += (f';font-size:{min(px(tspec.get("fontSize", "14px"), 14), 34):g}px'
                      f';font-weight:{tspec.get("fontWeight", "500")}')
        # A component that states no background and no visible border would render as loose text;
        # a dashed outline shows its real extent without inventing a fill the source never had.
        boxed = bool(re.search(r'background:(?!\s*transparent)', style)) or has_visible_border(style)
        if bid == 'cards':
            inner = ('<div class="demo-el-h">Card</div>'
                     '<div class="demo-el-b">Body copy sits inside the padding.</div>')
        elif bid == 'forms':
            inner = '<span class="demo-el-b">Placeholder text</span>'
        elif bid == 'nav':
            inner = ('<span class="demo-el-h">Home</span>&nbsp;&nbsp;'
                     '<span class="demo-el-b">Docs</span>&nbsp;&nbsp;'
                     '<span class="demo-el-b">Pricing</span>')
        elif bid == 'buttons':
            inner = 'Button'
        elif bid == 'badges':
            inner = 'Badge'
        else:
            inner = esc(comp_label(k))
        # the specimen's own properties live in .spec-<name>; only the ghost modifier is inline here
        cls = ('demo-el ' if boxed else 'demo-el demo-el-ghost ') + f'spec-{slugify(k)}'
        tag = 'button' if bid == 'buttons' else 'div'
        extra = ' type="button"' if tag == 'button' else ''
        return (f'      <div class="demo-col">'
                f'<div class="lb" title="{esc(k)}">{esc(comp_label(k))}</div>'
                f'<{tag} class="{cls}"{extra}>{inner}</{tag}></div>')

    for bid, title in BUCKET_TITLES:
        items = buckets.get(bid) or []
        if not items:
            continue
        A.append(f'  <section id="{bid if bid != "other" else "signature"}">')
        A.append(f'    <div class="sec-head"><h2>{title}</h2><span class="count">{len(items)}</span></div>')
        A.append('    <div class="demo"><div class="demo-row">')
        for k, props in items[:24]:
            A.append(comp_cell(k, props, bid))
        A.append('    </div></div>')
        A.append('  </section>')

    # -------- spacing
    if t['spacing']:
        A.append('  <section id="spacing">')
        A.append('    <div class="sec-head"><h2>Spacing Scale</h2>'
                 f'<span class="count">{len(t["spacing"])} steps</span></div>')
        items = sorted(t['spacing'].items(), key=lambda kv: px(kv[1]))
        mx = max((px(v) for _, v in items), default=1) or 1
        for k, v in items:
            A.append(f'    <div class="bar-row"><span>{esc(k)}</span><span class="val">{esc(v)}</span>'
                     f'<span class="bar bar-{slugify(k)}"></span></div>')
        A.append('  </section>')

    # -------- radius
    if t['rounded']:
        A.append('  <section id="radius">')
        A.append('    <div class="sec-head"><h2>Border Radius Scale</h2>'
                 f'<span class="count">{len(t["rounded"])} steps</span></div>')
        A.append('    <div class="radius-grid">')
        for k, v in t['rounded'].items():
            r = v if 'px' in v or '%' in v else v + 'px'
            A.append(f'      <div class="radius-cell"><div class="box rd-{slugify(k)}"></div>'
                     f'<div class="lb">{esc(k)} · {esc(v)}</div></div>')
        A.append('    </div>')
        A.append('  </section>')

    # -------- elevation
    if t['shadows']:
        A.append('  <section id="elevation">')
        A.append('    <div class="sec-head"><h2>Elevation &amp; Depth</h2>'
                 f'<span class="count">{len(t["shadows"])}</span></div>')
        A.append('    <div class="elev-grid">')
        for nm, val, desc in t['shadows'][:12]:
            A.append(f'      <div class="elev-cell elev-{slugify(nm)}">'
                     f'<div class="lb">{esc(nm)}</div><div class="vl">{esc(val[:64])}</div></div>')
        A.append('    </div>')
        A.append('  </section>')

    # -------- guidelines
    if t['do'] or t['dont']:
        A.append('  <section id="guidelines">')
        A.append('    <div class="sec-head"><h2>Do&rsquo;s &amp; Don&rsquo;ts</h2></div>')
        A.append('    <div class="guide">')
        for cls, items in (('yes', t['do']), ('no', t['dont'])):
            A.append(f'      <ul class="{cls}">')
            for it in items:
                A.append(f'        <li>{esc(it)}</li>')
            A.append('      </ul>')
        A.append('    </div>')
        A.append('  </section>')

    # -------- reference table
    if comps:
        A.append('  <section id="reference">')
        A.append('    <div class="sec-head"><h2>Component Reference</h2>'
                 f'<span class="count">{len(comps)}</span></div>')
        A.append('    <table class="ref"><thead><tr><th>Component</th><th>Resolved properties</th></tr></thead><tbody>')
        for k, props in list(comps.items())[:60]:
            A.append(f'      <tr><td class="k">{esc(k)}</td><td>'
                     + esc('; '.join(f'{kk}: {resolve(vv, t)}' for kk, vv in props.items()))
                     + '</td></tr>')
        A.append('    </tbody></table>')
        A.append('  </section>')

    A.append(f'  <footer><span>{esc(t["name"])} — design tokens extracted from DESIGN.md</span>'
             f'<span>awesome-design-md / getdesign.md</span></footer>')
    A.append('</div>')
    A.append('')
    A.append(THEME_TOGGLE)
    A.append(THEME_SCRIPT)
    doc = '\n'.join(A)
    present = set(re.findall(r'<section id="([^"]+)"', doc))
    NAV = [('colors', 'Colors'), ('typography', 'Type'), ('buttons', 'Buttons'),
           ('badges', 'Badges'), ('cards', 'Cards'), ('forms', 'Forms'), ('nav', 'Tabs'),
           ('spacing', 'Spacing'), ('radius', 'Radius'), ('elevation', 'Depth'),
           ('signature', 'Other'), ('reference', 'Reference')]
    return doc.replace('@@NAV@@',
                       ''.join(f'<a href="#{i}">{lbl}</a>' for i, lbl in NAV if i in present))


def _css_chunks(css):
    """Split a stylesheet into (selector, body) pairs; body is None for trailing text."""
    out, i, buf = [], 0, ''
    while i < len(css):
        j = css.find('{', i)
        if j < 0:
            buf += css[i:]
            break
        sel = buf + css[i:j]
        depth, k = 1, j + 1
        while k < len(css) and depth:
            if css[k] == '{':
                depth += 1
            elif css[k] == '}':
                depth -= 1
            k += 1
        out.append((sel.strip(), css[j + 1:k - 1]))
        buf, i = '', k
    if buf.strip():
        out.append((buf.strip(), None))
    return out


def _scoped(css, prefix):
    """Prefix every selector so one stylesheet can carry two skins side by side.

    The two preview files in the CN repo are full copies of each other with different values, so
    the later (dark) block overrides the earlier one property by property and nothing needs merging.
    """
    out = []
    for sel, body in _css_chunks(css):
        if body is None:
            out.append(sel)
            continue
        lead = ''
        m = re.match(r'^((?:\s*/\*.*?\*/\s*)*)(.*)$', sel, re.S)
        if m:
            lead, sel = m.group(1), m.group(2).strip()
        if sel == ':root':
            out.append(f'{lead}{prefix} {{ {body} }}')
        elif sel.startswith('@media'):
            out.append(f'{lead}{sel} {{ {_scoped(body, prefix)} }}')
        else:
            sels = ', '.join(f'{prefix} {p.strip()}' for p in sel.split(','))
            out.append(f'{lead}{sels} {{ {body} }}')
    return '\n'.join(out)


README_NOTE = """
---

> **Local note — awesome-design-md-previews.** {lead} What is actually in this folder:
>
> | file | what it is |
> |---|---|
> | `DESIGN.md` | the upstream design-system doc, also byte-for-byte{correction} |
> | `preview_auto.html` | the page generated from `DESIGN.md`; the viewer's "Auto" mode loads it |
> | `preview_auto.css` | its stylesheet; the webfonts are `url(../fonts/…)` references, not copies |
>
> Regenerate everything with `python3 _generator/build_previews.py` from the folder root.
>
> The getdesign.md links above are documentation, not something to click: this folder carries its
> own copy of every page.
"""


def patch_readme(slug, text, corrected=False, synthetic=False):
    """Append the local addendum. The upstream stub is a bare redirect to getdesign.md, so on its
    own it says nothing about the folder it sits in."""
    correction = (" — carrying a local correction to its global-nav description"
                  if corrected else "")
    if synthetic:
        lead = ("This style ships **no README upstream**, so there is nothing above to quote — "
                "this file exists for the note below.")
    else:
        lead = "Everything above is the upstream README, byte-for-byte."
    return (text.rstrip('\n') + '\n'
            + README_NOTE.format(slug=slug, correction=correction, lead=lead))


def build_page(t, slug, link_fonts=True):
    """link_fonts=False inlines the webfont instead of pointing at ../fonts/."""
    b = derive_base(t)
    font = base_font(t)
    # No remote font <link>: a stylesheet in <head> blocks first paint until the request settles,
    # and Google's host settles only after the OS connect timeout here (~75s of blank page). The
    # brand face is baked into the CSS instead, so the page is offline-complete.
    base = build_css(t, b, font)
    # only the weights this page's own stylesheet asks for, so fonts/ holds nothing unused
    wts = used_font_weights(base)
    css = font_face_css(font, wts, linked=link_fonts) + base
    css_inline = font_face_css(font, wts) + base
    body = build_html(t, b, font, slug)
    # data-theme is written into the markup, not only set by the script: every themed rule keys off
    # it, so a renderer that does not run JavaScript (macOS Quick Look) would otherwise show the
    # page unstyled. The script still overrides it, and browsers get no flash of the wrong skin.
    native = 'dark' if b['dark'] else 'light'
    doc = (f'<!DOCTYPE html>\n<html lang="en" data-native="{native}" data-theme="{native}"><head>\n'
           f'  <meta charset="UTF-8">\n'
           f'  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
           f'  <title>{esc(t["name"])} — Design System Preview</title>\n'
           f'  <link rel="stylesheet" href="preview_auto.css">\n'
           f'</head>\n<body>\n{body}\n</body></html>\n')
    one_file = doc.replace('  <link rel="stylesheet" href="preview_auto.css">\n',
                             '<style>\n' + css_inline + '</style>\n')
    return doc, one_file, css


def _get(url, timeout=45):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = []
    md_copied = [0]
    md_patched = [0]
    for d in sorted(SRC.iterdir()):
        if not d.is_dir() or not (d / 'DESIGN.md').is_file():
            continue
        slug = slugify(d.name)
        try:
            raw_md = (d / 'DESIGN.md').read_text(encoding='utf-8')
            md_text, n_patched = patch_design_md(slug, raw_md)
            md_patched[0] += n_patched
            t = load_tokens(d, design_md=md_text)
            source = t['source']
            pdir = OUT / 'design-md' / slug
            pdir.mkdir(parents=True, exist_ok=True)
            doc, _one_file, css = build_page(t, slug)
            (pdir / 'preview_auto.html').write_text(doc, encoding='utf-8')
            (pdir / 'preview_auto.css').write_text(css, encoding='utf-8')
            # The upstream markdown travels with the page, so every style folder carries its own
            # source instead of depending on a clone staying alive in /tmp.
            for md in ('DESIGN.md', 'README.md'):
                s_md = d / md
                if not s_md.is_file():
                    # slack ships no upstream README; give it the local note anyway rather than
                    # leaving the one folder without a way to explain itself
                    if md == 'README.md':
                        (pdir / md).write_text(
                            patch_readme(slug, f'# {t["name"]}\n', synthetic=True),
                            encoding='utf-8')
                    continue
                if md == 'DESIGN.md':
                    text = md_text
                else:
                    text = patch_readme(slug, s_md.read_text(encoding='utf-8'),
                                        corrected=bool(n_patched))
                (pdir / md).write_text(text, encoding='utf-8')
                md_copied[0] += 1
            report.append((slug, source, len(t['colors']), len(t['typography']),
                           len(t['rounded']), len(t['spacing']), len(t['components']),
                           len(t['shadows']), 'ok'))
        except Exception as e:
            report.append((slug, '?', 0, 0, 0, 0, 0, 0, f'FAIL {e}'))
            traceback.print_exc()

    print(f'{"style":22} {"src":11} col typ rnd spc cmp shd  status')
    for r in report:
        print(f'{r[0]:22} {r[1]:11} {r[2]:3} {r[3]:3} {r[4]:3} {r[5]:3} {r[6]:3} {r[7]:3}  {r[8]}')
    print(f'\n{sum(1 for r in report if r[8] == "ok")}/{len(report)} ok -> {OUT}')
    print('this script owns preview_auto.* — merge_themes.py owns preview.*, so the two never')
    print('collide and either order is fine.')
    print(f'markdown copied into style folders: {md_copied[0]} (design-md passages corrected: {md_patched[0]})')


if __name__ == '__main__':
    main()
