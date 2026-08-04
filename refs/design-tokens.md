# Design tokens — reference issue 412

Extracted from `offsec-quotidien-412.html` and encoded in `scripts/render.py`.
This file is documentation; `render.py` is the implementation. If they ever
disagree, `render.py` wins and this file is stale.

**Fidelity is exact.** Only *content* changes between issues — every colour,
font, spacing and border below is fixed.

## Format constraints (email)

- Layout in nested `<table role="presentation">`. Never `<div>` for structure.
- No flexbox, no grid, no CSS classes, no external stylesheet, no JavaScript.
- All styles inline via `style="…"`.
- Container 680 px, centred on a 100 % `#e6e4df` background.
- No `<meta viewport>` — its `width=device-width` gets mangled by
  quoted-printable in transit.
- All non-ASCII as HTML entities (`&eacute;`, `&rsquo;`, `&mdash;`, `&nbsp;`).
  `render.py` does this automatically; do not hand-encode.
- Light background assumed; no dark variant is provided.

## Colours

| Role | Hex | Usage |
|---|---|---|
| Page background | `#e6e4df` | `<body>` / outer cell |
| Card background | `#fbfaf8` | main 680 px table |
| Card border | `#cfccc4` | main table border |
| Ink — primary | `#1e1d1b` | headings, strong text, dark bands |
| Ink — body | `#2c2a26` | body paragraphs |
| Ink — soft | `#403d38` | secondary body |
| Ink — muted | `#5f5c55` | subtitles |
| Ink — faint | `#7d7a73` | metadata, captions |
| Accent brown | `#7a4a2e` | header rule, part numbers, TL;DR bullets, autopsy markers |
| Accent blue | `#2f5474` | links (hover `#7a4a2e`) |
| Sommaire band | `#2a2825` bg, `#3d3a35` rules, `#e2ddd3` text | clickable contents |
| TL;DR | `#f2ecdd` bg, `2px solid #1e1d1b` | summary block |
| Inline code | `#e4dcc6` (in TL;DR) / `#eeece6` (in body) | `<span>` code |
| Code block | `#211f1c` bg, `#111010` border, `#e0dcd3` text, `#a29d94` file header on `#3a3733` rule | source extracts |
| Warning callout | `#f7ecd6` bg, `2px dashed #8a5a12`, `#6b4409` title, `#3b2c11` text | untested hypothesis |
| Sources block | `#f1efea` bg, `#dcd8d0` border | per-part citations |
| Empty-surface note | `1px dashed #c4c0b8`, text `#7d7a73` / `#5f5c55` | deliberate gap |
| Footer | `#1e1d1b` bg, `3px solid #7a4a2e` top, `#b5b0a7` / `#8f8b82` text, `#c9b79a` link | footer |

## Tag badges

| Tag | Background | Border |
|---|---|---|
| `[quick]` | `#4a6b52` | `#35513c` |
| `[deep-dive]` | `#2f5474` | `#1f3d57` |
| `[PoC/lab]` | `#7a4a2e` | `#5c3620` |
| `[archive]` | `#5c5a55` | `#43413d` |

Badge text: off-white (`#f7f5f0` / `#f9f6f1`), `font-weight:700`,
`letter-spacing:0.5px`, `font-size:11px`.

## Typography

- **Sans** (headings, body): `-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif`
- **Mono** (metadata, code, labels): `Consolas,'SF Mono',Menlo,monospace`

| Element | Size / line-height |
|---|---|
| Main title | 27px / 32px bold |
| Part title | 24px / 29px bold |
| Item title | 17px / 24px bold |
| Body | 15–16px / 22–25px |
| Metadata (mono) | 11–13px |
| Code | 13px / 20px |

Mono labels are always `text-transform:uppercase` with
`letter-spacing:1.5–2px`.

## Components → `render.py`

| # | Component | Function | `content.json` block |
|---|---|---|---|
| 1 | En-tête | `header()` | `meta` |
| 2 | Sommaire | `toc()` | derived from `parts` |
| 3 | TL;DR | `tldr()` | `tldr[]` |
| 4 | Titre de partie | `part_title()` | `parts[].title_html` |
| 5 | Item de veille | `news_item()` | `{"type":"item"}` |
| 6 | Bloc de code | `code_block()` | `{"type":"code"}` |
| 7 | Encart avertissement | `warning()` | `{"type":"warning"}` |
| 8 | Étapes numérotées | `numbered_steps()` | `{"type":"steps"}` |
| 9 | Tableau comparatif | `comparison_table()` | `{"type":"table"}` |
| 10 | Étapes d'autopsie | `autopsy_steps()` | `{"type":"autopsy"}` |
| 11 | Bloc de sources | `sources_block()` | `parts[].sources` |
| 12 | Note « surface à vide » | `empty_note()` | `{"type":"empty"}` |
| 13 | Pied de page | `footer()` | `meta` |

Component 12 is the one that matters editorially: it exists so a section with
nothing solid to say can stay empty rather than be filled with hollow text.
Using it is correct behaviour, not a failure.

## Measured budget

| Metric | Value |
|---|---|
| Reference issue 412 | 62 KB, ~4 000 words |
| Full issue, ~10 000 words | ≈ 140–180 KB |
| Quoted-printable inflation | +3.7 % (output is pure ASCII) |
| Digest budget | 90 KB raw → ≈ 93 KB encoded |
| Gmail clip threshold | ~102 KB, attachments exempt |
| Typical digest contents | Parties 01–02 complete |
