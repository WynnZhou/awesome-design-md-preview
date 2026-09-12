# awesome-design-md → previews

<p dir="auto"><a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow" alt="License: MIT"></a> <a href="./index.html"><img src="https://img.shields.io/badge/Styles-76%20previews-4B32C3" alt="76 previews"></a> <a href="https://github.com/VoltAgent/awesome-design-md"><img src="https://img.shields.io/badge/Source-awesome--design--md-181717" alt="Source: awesome-design-md"></a> <a href="https://getdesign.md/"><img src="https://img.shields.io/badge/Previews-getdesign.md-0052CC" alt="Previews: getdesign.md"></a> <a href="https://developer.mozilla.org/docs/Web/HTML"><img src="https://img.shields.io/badge/Language-HTML%20%2F%20CSS-E34F26" alt="HTML / CSS"></a></p>

**English** · [中文](README-zh.md)

**Live:** <https://wynnzhou.github.io/awesome-design-md-preview/> — the same viewer, served from the repo.

76 design systems, previewed offline. `index.html` is the viewer; each style folder carries that style's page with both its light and its dark theme in it.

## Layout
    awesome-design-md-preview/
    ├── index.html                  the viewer — style list left, live preview right. Hand-kept:
    │                               no script writes it
    ├── README.md · README-zh.md · LICENSE
    ├── design-md/                  one folder per style — 76 of them, as upstream lays them out
    │   ├── <style>/
    │   │   ├── DESIGN.md           the upstream design doc, byte-for-byte
    │   │   ├── README.md           the upstream readme plus a local note
    │   │   ├── preview.html        merged — getdesign.md's two pages in one file (the default)
    │   │   ├── preview.css         its stylesheet, both themes at once
    │   │   ├── preview_auto.html   generated from DESIGN.md — the viewer's "Auto" mode
    │   │   ├── preview_auto.css    its stylesheet; 74 of the 76 have an auto page — Discord
    │   │   │                       and Mobbin have no DESIGN.md to generate one from
    │   │   ├── preview_light.html  getdesign.md's own saved page, light — the source, kept
    │   │   └── preview_dark.html   the same, dark. 74 of the 76 have one — BMW M and Lamborghini
    │   │                           have no dark variant upstream
    │   └── fonts/                  21 woff2 (latin subset) for the 5 families we host. It sits
    │                               here because the stylesheets beside it reference ../fonts/
    ├── icons/                      72 style icons, used by index.html. The other four rows fall back
    │                               to their brand colour chip
    └── _generator/
        ├── build_previews.py       DESIGN.md → preview_auto.html, preview_auto.css, fonts/ and
        │                           each folder's DESIGN.md + README.md
        ├── merge_themes.py         preview_light.html + preview_dark.html → preview.html and
        │                           preview.css, with both themes in one file
        └── fetch_getdesign.py      <slug> → preview_light.html + preview_dark.html, rendered from
                                    getdesign.md. Only needed for a style that is new here.

## Viewer

Three chips in the list header:

    EN / 中        the viewer's own chrome. Chinese by default. The style list translates with it;
                   the previews themselves never do.
    Merged/Split/Auto   cycles the three: preview.html, preview_light.html / preview_dark.html, or
                   preview_auto.html
    ☀ / ☾          light / dark — the viewer chrome and the previewed page together

Keys: `/` filter · `Esc` clear · `↑` `↓` previous/next · `t` theme. All three chips are remembered.

Merged and Auto hand the theme to the page over postMessage, so they swap without reloading; Split loads the other file. A style missing one of the three falls back to merged — BMW M and Lamborghini have no dark page, Discord and Mobbin no auto page.

## Merged preview

`preview_light.html` and `preview_dark.html` are near-copies — same head, same font CSS, a stylesheet that differs only in `:root` — so they fold into one page and one stylesheet with the two themes scoped under `html[data-theme]`. The bodies are identical for 43 of the 76; the other 33 differ in prose and swatches, so both are kept and CSS hides the inactive one.

The theme is settled before the first paint — a small script in `<head>` reads `?theme=` and localStorage — so switching to dark never flashes the light page first.

