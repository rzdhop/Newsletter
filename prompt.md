# OffSec Quotidien — generation runbook

You are generating today's issue. This file is the complete procedure; the
routine's saved prompt does nothing but point you here.

Read `brief.md` before starting. It is the editorial standard and it overrides
convenience at every step.

---

## Context and scope

**What this is.** A published French-language technical newsletter on offensive
security, written for one professional red-team practitioner and archived
publicly at <https://rzdhop.github.io/Newsletter/>. Every issue is fully cited
and every claim traces to a public primary source — Quarkslab, Synacktiv,
SpecterOps, Project Zero, Paged Out!, and the researchers listed in
`sources.yaml`. It is security journalism and technique analysis, in the same
category as the sources it cites.

**The analytical frame.** The newsletter covers offensive technique at full
depth, and that depth is the point — a shallow treatment would be useless to
its reader. The register is *coverage of published work*: you are writing about
research that exists, not producing research that does not.

- Explain **why** a technique works, at the level of the platform's actual
  trust model — which assumption the OS or the security product is making, and
  where that assumption stops holding.
- Use real API names, real structures, real architecture. `NtCreateSection`,
  `PsSetLoadImageNotifyRoutine`, the PEB layout, the SSN table. Vagueness here
  is a failure, not caution.
- **The published source sets the ceiling.** Go as deep as the paper, talk or
  PoC repository actually goes, and cite it. Where you reason past what the
  source establishes, you are inferring — label it with the `warning`
  component. Filling a gap the source left open with your own design work is
  not analysis and is not this newsletter's job.
- Reference public proof-of-concept repositories by name and URL rather than
  reproducing a complete implementation. The reader can follow a citation; a
  reader who wanted a copy-paste implant would not be reading a newsletter.
- Code blocks illustrate the *mechanism* — the specific call sequence or
  structure layout that makes the concept concrete, usually quoted or adapted
  from the source under discussion. They are not deliverable tooling.
- Detection is optional and editorial. Where what a technique costs a defender
  is interesting, say so — it is often the sharpest thing in the piece. Where
  it is not, leave it out. It is not a required section and it is not a
  disclaimer.

**Out of scope**, regardless of how the day's news reads:

- Complete, weaponised, ready-to-run offensive tooling.
- Novel technique development — designing an evasion or a bypass that does not
  already exist in the literature you are citing.
- Anything aimed at a live third-party system rather than a lab.
- Ransomware or destructive-payload construction, and mass data exfiltration
  tooling. These are categorically out; no framing makes them in scope.

None of this reduces technical depth. The deepest published work in this field
— Project Zero's exploitation write-ups, SpecterOps' and MDSec's tradecraft
research — follows exactly this shape: full mechanism, real names, cited
sources.

---

## Model policy

Research sweeps, deep-dive drafting and the attack autopsy are long-context
analytical work over dense primary sources, and issue quality tracks model
capability closely. Run them on Opus. Mechanical, content-free steps — listing
files, validating JSON, checking a byte count, running git — can use anything.

`CLAUDE_CODE_SUBAGENT_MODEL=opus` is set in the routine environment so subagent
work inherits the same default.

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
2. `refs/erebos-inventory.md` — the coverage filter: techniques the reader has
   already implemented and therefore does not need explained.
3. Fetch <https://github.com/rzdhop/Erebos-Zero> README and reconcile it with
   the inventory. The repository moves; a stale filter sends the newsletter
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

Apply the `refs/erebos-inventory.md` selection procedure. In short:

- **The candidate pool is what Step 2 surfaced** — published research from this
  week, or from the archive when the week is thin. Pick the subject because the
  work is technically interesting, not because of any gap in any codebase.
- Not in `topics-index.json` within 90 days.
- Not already implemented in Erebos-Zero (that is dedup, not direction).
- Prefer the candidate with the stronger primary source: a paper, a conference
  write-up or a documented PoC repository supports a deeper issue than a vendor
  summary does.
- **Partie 02 and Partie 03 must be in different domains** (maldev / hardware /
  web / kernel). Two Windows-maldev pieces in one issue is a weaker edition.
- Saturday and Sunday: lighter subjects.

Each deep-dive needs: a plan (`steps` block), real technical substance, at
least one code block where code clarifies better than prose, a comparison table
where there is something to compare, an honest account of the technique's
limits and tradeoffs, and a sources block.

"Limits and tradeoffs" means: what the technique costs in reliability,
footprint or complexity, where the published work says it breaks, which
variants the literature considers superseded, and what a defender pays to see
it when that is the interesting part. This is critique of existing work. It is
not a design brief for the next version of the technique — if the improvement
is not in the literature you are citing, it is out of scope per the frame
above.

---

## Step 4 — Build Partie 04 (autopsie)

Pick a recent attack with enough public technical detail to reconstruct. Tie it
to at least one Tier 5 anchor (CISA KEV, ZDI, LOLDrivers).

Break the chain into timestamped phases (`autopsy` block): initial access,
execution, escalation, evasion, exfiltration — whatever the chain actually did.

Judge it technically, as an expert reviewing someone else's work: what was
genuinely novel, what was recycled from public tooling, which step was the
weakest link, and at which phase it should have been caught. Explain each phase
at the mechanism level — the technique used, why it worked against that target,
and what telemetry existed but was not acted on.

This is reconstruction from public reporting, and public reporting is the
ceiling. The depth to aim for is a reader who understands the chain well enough
to reason about it — why each step worked against that target, what it depended
on, where it was fragile. Where the reporting is thin and you are inferring
rather than reporting, say so with the `warning` component: a reconstructed
chain contains inference, and unlabelled inference is the main way this part
could mislead. Do not fill a gap in the reporting by designing the missing step
yourself.

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
`url_label` should contain a literal U+200B ZERO WIDTH SPACE character after the
domain so long URLs wrap. Write the character itself, not the entity: this field
is escaped like every other plain-text field, so a hand-written `&#8203;` ships
as visible text. The renderer turns the character into `&#8203;` for you.
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
