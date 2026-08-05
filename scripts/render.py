#!/usr/bin/env python3
"""
OffSec Quotidien - deterministic HTML renderer.

Turns a structured content.json into the exact component system of reference
issue 412. The generating model never writes HTML: it writes content, and this
module emits the markup. That separation is the whole point - it makes design
drift impossible and keeps the byte budget predictable.

Every style value below is copied verbatim from offsec-quotidien-412.html.
Do not "clean up" the inline styles: email clients need them inline, and the
handoff specifies pixel-exact reproduction.

Usage:
    python3 scripts/render.py content.json out/full.html
"""

import html
import json
import sys
from html.entities import codepoint2name
from datetime import datetime, timezone

# --- Design tokens (handoff 412) ---------------------------------------------

SANS = "-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
MONO = "Consolas,'SF Mono',Menlo,monospace"

PAGE_BG = "#e6e4df"
CARD_BG = "#fbfaf8"
CARD_BORDER = "#cfccc4"
INK = "#1e1d1b"
INK_BODY = "#2c2a26"
INK_SOFT = "#403d38"
INK_MUTED = "#5f5c55"
INK_FAINT = "#7d7a73"
BROWN = "#7a4a2e"
BLUE = "#2f5474"

# Tag badge variants: (background, border, text)
TAGS = {
    "quick":    ("#4a6b52", "#35513c", "#f7f5f0"),
    "deep-dive": ("#2f5474", "#1f3d57", "#f7f5f0"),
    "PoC/lab":  ("#7a4a2e", "#5c3620", "#f9f6f1"),
    "archive":  ("#5c5a55", "#43413d", "#f7f5f0"),
}

# --- Text encoding ------------------------------------------------------------

# Override map consulted before the generic entity encoder below. It exists for
# characters whose standard name is wrong for French typesetting, or that have
# no name at all - notably U+202F NARROW NO-BREAK SPACE, which a French keyboard
# produces before ':', ';', '!' and '?' and which must render as &nbsp;.
_TYPO = {
    "’": "&rsquo;", "‘": "&lsquo;",
    "“": "&ldquo;", "”": "&rdquo;",
    "—": "&mdash;", "–": "&ndash;",
    "«": "&laquo;", "»": "&raquo;",
    "…": "&hellip;", "→": "&rarr;", "›": "&rsaquo;",
    " ": "&nbsp;",
}


def _entities(text):
    """
    Replace every non-ASCII character with an HTML entity.

    The handoff requires French text encoded as entities (&eacute;, &rsquo;,
    &mdash;, &nbsp;...). This matters beyond matching the spec: mail transport
    re-encodes a raw UTF-8 body as quoted-printable, where every accent becomes
    a 6-byte '=C3=A9' sequence that is both larger and easier to corrupt, and a
    few older clients mis-render the result outright.

    _TYPO is consulted first for the special cases, then html.entities supplies
    the name for everything else - which is what catches the accented letters an
    explicit hand-written map always ends up missing. Characters with no name
    fall back to a numeric reference, which is always valid.

    ASCII passes through untouched, so this is safe on already-escaped text
    ('&amp;' survives) and on trusted markup ('<span style="...">' survives).
    """
    if text is None:
        return ""
    out = []
    for char in str(text):
        mapped = _TYPO.get(char)
        if mapped is not None:
            out.append(mapped)
            continue
        point = ord(char)
        if point < 128:
            out.append(char)
        elif point in codepoint2name:
            out.append(f"&{codepoint2name[point]};")
        else:
            out.append(f"&#{point};")
    return "".join(out)


def esc(text):
    """
    Escape untrusted plain text, then entity-encode it.

    Order matters: html.escape first neutralises &, < and >, and because
    _entities leaves ASCII alone the '&amp;' it produced is not double-encoded.
    """
    if text is None:
        return ""
    return _entities(html.escape(str(text), quote=False))