## Styles

All 76, grouped the way the sidebar groups them. Each link is that style's merged page — `preview_light.html` and `preview_dark.html` sit beside it.

### AI & LLM Platforms

- [Claude](design-md/claude/preview.html) — Anthropic's AI assistant. Warm terracotta accent, clean editorial layout.
- [Cohere](design-md/cohere/preview.html) — Enterprise AI platform. Vibrant gradients, data-rich dashboard aesthetic.
- [ElevenLabs](design-md/elevenlabs/preview.html) — AI voice platform. Dark cinematic UI, audio-waveform aesthetics.
- [MiniMax](design-md/minimax/preview.html) — AI model provider. Bold dark interface with neon accents.
- [Mistral AI](design-md/mistral-ai/preview.html) — Open-weight LLM provider. French-engineered minimalism, purple-toned.
- [Ollama](design-md/ollama/preview.html) — Run LLMs locally. Terminal-first, monochrome simplicity.
- [OpenCode](design-md/opencode-ai/preview.html) — AI coding platform. Developer-centric dark theme.
- [Replicate](design-md/replicate/preview.html) — Run ML models via API. Clean white canvas, code-forward.
- [Runway](design-md/runwayml/preview.html) — AI video generation. Cinematic dark UI, media-rich layout.
- [Together AI](design-md/together-ai/preview.html) — Open-source AI infrastructure. Technical, blueprint-style design.
- [VoltAgent](design-md/voltagent/preview.html) — AI agent framework. Void-black canvas, emerald accent, terminal-native.
- [xAI](design-md/x-ai/preview.html) — Elon Musk's AI lab. Stark monochrome, futuristic minimalism.

### Developer Tools & IDEs

- [Cursor](design-md/cursor/preview.html) — AI-first code editor. Sleek dark interface, gradient accents.
- [Expo](design-md/expo/preview.html) — React Native platform. Dark theme, tight letter-spacing, code-centric.
- [Lovable](design-md/lovable/preview.html) — AI full-stack builder. Playful gradients, friendly dev aesthetic.
- [Raycast](design-md/raycast/preview.html) — Productivity launcher. Sleek dark chrome, vibrant gradient accents.
- [Superhuman](design-md/superhuman/preview.html) — Fast email client. Premium dark UI, keyboard-first, purple glow.
- [Vercel](design-md/vercel/preview.html) — Frontend deployment. Black and white precision, Geist font.
- [Warp](design-md/warp/preview.html) — Modern terminal. Dark IDE-like interface, block-based command UI.

### Backend, Database & DevOps

- [ClickHouse](design-md/clickhouse/preview.html) — Fast analytics database. Yellow-accented, technical documentation style.
- [Composio](design-md/composio/preview.html) — Tool integration platform. Modern dark with colorful integration icons.
- [HashiCorp](design-md/hashicorp/preview.html) — Infrastructure automation. Enterprise-clean, black and white.
- [MongoDB](design-md/mongodb/preview.html) — Document database. Green leaf branding, developer documentation focus.
- [PostHog](design-md/posthog/preview.html) — Product analytics. Playful hedgehog branding, developer-friendly dark UI.
- [Sanity](design-md/sanity/preview.html) — Headless CMS. Red accent, content-first editorial layout.
- [Sentry](design-md/sentry/preview.html) — Error monitoring. Dark dashboard, data-dense, pink-purple accent.
- [Supabase](design-md/supabase/preview.html) — Open-source Firebase alternative. Dark emerald theme, code-first.

### Productivity & SaaS

- [Cal.com](design-md/cal/preview.html) — Open-source scheduling. Clean neutral UI, developer-oriented simplicity.
- [Intercom](design-md/intercom/preview.html) — Customer messaging. Friendly blue palette, conversational UI patterns.
- [Linear](design-md/linear-app/preview.html) — Project management. Ultra-minimal, precise, purple accent.
- [Mintlify](design-md/mintlify/preview.html) — Documentation platform. Clean, green-accented, reading-optimized.
- [Notion](design-md/notion/preview.html) — All-in-one workspace. Warm minimalism, serif headings, soft surfaces.
- [Resend](design-md/resend/preview.html) — Email API. Minimal dark theme, monospace accents.
- [Zapier](design-md/zapier/preview.html) — Automation platform. Warm orange, friendly illustration-driven.
- [Discord](design-md/discord/preview.html) — Team & community chat platform. Deep-indigo canvas with Blurple gradients, heavy all-caps display type.
- [Slack](design-md/slack/preview.html) — Workplace messaging brand. Deep-aubergine primary with cream-lavender hero gradients and pill CTAs.

