# OffSec Quotidien — generation runbook

You are generating today's issue. This file is the complete procedure; the
routine's saved prompt does nothing but point you here.

Read `brief.md` before starting. It is the editorial standard and it overrides
convenience at every step.

---

## Step 0 — Arm the dead-man switch (FIRST, before any research)

```bash
python3 scripts/deliver.py arm
```

This queues a "no issue this morning" alert for the next 06:00 Europe/Paris.
If this run dies at any later point, that alert still fires and the operator
learns about it at 06:00 instead of by noticing an absence. Step 8 cancels it.

**Do not skip this and do not move it later.** Its entire value is that it
happens before anything that can fail.

---

## Step 1 — Load state

Read, in this order:

1. `state/topics-index.json` — every subject ever covered. Anything with an
   entry in the last 90 days is off-limits as a new subject.
2. `refs/erebos-inventory.md` — implemented vs. candidate techniques.
3. Fetch <https://github.com/rzdhop/Erebos-Zero> README and reconcile it with
   the inventory. The repository moves; a stale inventory sends the newsletter
   over ground already covered.
4. `sources.yaml` — the source registry.

Determine the issue number: highest directory under `issues/` plus one. The
first automated issue is **413** (the design reference was 412).

---

## Step 2 — Collect (Partie 01 material)

Sweep Tier 4 and Tier 5 for the **current week**. For every candidate capture:
source, date, URL, and one sentence on why it matters.

Then do the thing that makes this worth reading: **follow each candidate up to
its primary source.** A BleepingComputer piece about a Quarkslab paper is a
pointer to the Quarkslab paper. Cite the paper.

Classify each retained item into exactly one tag: `quick`, `deep-dive`,
`PoC/lab`, `archive`.

Target 6–10 items. If the week is thin, say so in an `empty` block and take an
older red-team subject as a blogpost instead — do not inflate the count.

---

## Step 3 — Choose the deep-dives (Parties 02 and 03)

Apply `refs/erebos-inventory.md` selection procedure:

- Not in `topics-index.json` within 90 days.
- Not already implemented in Erebos-Zero.
- Prefer a candidate whose prerequisite *is* implemented, so the deep-dive
  reads as the operator's next commit rather than a disconnected tutorial.
- **Partie 02 and Partie 03 must be in different domains** (maldev / hardware /
  web / kernel). Two Windows-maldev pieces in one issue is a weaker edition.
- Saturday and Sunday: lighter subjects.

Each deep-dive needs: a plan (`steps` block), real technical substance, at
least one code block where code clarifies better than prose, a comparison
table where there is something to compare, concrete proposed improvements, and
a sources block.

---

## Step 4 — Build Partie 04 (autopsie)

Pick a recent attack with enough public technical detail to reconstruct. Tie it
to at least one Tier 5 anchor (CISA KEV, ZDI, LOLDrivers).

Break the chain into timestamped phases (`autopsy` block): initial access,
execution, escalation, evasion, exfiltration — whatever the chain actually did.
Judge it technically: what was novel, what was recycled, what would have caught
it. Explain to the depth where a reader could approach reproduction in a lab.

Where you are inferring rather than reporting, use the `warning` component.

---

## Step 5 — Write

French. Technical terms in English. The voice section of `brief.md` is binding.

Target ~10 000 words total, **as a target and not a floor**. If a part has no
solid material, it gets an `empty` block and one honest sentence. Never pad.

Number sources continuously across the whole issue: if Partie 01 ends at [4],
Partie 02 starts at [5].

---

## Step 6 — Emit `content.json`

The schema below is the contract with `render.py`. You never write HTML — you
write content, and the renderer produces the markup. This is what makes design
drift impossible.

Fields ending in `_html` accept inline markup (`<span>`, `<strong>`, `<a>`).
Everything else is plain text and gets escaped. **You do not need to write HTML
entities**: the renderer converts every accent and every piece of French
punctuation automatically. Write natural French.