def typo(text):
    """
    Convert French typography to entities WITHOUT escaping HTML markup.

    Applied to every *_html field. Those fields are trusted markup produced by
    the pipeline (they may legitimately contain <span>, <strong>, <a>), so they
    must not be html.escape()d - but they still need their curly quotes, dashes
    and non-breaking spaces turned into entities before transport re-encodes
    the body. Without this, an em dash typed naturally in a title survives as a
    raw multi-byte character and can be mangled by quoted-printable.
    """
    return _entities(text)


def code_esc(text):
    """
    Escape a code block.

    html.escape neutralises the XML-significant characters, then _entities makes
    the result 7-bit clean. Entity-encoding code is safe: the block renders with
    white-space:pre-wrap, so '&eacute;' still displays as the accented character
    while the transmitted bytes stay pure ASCII.
    """
    return _entities(html.escape(str(text), quote=False))


def inline_code(text):
    """Monospace span used for technical terms inside body prose."""
    return (f'<span style="font-family:{MONO}; font-size:14px; '
            f'background-color:#eeece6; padding:1px 4px;">{esc(text)}</span>')


def _row(inner):
    """Wrap a cell in the outer single-column table row used by every block."""
    return f"<tr>\n{inner}\n</tr>\n"


# --- Component 1 : header -----------------------------------------------------

def header(meta):
    theme = meta.get("theme", {})
    # French thousands separator is a non-breaking space, not a comma.
    words = f"{meta['words']:,}".replace(",", "&nbsp;")
    return _row(f"""<td style="padding:26px 30px 20px 30px; background-color:{INK}; border-bottom:3px solid {BROWN};">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse;">
  <tr>
    <td style="font-family:{MONO}; font-size:11px; letter-spacing:2px; text-transform:uppercase; color:#a8a49b; padding-bottom:8px;">Bulletin interne &nbsp;/&nbsp; s&eacute;curit&eacute; offensive &nbsp;/&nbsp; diffusion {meta.get('diffusion', 1)}</td>
  </tr>
  <tr>
    <td style="font-family:{SANS}; font-size:27px; line-height:32px; font-weight:700; color:#f5f3ef; letter-spacing:-0.4px; padding-bottom:10px;">OffSec Quotidien &mdash; n&deg;{meta['issue']}</td>
  </tr>
  <tr>
    <td style="font-family:{MONO}; font-size:13px; line-height:20px; color:#c8c3b9;">{esc(meta['date_label'])} &nbsp;&middot;&nbsp; {esc(meta['time_label'])} &nbsp;&middot;&nbsp; {words} mots &nbsp;&middot;&nbsp; ~{meta['reading_minutes']} min</td>
  </tr>
  <tr>
    <td style="padding-top:14px;">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse; border-left:3px solid {BROWN};">
      <tr>
        <td style="padding:2px 0 2px 12px; font-family:{SANS}; font-size:14px; line-height:21px; color:#e8e4dc;"><span style="font-family:{MONO}; font-size:11px; letter-spacing:1px; text-transform:uppercase; color:#a8a49b;">Th&egrave;me de la semaine</span><br><span style="font-weight:600; color:#f5f3ef;">{esc(theme.get('title', ''))}</span> &mdash; {esc(theme.get('subtitle', ''))}</td>
      </tr>
      </table>
    </td>
  </tr>
  </table>
</td>""")


# --- Component 2 : table of contents -----------------------------------------

def toc(parts):
    rows = []
    for index, part in enumerate(parts):
        last = index == len(parts) - 1
        padding = "5px 0 16px 0" if last else "5px 0"
        rows.append(
            f'  <tr><td style="padding:{padding}; border-top:1px solid #3d3a35; font-family:{MONO}; font-size:13px; line-height:19px;">'
            f'<a href="#partie-{part["n"]}" style="color:#e2ddd3; text-decoration:none;">'
            f'<span style="color:{BROWN}; font-weight:700;">{part["n"]:02d}</span> &nbsp; {esc(part["title"])} '
            f'<span style="color:#8f8b82;">&mdash; {esc(part.get("count_label", ""))}</span></a></td></tr>'
        )
    body = "\n".join(rows)
    return _row(f"""<td style="padding:0 30px; background-color:#2a2825;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse;">
  <tr>
    <td style="padding:16px 0 8px 0; font-family:{MONO}; font-size:11px; letter-spacing:1.5px; text-transform:uppercase; color:#8f8b82;">Sommaire</td>
  </tr>
{body}
  </table>
</td>""")