### Design & Creative Tools

- [Airtable](design-md/airtable/preview.html) — Spreadsheet-database hybrid. Colorful, friendly, structured data aesthetic.
- [Clay](design-md/clay/preview.html) — Creative agency. Organic shapes, soft gradients, art-directed layout.
- [Figma](design-md/figma/preview.html) — Collaborative design tool. Vibrant multi-color, playful yet professional.
- [Framer](design-md/framer/preview.html) — Website builder. Bold black and blue, motion-first, design-forward.
- [Miro](design-md/miro/preview.html) — Visual collaboration. Bright yellow accent, infinite canvas aesthetic.
- [Webflow](design-md/webflow/preview.html) — Visual web builder. Blue-accented, polished marketing site aesthetic.
- [Mobbin](design-md/mobbin/preview.html) — UI reference library. Gallery-white monochrome, stadium pills, electric blue accent.

### Fintech & Crypto

- [Binance](design-md/binance/preview.html) — Crypto exchange. Bold yellow accent on monochrome, trading-floor urgency.
- [Coinbase](design-md/coinbase/preview.html) — Crypto exchange. Clean blue identity, trust-focused, institutional feel.
- [Kraken](design-md/kraken/preview.html) — Crypto trading. Purple-accented dark UI, data-dense dashboards.
- [Mastercard](design-md/mastercard/preview.html) — Global payments network. Warm cream canvas, orbital pill shapes, editorial warmth.
- [Revolut](design-md/revolut/preview.html) — Digital banking. Sleek dark interface, gradient cards, fintech precision.
- [Stripe](design-md/stripe/preview.html) — Payment infrastructure. Signature purple gradients, weight-300 elegance.
- [Wise](design-md/wise/preview.html) — Money transfer. Bright green accent, friendly and clear.

### E-commerce & Retail

- [Airbnb](design-md/airbnb/preview.html) — Travel marketplace. Warm coral accent, photography-driven, rounded UI.
- [Meta](design-md/meta/preview.html) — Tech retail store. Photography-first, binary light/dark surfaces, Meta Blue CTAs.
- [Nike](design-md/nike/preview.html) — Athletic retail. Monochrome UI, massive uppercase type, full-bleed photography.
- [Shopify](design-md/shopify/preview.html) — E-commerce platform. Dark-first cinematic, neon green accent, ultra-light type.
- [Starbucks](design-md/starbucks/preview.html) — Global coffee retail brand. Four-tier green system, warm cream canvas, full-pill buttons.

### Media & Consumer Tech

- [Apple](design-md/apple/preview.html) — Consumer electronics. Premium white space, SF Pro, cinematic imagery.
- [HP](design-md/hp/preview.html) — Consumer electronics catalog. White canvas with electric blue accent, angular chevron motifs.
- [IBM](design-md/ibm/preview.html) — Enterprise technology. Carbon design system, structured blue palette.
- [NVIDIA](design-md/nvidia/preview.html) — GPU computing. Green-black energy, technical power aesthetic.
- [Pinterest](design-md/pinterest/preview.html) — Visual discovery. Red accent, masonry grid, image-first.
- [PlayStation](design-md/playstation/preview.html) — Gaming console retail. Three-surface channel layout, quiet-authority display type, cyan hover-scale.
- [SpaceX](design-md/spacex/preview.html) — Space technology. Stark black and white, full-bleed imagery, futuristic.
- [Spotify](design-md/spotify/preview.html) — Music streaming. Vibrant green on dark, bold type, album-art-driven.
- [The Verge](design-md/theverge/preview.html) — Tech editorial media. Acid-mint and ultraviolet accents, Manuka display, rave-flyer story tiles.
- [Uber](design-md/uber/preview.html) — Mobility platform. Bold black and white, tight type, urban energy.
- [Vodafone](design-md/vodafone/preview.html) — Global telecom brand. Monumental uppercase display, Vodafone Red chapter bands.
- [WIRED](design-md/wired/preview.html) — Tech magazine. Paper-white broadsheet density, custom serif display, mono kickers, ink-blue links.

