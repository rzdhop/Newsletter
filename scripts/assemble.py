#!/usr/bin/env python3
"""
OffSec Quotidien - fragment assembler.

Merges the per-part fragments written during drafting into the single
`content.json` that `split.py` and `render.py` consume.

Why fragments exist at all
--------------------------
A cyber-safeguard block is terminal for the model session that hits it: once a
session trips, every subsequent request fails regardless of content, including
the ones that would have written the remaining parts. If the whole issue lives
in the model's context until Step 6, a trip during Partie 03 destroys Parties
01, 02 and 04 as well, and the morning is lost.

Writing each part to disk the moment it is finished turns that total loss into a
partial one. This script then builds a publishable issue out of whatever
survived, substituting the `empty` component for parts that never landed -
which is exactly what rule 1 of `brief.md` prescribes for a part with no
material, and what the reader already expects to see on a thin day.

Expected layout, all written by the drafting session:

    work/meta.json      meta + preheader + tldr
    work/part-01.json   one part object, schema per prompt.md Step 6
    work/part-02.json
    work/part-03.json
    work/part-04.json

Usage:
    python3 scripts/assemble.py work/ content.json
"""

import json
import os
import sys

# Parts the issue is contractually expected to carry. A fragment missing from
# this range is replaced by an `empty` block rather than silently shrinking the
# issue, so a dropped part is visible to the reader and to the archive instead
# of being indistinguishable from an issue that never planned to have one.
EXPECTED_PARTS = (1, 2, 3, 4)

# Titles used only when a fragment is absent. They must still read as deliberate
# editorial choices, because that is what the reader sees.
FALLBACK_TITLES = {
    1: "Le fil de la semaine",
    2: "Deep-dive",
    3: "Deep-dive",
    4: "Autopsie d'attaque",
}

FALLBACK_KINDS = {1: None, 2: "Deep-dive", 3: "Deep-dive", 4: "Autopsie d'attaque"}


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def empty_part(number):
    """
    Build a placeholder part carrying the `empty` component.

    `render.py` requires `n`, `title` and `title_html`; everything else is
    optional. The wording is deliberately the honest one from brief.md rule 1
    rather than an apology or an error message - the archive is public, and a
    reader who sees this should read a decision, not a stack trace.
    """
    return {
        "n": number,
        "title": FALLBACK_TITLES[number],
        "title_html": FALLBACK_TITLES[number],
        "count_label": "surface a vide",
        "kind": FALLBACK_KINDS[number],
        "subtitle": "Rien de solide a publier sur cette partie aujourd'hui.",
        "blocks": [{
            "type": "empty",
            "headline": "Surface a vide",
            "detail": "Aucun sujet ne justifiait un traitement de fond sur cette "
                      "partie pour ce numero. Le remplissage est exclu par le "
                      "contrat editorial : mieux vaut une partie vide qu'une "
                      "partie sans substance.",
        }],
        "sources": [],
    }


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1

    work_dir, out_path = sys.argv[1], sys.argv[2]

    meta_path = os.path.join(work_dir, "meta.json")
    if not os.path.exists(meta_path):
        # Without meta there is no issue number, no date and no theme, so there
        # is nothing publishable. This is the one fragment that cannot be
        # defaulted, and failing loudly here leaves the dead-man alert armed.
        print(f"FATAL: {meta_path} missing - nothing publishable.")
        return 1

    content = load_json(meta_path)
    parts, recovered, missing = [], [], []

    for number in EXPECTED_PARTS:
        fragment = os.path.join(work_dir, f"part-{number:02d}.json")
        if os.path.exists(fragment):
            try:
                parts.append(load_json(fragment))
                recovered.append(number)
                continue
            except json.JSONDecodeError as error:
                # A truncated fragment is the signature of a session killed
                # mid-write. Treat it exactly like an absent one: the issue is
                # still worth shipping, and half a part is not.
                print(f"WARNING: part-{number:02d}.json is malformed ({error}); "
                      f"substituting an empty block.")
        parts.append(empty_part(number))
        missing.append(number)

    if not recovered:
        # Every part failed. brief.md's failure rule: stop, do not cancel the
        # alert, do not ship a shell of an issue.
        print("FATAL: no part fragment survived - refusing to publish an empty issue.")
        return 1

    content["parts"] = parts

    # Keep the declared word count honest when parts were dropped. An issue that
    # advertises 10 000 words and delivers 5 000 is a credibility problem the
    # archive keeps forever.
    if missing:
        content.setdefault("meta", {})["words"] = sum(
            part.get("words", 0) for part in parts) or content.get("meta", {}).get("words", 0)

    # Same honesty rule applied to the footer's "Diffusion : N destinataire(s)".
    # The model writes meta.json before the list is ever read, so it can only
    # guess the count; deriving it here from the single source of truth means
    # the footer cannot drift from subscribers.txt. Import is local because a
    # failure to read the list must not stop an otherwise publishable issue.
    try:
        from deliver import recipients
        content.setdefault("meta", {})["recipients"] = len(recipients())
    except Exception as error:  # noqa: BLE001 - assembly must never die on a footer
        print(f"WARNING: recipient count left as declared ({error})")

    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(content, handle, ensure_ascii=False, indent=2)

    print(f"Assembled {out_path}: parts {recovered} recovered"
          + (f", parts {missing} empty" if missing else ", complete issue"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