# --- Component 3 : TL;DR ------------------------------------------------------

def tldr(bullets):
    rows = []
    for index, bullet in enumerate(bullets):
        last = index == len(bullets) - 1
        pad = "" if last else " padding-bottom:9px;"
        rows.append(f"""      <tr>
        <td width="22" valign="top" style="width:22px; font-family:{MONO}; font-size:16px; line-height:24px; color:{BROWN}; font-weight:700;">&rsaquo;</td>
        <td valign="top" style="font-family:{SANS}; font-size:16px; line-height:24px; color:{INK};{pad}">{typo(bullet)}</td>
      </tr>""")
    body = "\n".join(rows)
    return _row(f"""<td style="padding:24px 20px 4px 20px;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse; background-color:#f2ecdd; border:2px solid {INK};">
  <tr>
    <td style="padding:16px 18px 6px 18px; font-family:{MONO}; font-size:13px; letter-spacing:2px; text-transform:uppercase; font-weight:700; color:{INK}; border-bottom:1px solid #cfc4a8;">TL;DR &mdash; 30 secondes</td>
  </tr>
  <tr>
    <td style="padding:14px 18px 18px 18px;">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse;">
{body}
      </table>
    </td>
  </tr>
  </table>
</td>""")


# --- Component 4 : part title -------------------------------------------------

def part_title(part, first=False):
    top_pad = "34px" if first else "14px"
    kicker = f"Partie {part['n']:02d}"
    if part.get("kind"):
        kicker += f" &nbsp;&middot;&nbsp; {esc(part['kind'])}"
    return _row(f"""<td id="partie-{part['n']}" style="padding:{top_pad} 30px 0 30px;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse; border-top:3px solid {INK};">
  <tr><td style="padding:10px 0 0 0; font-family:{MONO}; font-size:12px; letter-spacing:2px; text-transform:uppercase; color:{BROWN}; font-weight:700;">{kicker}</td></tr>
  <tr><td style="padding:4px 0 6px 0; font-family:{SANS}; font-size:24px; line-height:29px; font-weight:700; color:{INK}; letter-spacing:-0.3px;">{typo(part['title_html'])}</td></tr>
  <tr><td style="padding:0 0 {'4px' if first else '14px'} 0; font-family:{SANS}; font-size:14px; line-height:21px; color:{INK_MUTED};">{esc(part.get('subtitle', ''))}</td></tr>
  </table>
</td>""")


# --- Component 5 : news item --------------------------------------------------

def news_item(item, last=False):
    bg, border, fg = TAGS.get(item.get("tag", "quick"), TAGS["quick"])
    bottom = "18px" if last else "16px"
    return _row(f"""<td style="padding:0 30px;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse; border-top:1px solid #dcd8d0;">
  <tr>
    <td style="padding:16px 0 4px 0;">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
      <tr><td style="background-color:{bg}; padding:3px 8px; font-family:{MONO}; font-size:11px; font-weight:700; letter-spacing:0.5px; color:{fg}; border:1px solid {border};">[{esc(item.get('tag', 'quick'))}]</td></tr>
      </table>
    </td>
  </tr>
  <tr><td style="padding:8px 0 0 0; font-family:{SANS}; font-size:17px; line-height:24px; font-weight:700; color:{INK};">{typo(item['title_html'])}</td></tr>
  <tr><td style="padding:5px 0 0 0; font-family:{SANS}; font-size:15px; line-height:22px; color:{INK_SOFT};"><span style="color:{BROWN}; font-weight:700;">Pourquoi &ccedil;a compte&nbsp;:</span> {typo(item['why_html'])}</td></tr>
  <tr><td style="padding:6px 0 {bottom} 0; font-family:{MONO}; font-size:12px; line-height:18px;"><a href="{esc(item['url'])}" style="color:{BLUE}; text-decoration:underline;">{esc(item['url_label'])}</a> <span style="color:{INK_FAINT};">&middot; {esc(item['date_label'])}</span></td></tr>
  </table>
</td>""")


