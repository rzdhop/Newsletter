#!/usr/bin/env python3
"""
OffSec Quotidien - digest/full splitter.

Gmail clips a message when its HTML body exceeds roughly 102 KB. Attachments
and linked files are exempt, so the strategy is:

  full.html    every part, ~10k words, attached to the mail and published to
               GitHub Pages. Never truncated.
  digest.html  as many complete parts as fit under the byte budget, rendered
               from the SAME content tree so the two can never disagree.

Parts are dropped whole, never mid-article: a reader should either get a part
in full or get a clear pointer to it, never a sentence cut in half.

Usage:
    python3 scripts/split.py content.json out/
"""

import json
import os
import sys

import render

# Gmail clips at ~102 KB of HTML.
#
# render.py emits pure ASCII (every accent is a named entity), which makes the
# quoted-printable inflation applied in transit almost free: measured at +3.7%
# on a full issue, because only the soft line breaks on long style attributes
# cost anything. Had the body stayed raw UTF-8, French accents would each have
# become a 6-byte '=C3=A9' sequence and the inflation would have been 20-30%.
#
# So the usable ceiling is 102 / 1.04 = ~98 KB. 90 KB leaves an 8 KB margin for
# a heavier-than-usual issue and for Gmail measuring slightly differently than
# documented. Raising this further is not worth the risk of a clipped issue.
BUDGET_BYTES = 90 * 1024

CONTINUATION_TEMPLATE = (
    'Les parties {parts} de ce num&eacute;ro ne tiennent pas dans le corps du mail '
    '(limite de {limit}&nbsp;Ko impos&eacute;e par Gmail). Elles sont '
    '<strong>compl&egrave;tes dans la pi&egrave;ce jointe</strong> '
    '<span style="font-family:Consolas,\'SF Mono\',Menlo,monospace; font-size:14px; '
    'background-color:#eeece6; padding:1px 4px;">offsec-quotidien-{issue}.html</span> '
    'et en ligne&nbsp;: <a href="{url}" style="color:#2f5474; text-decoration:underline;">{label}</a>.'
)


def byte_size(text):
    return len(text.encode("utf-8"))


def build_digest(content):
    """
    Return (html, included_part_numbers).

    Greedy from the full set downwards: try every part, then drop the last part
    repeatedly until it fits. Dropping from the end preserves reading order and
    keeps Partie 01 (the news review, the most time-sensitive material) inline
    for as long as possible.
    """
    all_numbers = [part["n"] for part in content["parts"]]

    for cutoff in range(len(all_numbers), 0, -1):
        included = all_numbers[:cutoff]
        excluded = all_numbers[cutoff:]

        # Work on a shallow copy so the continuation notice never leaks into the
        # full render, which must stay clean for the Pages archive.
        candidate = dict(content)
        if excluded:
            issue = content["meta"]["issue"]
            url = f"{content['meta']['archive_url'].rstrip('/')}/{issue}"
            candidate["continuation"] = CONTINUATION_TEMPLATE.format(
                parts=" et ".join(f"{n:02d}" for n in excluded),
                limit=BUDGET_BYTES // 1024,
                issue=issue,
                url=url,
                label=url.replace("https://", ""),
            )
        else:
            candidate.pop("continuation", None)

        html = render.render(candidate, parts_to_include=included)
        if byte_size(html) <= BUDGET_BYTES:
            return html, included

    # Even Partie 01 alone overflows. Emit it anyway and let the caller warn:
    # shipping a clipped issue beats shipping nothing.
    return html, all_numbers[:1]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1

    content_path, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    with open(content_path, encoding="utf-8") as handle:
        content = json.load(handle)

    full_html = render.render(content)
    full_path = os.path.join(out_dir, "full.html")
    with open(full_path, "w", encoding="utf-8") as handle:
        handle.write(full_html)

    digest_html, included = build_digest(content)
    digest_path = os.path.join(out_dir, "digest.html")
    with open(digest_path, "w", encoding="utf-8") as handle:
        handle.write(digest_html)

    full_kb = byte_size(full_html) / 1024
    digest_kb = byte_size(digest_html) / 1024
    total = len(content["parts"])

    print(f"full.html    {full_kb:6.1f} KB   parts 1-{total}")
    print(f"digest.html  {digest_kb:6.1f} KB   parts {included} "
          f"(budget {BUDGET_BYTES // 1024} KB)")

    if digest_kb > BUDGET_BYTES / 1024:
        print("WARNING: digest exceeds budget even at one part - it will be clipped.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