### Automotive

- [BMW](design-md/bmw/preview.html) — Luxury automotive. Dark premium surfaces, precise German engineering aesthetic.
- [BMW M](design-md/bmw-m/preview.html) — Motorsport automotive. Pure black canvas, M tricolor stripe accents, full-bleed photography.
- [Bugatti](design-md/bugatti/preview.html) — Hypercar brand. Cinema-black canvas, monochrome austerity, monumental display type.
- [Ferrari](design-md/ferrari/preview.html) — Luxury automotive. Chiaroscuro editorial, Ferrari Red accents, cinematic black.
- [Lamborghini](design-md/lamborghini/preview.html) — Supercar brand. True black surfaces, gold accents, dramatic uppercase typography.
- [Renault](design-md/renault/preview.html) — French automotive. Vibrant aurora gradients, NouvelR typography, bold energy.
- [Tesla](design-md/tesla/preview.html) — Electric automotive. Radical subtraction, full-viewport photography, near-zero UI.

### Retro Web · DESIGN.md Nostalgia

- [Dell (1996)](design-md/dell-1996/preview.html) — Catalog-era PC retail web. Black page frame, flat color-block ribbon cards, Helvetica-Black over Times Roman.
- [Nintendo (2001)](design-md/nintendo-2001/preview.html) — Y2K "console chrome" web. Brushed-periwinkle metal panels, amber nav on a dotted carbon bar, outlined Arial-Black box-art type.

## Regenerate

    git clone --depth 1 https://github.com/VoltAgent/awesome-design-md /tmp/awesome-design-md
    python3 _generator/build_previews.py      # DESIGN.md -> preview_auto.html, preview_auto.css, fonts/
    python3 _generator/merge_themes.py        # preview_light/dark.html -> preview.html, preview.css

A style that is new here needs its source pages first — that is the only thing `fetch_getdesign.py` is for:

    python3 _generator/fetch_getdesign.py <slug>   # getdesign.md -> preview_light.html, preview_dark.html

`fetch_getdesign.py <slug>` is the only script here that goes to the network, and it does so three ways: it opens the live site in headless Chrome (getdesign.md is a JS app, so curl only returns an 8K shell); that page load also fires the page's own requests — Google Fonts, the site's Cloudflare beacon, the GitHub avatar in its footer — which are then stripped from the saved copy; and any woff2 we do not already have is pulled from jsDelivr. Running it means one real visit to someone else's site. `merge_themes.py` never touches the network.

Each script owns its own filenames, so the two never collide and either order is fine: `build_previews.py` writes `preview_auto.*`, `merge_themes.py` writes `preview.*`.

`index.html` is not regenerated by anything — its rows, its i18n and the two `NO_DARK` / `NO_AUTO` fallback lists are maintained in the file directly.

## License

[MIT](LICENSE), the same license the upstream design docs ship under.

## Acknowledgements

- [**VoltAgent/awesome-design-md**](https://github.com/VoltAgent/awesome-design-md) — the `DESIGN.md` documents every page derives from, and the licence this folder carries.
- [**getdesign.md**](https://getdesign.md/) — the hand-authored light and dark pages, and the sidebar listing.
- [**fontsource**](https://fontsource.org/) on jsDelivr — the woff2 in `fonts/`, fetched once so the pages carry their own faces.
- [**Simple Icons**](https://simpleicons.org/) (CC0 1.0) — 19 of the SVG marks in `icons/`; the rest are the organisations' GitHub avatars.
- Brand names, marks and design systems belong to their owners. The `DESIGN.md` files are VoltAgent's (MIT); the light and dark pages are getdesign.md's, mirrored here so the set can be read offline.