# --- Component 6 : code block -------------------------------------------------

def code_block(block, caption=None):
    caption_row = ""
    if caption:
        caption_row = _row(f'<td style="padding:0 30px 18px 30px; font-family:{MONO}; font-size:11px; line-height:17px; color:{INK_FAINT};">{esc(caption)}</td>')
    bottom = "6px" if caption else "16px"
    return _row(f"""<td style="padding:0 30px {bottom} 30px;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse; background-color:#211f1c; border:1px solid #111010;">
  <tr>
    <td style="padding:9px 14px; border-bottom:1px solid #3a3733; font-family:{MONO}; font-size:11px; letter-spacing:1px; color:#a29d94;">{esc(block['label'])}</td>
  </tr>
  <tr>
    <td style="padding:14px; font-family:{MONO}; font-size:13px; line-height:20px; color:#e0dcd3; white-space:pre-wrap; word-break:break-word; overflow-wrap:break-word;">{code_esc(block['code'])}</td>
  </tr>
  </table>
</td>""") + caption_row


# --- Component 7 : untested-hypothesis callout --------------------------------

def warning(text_html):
    return _row(f"""<td style="padding:0 30px 20px 30px;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse; background-color:#f7ecd6; border:2px dashed #8a5a12;">
  <tr>
    <td style="padding:12px 16px 6px 16px; font-family:{MONO}; font-size:12px; letter-spacing:1.5px; text-transform:uppercase; font-weight:700; color:#6b4409;">&#9888;&#65039; Hypoth&egrave;se non test&eacute;e</td>
  </tr>
  <tr>
    <td style="padding:0 16px 14px 16px; font-family:{SANS}; font-size:15px; line-height:23px; color:#3b2c11;">{typo(text_html)}</td>
  </tr>
  </table>
</td>""")


# --- Component 8 : numbered steps (no <ol>, tables only) ----------------------

def numbered_steps(title, steps):
    rows = []
    for index, step in enumerate(steps):
        last = index == len(steps) - 1
        cell_pad = "0 10px 0 0" if last else "0 10px 10px 0"
        text_pad = "" if last else "padding:0 0 10px 0; "
        rows.append(f"""      <tr>
        <td width="34" valign="top" style="width:34px; padding:{cell_pad};"><table role="presentation" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;"><tr><td width="24" height="24" align="center" valign="middle" style="width:24px; height:24px; background-color:{INK}; font-family:{MONO}; font-size:12px; font-weight:700; color:#f5f3ef; line-height:24px;">{index + 1}</td></tr></table></td>
        <td valign="top" style="{text_pad}font-family:{SANS}; font-size:15px; line-height:24px; color:{INK_BODY};">{typo(step)}</td>
      </tr>""")
    body = "\n".join(rows)
    return _row(f"""<td style="padding:0 30px 18px 30px;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse;">
  <tr>
    <td style="padding:0 0 10px 0; font-family:{MONO}; font-size:11px; letter-spacing:1.5px; text-transform:uppercase; color:{INK_MUTED}; font-weight:700;">{esc(title)}</td>
  </tr>
  <tr>
    <td>
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse;">
{body}
      </table>
    </td>
  </tr>
  </table>
</td>""")


# --- Component 9 : comparison table -------------------------------------------