```jsonc
{
  "meta": {
    "issue": 413,
    "date_label": "mardi 4 août 2026",
    "time_label": "06:00 CEST",
    "words": 10240,                    // real count, not the target
    "reading_minutes": 51,             // words / 200
    "diffusion": 1,
    "theme": { "title": "...", "subtitle": "..." },
    "generated_at": "2026-08-04 à 02:41 UTC",
    "pipeline": "v1.0",
    "window": "2026-07-28 06:00 → 2026-08-04 06:00 UTC",
    "sources_scanned": 91,             // be honest
    "sources_kept": 13,
    "archive_url": "https://rzdhop.github.io/Newsletter",
    "recipients": 1
  },
  "preheader": "one line, shown next to the subject in the inbox",
  "tldr": ["bullet 1", "bullet 2", "bullet 3",
           "<span style=\"font-weight:700;\">À faire aujourd'hui :</span> concrete dated action"],
  "parts": [
    {
      "n": 1,
      "title": "Le fil de la semaine",          // used in the sommaire
      "count_label": "9 items",
      "title_html": "Le fil de la semaine",     // used in the part header
      "subtitle": "Neuf items retenus sur 91 candidats.",
      "kind": null,                              // or "Deep-dive" / "Autopsie d'attaque"
      "blocks": [ /* see block types below */ ],
      "sources": [
        { "n": 1, "date": "2026-07-31", "author": "Microsoft",
          "title": "Recommended driver block rules",
          "url": "https://learn.microsoft.com/..." }
      ]
    }
  ]
}
```

### Block types

| `type` | Fields | Use for |
|---|---|---|
| `prose` | `html` | body paragraphs |
| `item` | `tag`, `title_html`, `why_html`, `url`, `url_label`, `date_label`, `last` | Partie 01 news items |
| `code` | `label`, `code`, `caption?` | source extracts |
| `warning` | `html` | unverified claims |
| `steps` | `title`, `steps[]` | deep-dive plan |
| `table` | `headers[]`, `rows[][]`, `widths?`, `caption?` | comparisons (4 columns) |
| `autopsy` | `steps[]` of `{stamp, phase, text_html}` | Partie 04 attack chain |
| `empty` | `headline`, `detail` | a section with nothing solid to say |

`tag` must be exactly one of `quick`, `deep-dive`, `PoC/lab`, `archive`.
`url_label` should contain `&#8203;` after the domain so long URLs wrap.
Set `"last": true` on the final `item` of a part.

---

## Step 7 — Render and check the budget

```bash
python3 scripts/split.py content.json issues/<YYYY>/<MM>/<NNN>/
```

Produces `full.html` (every part) and `digest.html` (as many complete parts as
fit under 90 KB, plus a pointer to the rest). Parts are dropped whole, never
mid-article.

Expect roughly: full ≈ 140–180 KB for a 10k-word issue, digest ≈ Parties 01–02.
If `split.py` exits non-zero, the digest overflowed even at one part — shorten
Partie 01 and re-render.

Verify before continuing:
- both files are pure ASCII (the renderer guarantees this; confirm anyway)
- the digest carries the continuation notice when parts were dropped
- no `empty` block was used to dodge work that had material available

---

## Step 8 — Publish, archive, deliver

```bash
# 1. commit — this is the archive AND it resets GitHub's 60-day
#    scheduled-workflow inactivity timer
git add issues/ state/
git commit -m "issue <NNN> — <subject of the day>"
git push

# 2. deliver: queue for exactly 06:00 Europe/Paris and cancel the alert
python3 scripts/deliver.py send issues/<YYYY>/<MM>/<NNN>/ <NNN>
```

Then update `state/topics-index.json` with every subject covered — this is what
makes rule 3 work tomorrow. Include, per subject: issue number, date, part,
domain, a two-sentence summary, and the source URLs.

Finally, mirror `full.html` into Google Drive under
`/Newsletter/archive/<YYYY>/<MM>/` using the Drive connector. If that fails,
**log it and carry on** — the mail is already queued and the repo already has
the archive. A Drive hiccup must never cost the operator a morning.

---

## Failure handling

If you cannot complete the issue, **stop and leave the dead-man alert armed**.
Do not send a half-issue and do not cancel the alert. A missing issue the
operator knows about is strictly better than a padded one they have to read.
