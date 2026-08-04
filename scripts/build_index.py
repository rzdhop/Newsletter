#!/usr/bin/env python3
"""
OffSec Quotidien - GitHub Pages archive builder.

Two jobs:

  1. Publish a clean permalink for each issue at /<NNN>/index.html, so the
     "lire la suite" link in the email is rzdhop.github.io/Newsletter/413
     rather than a path exposing the internal issues/YYYY/MM layout. The email
     is the durable artefact - its links must survive any future reorganisation
     of the repository.

  2. Regenerate the archive index at /index.html.

Run after split.py, before committing.

Usage:
    python3 scripts/build_index.py
"""

import os
import re
import shutil
import sys
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ISSUES_DIR = os.path.join(REPO_ROOT, "issues")

TITLE_RE = re.compile(r"<title>OffSec Quotidien n&deg;(\d+)</title>")
# The header carries "<date> · <time> · <words> mots · ~<n> min" in a mono cell.
META_RE = re.compile(
    r"color:#c8c3b9;\">(.*?)&nbsp;&middot;&nbsp;(.*?)&nbsp;&middot;&nbsp;(.*?)&nbsp;&middot;&nbsp;(.*?)</td>"
)
THEME_RE = re.compile(r"color:#f5f3ef;\">(.*?)</span> &mdash; (.*?)</td>")


def discover():
    """Yield (number, date_label, words, theme, source_path), newest first."""
    found = []
    for root, _dirs, files in os.walk(ISSUES_DIR):
        if "full.html" not in files:
            continue
        path = os.path.join(root, "full.html")
        with open(path, encoding="utf-8") as handle:
            # The header sits in the first few KB; no need to read a 180 KB file.
            head = handle.read(20000)

        title = TITLE_RE.search(head)
        if not title:
            print(f"  skipped (no issue number): {path}")
            continue

        meta = META_RE.search(head)
        theme = THEME_RE.search(head)
        found.append({
            "n": int(title.group(1)),
            "date": meta.group(1).strip() if meta else "",
            "words": meta.group(3).strip() if meta else "",
            "theme": theme.group(1).strip() if theme else "",
            "path": path,
        })

    return sorted(found, key=lambda issue: issue["n"], reverse=True)


def publish_permalinks(issues):
    for issue in issues:
        target_dir = os.path.join(REPO_ROOT, str(issue["n"]))
        os.makedirs(target_dir, exist_ok=True)
        shutil.copyfile(issue["path"], os.path.join(target_dir, "index.html"))


def build_index(issues):
    rows = "\n".join(
        f'      <tr>'
        f'<td style="padding:10px 12px; border-top:1px solid #dcd8d0; '
        f'font-family:Consolas,monospace; font-size:13px; color:#7a4a2e; font-weight:700;">'
        f'<a href="./{issue["n"]}/" style="color:#7a4a2e; text-decoration:none;">n&deg;{issue["n"]}</a></td>'
        f'<td style="padding:10px 12px; border-top:1px solid #dcd8d0; '
        f'font-family:Consolas,monospace; font-size:12px; color:#7d7a73;">{issue["date"]}</td>'
        f'<td style="padding:10px 12px; border-top:1px solid #dcd8d0; '
        f'font-family:-apple-system,sans-serif; font-size:14px; color:#1e1d1b;">'
        f'<a href="./{issue["n"]}/" style="color:#2f5474;">{issue["theme"] or "—"}</a></td>'
        f'<td style="padding:10px 12px; border-top:1px solid #dcd8d0; '
        f'font-family:Consolas,monospace; font-size:12px; color:#7d7a73;">{issue["words"]}</td>'
        f'</tr>'
        for issue in issues
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OffSec Quotidien &mdash; archive</title>
</head>
<body style="margin:0; padding:0; background-color:#e6e4df;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse; background-color:#e6e4df;">
<tr><td align="center" style="padding:24px 12px 40px 12px;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="820" style="width:100%; max-width:820px; border-collapse:collapse; background-color:#fbfaf8; border:1px solid #cfccc4;">
  <tr><td style="padding:26px 30px 20px 30px; background-color:#1e1d1b; border-bottom:3px solid #7a4a2e;">
    <div style="font-family:Consolas,monospace; font-size:11px; letter-spacing:2px; text-transform:uppercase; color:#a8a49b; padding-bottom:8px;">Archive</div>
    <div style="font-family:-apple-system,sans-serif; font-size:27px; font-weight:700; color:#f5f3ef;">OffSec Quotidien</div>
    <div style="font-family:Consolas,monospace; font-size:13px; color:#c8c3b9; padding-top:8px;">{len(issues)} num&eacute;ros &middot; g&eacute;n&eacute;r&eacute; le {datetime.utcnow().strftime('%Y-%m-%d')}</div>
  </td></tr>
  <tr><td style="padding:0 20px 24px 20px;">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%; border-collapse:collapse;">
{rows}
    </table>
  </td></tr>
</table>
</td></tr>
</table>
</body>
</html>
"""


def main():
    if not os.path.isdir(ISSUES_DIR):
        print(f"No issues directory at {ISSUES_DIR}; nothing to build.")
        return 0

    issues = discover()
    if not issues:
        print("No rendered issues found.")
        return 0

    publish_permalinks(issues)
    with open(os.path.join(REPO_ROOT, "index.html"), "w", encoding="utf-8") as handle:
        handle.write(build_index(issues))

    print(f"Published {len(issues)} permalink(s); newest is n°{issues[0]['n']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