def comparison_table(table, caption=None):
    widths = table.get("widths", ["28%", "24%", "24%", "24%"])
    headers = []
    for index, head in enumerate(table["headers"]):
        last = index == len(table["headers"]) - 1
        sep = "" if last else f" border-right:1px solid #3a3733;"
        headers.append(
            f'    <td width="{widths[index]}" style="width:{widths[index]}; padding:8px 8px; background-color:{INK}; '
            f'font-family:{MONO}; font-size:11px; line-height:15px; letter-spacing:0.5px; color:#f5f3ef; '
            f'font-weight:700;{sep} word-break:break-word;">{esc(head)}</td>'
        )
    rows = ["  <tr>\n" + "\n".join(headers) + "\n  </tr>"]

    for row_index, row in enumerate(table["rows"]):
        bg = CARD_BG if row_index % 2 == 0 else "#f4f2ed"
        cells = []
        for cell_index, cell in enumerate(row):
            last = cell_index == len(row) - 1
            sep = "" if last else " border-right:1px solid #dcd8d0;"
            # First column is the row key: mono and bold, matching reference 412.
            if cell_index == 0:
                font = f"font-family:{MONO}; font-size:12px; line-height:17px; color:{INK}; font-weight:700;"
            else:
                font = f"font-family:{SANS}; font-size:13px; line-height:18px; color:{INK_SOFT};"
            cells.append(
                f'    <td style="padding:9px 8px; background-color:{bg}; border-top:1px solid #dcd8d0;{sep} '
                f'{font} word-break:break-word;">{esc(cell)}</td>'
            )
        rows.append("  <tr>\n" + "\n".join(cells) + "\n  </tr>")

    body = "\n".join(rows)
    out = _row(f"""<td style="padding:0 30px 8px 30px;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse; table-layout:fixed; border:1px solid {CARD_BORDER};">
{body}
  </table>
</td>""")
    if caption:
        out += _row(f'<td style="padding:0 30px 18px 30px; font-family:{MONO}; font-size:11px; line-height:17px; color:{INK_FAINT};">{esc(caption)}</td>')
    return out


# --- Component 10 : attack autopsy steps --------------------------------------

def autopsy_steps(steps):
    rows = []
    for index, step in enumerate(steps):
        first = index == 0
        last = index == len(steps) - 1
        marker_pad = "0 10px 14px 0" if first else ("14px 10px 0 0" if last else "14px 10px 14px 0")
        if first:
            text_style = "padding:0 0 14px 0; border-bottom:1px solid #e3dfd7; "
        elif last:
            text_style = "padding:14px 0 0 0; "
        else:
            text_style = "padding:14px 0; border-bottom:1px solid #e3dfd7; "
        rows.append(f"""  <tr>
    <td width="34" valign="top" style="width:34px; padding:{marker_pad};"><table role="presentation" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;"><tr><td width="26" height="26" align="center" valign="middle" style="width:26px; height:26px; background-color:{BROWN}; font-family:{MONO}; font-size:12px; font-weight:700; color:#f9f6f1; line-height:26px;">{index + 1}</td></tr></table></td>
    <td valign="top" style="{text_style}font-family:{SANS}; font-size:15px; line-height:23px; color:{INK_BODY};"><span style="font-family:{MONO}; font-size:11px; color:{INK_FAINT}; letter-spacing:1px;">{esc(step['stamp'])} &nbsp;&middot;&nbsp; {esc(step['phase']).upper()}</span><br>{typo(step['text_html'])}</td>
  </tr>""")
    body = "\n".join(rows)
    return _row(f"""<td style="padding:0 30px 20px 30px;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse;">
{body}
  </table>
</td>""")


# --- Component 11 : sources block ---------------------------------------------

def sources_block(part_number, entries):
    rows = []
    width = 34 if any(entry["n"] >= 10 for entry in entries) else 30
    for index, entry in enumerate(entries):
        last = index == len(entries) - 1
        pad = "" if last else " padding-bottom:6px;"
        if entry.get("url"):
            link = f'<a href="{esc(entry["url"])}" style="color:{BLUE};">{esc(entry["title"])}</a>'
        else:
            # Offline references (books, papers) carry no link, per issue 412.
            link = f'<span style="color:{INK_MUTED};">{esc(entry["title"])}</span>'
        rows.append(f"""      <tr>
        <td width="{width}" valign="top" style="width:{width}px; font-size:12px; line-height:19px; color:{BROWN}; font-weight:700;{pad}">[{entry['n']}]</td>
        <td valign="top" style="font-size:12px; line-height:19px; color:{INK_SOFT};{pad} word-break:break-word;"><span style="color:{INK}; font-weight:700;">{esc(entry['date'])}</span> &nbsp;&middot;&nbsp; {esc(entry['author'])} &mdash; {link}</td>
      </tr>""")
    body = "\n".join(rows)
    return _row(f"""<td style="padding:8px 30px 30px 30px;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse; background-color:#f1efea; border:1px solid #dcd8d0;">
  <tr><td style="padding:12px 16px 8px 16px; font-family:{MONO}; font-size:11px; letter-spacing:1.5px; text-transform:uppercase; color:{INK_MUTED}; font-weight:700; border-bottom:1px solid #dcd8d0;">Sources &mdash; partie {part_number:02d}</td></tr>
  <tr>
    <td style="padding:12px 16px 14px 16px;">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse; font-family:{MONO};">
{body}
      </table>
    </td>
  </tr>
  </table>
</td>""")


# --- Component 12 : deliberate-gap note ---------------------------------------

def empty_note(headline, detail):
    return _row(f"""<td style="padding:0 30px 4px 30px;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse; border-top:1px dashed #c4c0b8;">
  <tr>
    <td style="padding:12px 0 14px 0; font-family:{MONO}; font-size:13px; line-height:20px; color:{INK_FAINT};"><span style="color:#9b9791;">&mdash;&mdash;</span>&nbsp; <span style="color:{INK_MUTED};">{esc(headline)}</span> {esc(detail)}</td>
  </tr>
  </table>
</td>""")


# --- Component 13 : footer ----------------------------------------------------

# Standing colophon, identical on every issue.
#
# Hardcoded here rather than exposed as a content.json field on purpose: it
# describes what the publication *is*, which does not vary per issue, and a
# generation run has no business rewording or dropping it. If the statement
# below ever stops being true of an issue, the issue is wrong - not this text.
COLOPHON = (
    "Bulletin d&rsquo;analyse technique en s&eacute;curit&eacute; offensive. "
    "Chaque sujet porte sur des travaux publics et cit&eacute;s&nbsp;: le "
    "bulletin commente la recherche existante et n&rsquo;en produit pas. "
    "Destin&eacute; &agrave; un lectorat professionnel, pour usage en "
    "laboratoire ou dans le cadre d&rsquo;engagements autoris&eacute;s."
)


def footer(meta):
    archive = meta.get("archive_url", "")
    label = archive.replace("https://", "")
    return _row(f"""<td style="padding:22px 30px 26px 30px; background-color:{INK}; border-top:3px solid {BROWN};">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse;">
  <tr><td style="font-family:{MONO}; font-size:12px; line-height:19px; color:#b5b0a7; padding-bottom:4px;">G&eacute;n&eacute;r&eacute; le {esc(meta['generated_at'])} &nbsp;&middot;&nbsp; pipeline {esc(meta.get('pipeline', 'v1.0'))}</td></tr>
  <tr><td style="font-family:{MONO}; font-size:12px; line-height:19px; color:#b5b0a7; padding-bottom:4px;">Fen&ecirc;tre couverte&nbsp;: {esc(meta['window'])} &nbsp;&middot;&nbsp; {meta['sources_scanned']} sources scann&eacute;es, {meta['sources_kept']} retenues</td></tr>
  <tr><td style="font-family:{MONO}; font-size:12px; line-height:19px; padding-bottom:10px;"><a href="{esc(archive)}" style="color:#c9b79a; text-decoration:underline;">{esc(label)}</a> &nbsp;&middot;&nbsp; <span style="color:#8f8b82;">&eacute;ditions n&deg;1 &agrave; {meta['issue']}</span></td></tr>
  <tr><td style="border-top:1px solid #3a3733; padding-top:10px; padding-bottom:8px; font-family:{MONO}; font-size:11px; line-height:17px; color:{INK_FAINT};">Fond clair assum&eacute;&nbsp;: aucune variante sombre n&rsquo;est fournie. Diffusion&nbsp;: {meta.get('recipients', 1)} destinataire(s).</td></tr>
  <tr><td style="border-top:1px solid #3a3733; padding-top:8px; font-family:{MONO}; font-size:11px; line-height:17px; color:#8f8b82;">{COLOPHON}</td></tr>
  </table>
</td>""")


# --- Body assembly ------------------------------------------------------------

def render_part(part):
    """Render one part's blocks in declared order."""
    out = ""
    for block in part.get("blocks", []):
        kind = block["type"]
        if kind == "prose":
            out += _row(f'<td style="padding:0 30px 16px 30px; font-family:{SANS}; font-size:16px; line-height:25px; color:{INK_BODY};">\n  {typo(block["html"])}\n</td>')
        elif kind == "item":
            out += news_item(block, last=block.get("last", False))
        elif kind == "code":
            out += code_block(block, caption=block.get("caption"))
        elif kind == "warning":
            out += warning(block["html"])
        elif kind == "steps":
            out += numbered_steps(block["title"], block["steps"])
        elif kind == "table":
            out += comparison_table(block, caption=block.get("caption"))
        elif kind == "autopsy":
            out += autopsy_steps(block["steps"])
        elif kind == "empty":
            out += empty_note(block["headline"], block["detail"])
        else:
            raise ValueError(f"Unknown block type: {kind}")
    if part.get("sources"):
        out += sources_block(part["n"], part["sources"])
    return out


def render(content, parts_to_include=None):
    """
    Assemble the full document.

    parts_to_include lets split.py emit a reduced digest from the same content
    tree, so the digest and the full issue can never disagree on wording.
    """
    meta = content["meta"]
    parts = content["parts"]
    if parts_to_include is not None:
        parts = [p for p in parts if p["n"] in parts_to_include]

    body = header(meta) + toc(content["parts"]) + tldr(content["tldr"])
    for index, part in enumerate(parts):
        body += part_title(part, first=(index == 0))
        body += render_part(part)

    if content.get("continuation"):
        body += _row(f'<td style="padding:0 30px 24px 30px; font-family:{SANS}; font-size:15px; line-height:23px; color:{INK_BODY};">\n  {typo(content["continuation"])}\n</td>')

    body += footer(meta)

    preheader = esc(content.get("preheader", ""))
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="color-scheme" content="light dark">
<title>OffSec Quotidien n&deg;{meta['issue']}</title>
<!-- No <meta viewport>: its width=device-width is mangled by quoted-printable
     encoding in transit. No stylesheet, no JS: every style is inline below. -->
</head>
<body style="margin:0; padding:0; background-color:{PAGE_BG}; -webkit-text-size-adjust:100%;">

<div style="display:none; font-size:1px; line-height:1px; max-height:0; max-width:0; opacity:0; overflow:hidden; color:{PAGE_BG};">{preheader}</div>

<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse; background-color:{PAGE_BG}; margin:0; padding:0;">
<tr>
<td align="center" style="padding:24px 12px 40px 12px; font-family:{SANS};">

<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="680" style="width:100%; max-width:680px; border-collapse:collapse; background-color:{CARD_BG}; border:1px solid {CARD_BORDER};">

{body}
</table>
</td>
</tr>
</table>

</body>
</html>
"""


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    with open(sys.argv[1], encoding="utf-8") as handle:
        content = json.load(handle)

    content["meta"].setdefault(
        "generated_at",
        datetime.now(timezone.utc).strftime("%Y-%m-%d à %H:%M UTC"),
    )

    output = render(content)
    with open(sys.argv[2], "w", encoding="utf-8") as handle:
        handle.write(output)

    size_kb = len(output.encode("utf-8")) / 1024
    print(f"Wrote {sys.argv[2]} - {size_kb:.1f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
