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

## Step 0 — Preflight, then arm the dead-man switch (FIRST, before any research)

```bash
python3 scripts/preflight.py        # exits 1 on a broken environment
python3 scripts/deliver.py arm
```

`preflight.py` validates the routine environment before a single token of
research is spent. It exists because the environment is configured through a
web UI and is therefore not version-controlled, so it drifts silently. Each of
its checks corresponds to a failure that has already cost a run:
`CLAUDE_CODE_SUBAGENT_MODEL` holding an invalid alias (every subagent dies at
spawn), Cloudflare rejecting our User-Agent (`arm` fails, switch disarmed),
`RESEND_MGMT_KEY` missing (the alert cannot be cancelled). **If it exits
non-zero, stop.** Report the failed checks and do not arm.

`arm` then queues a "no issue this morning" alert for the next 06:00
Europe/Paris. If this run dies at any later point, that alert still fires and
the operator learns about it at 06:00 instead of by noticing an absence.
Step 8 cancels it.

**Do not skip either command and do not move them later.** Their entire value
is that they happen before anything that can fail.

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
Set `"last": true` on the final `item` of a part.

`url_label` should contain a **literal U+200B zero-width space** after the
domain so long URLs wrap. Write the actual character, never the `&#8203;`
entity: `url_label` is a plain-text field, so the renderer escapes it and the
entity ships as six visible characters in the middle of the link. The renderer
converts the literal character to an entity for you, as it does every other
non-ASCII character.

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

The order below is load-bearing. Two of these steps are in the position they
are because the alternative has already failed in production.

### 8.1 — Update the ledger BEFORE committing

Write every subject covered today into `state/topics-index.json`. Per subject:
issue number, date, part, domain, a two-sentence summary, and the source URLs.
This is what makes rule 3 work tomorrow.

Do it **now**, not after the commit. A ledger update written afterwards needs a
second commit that a run ending early will never make — which is how issue
413's subjects nearly went unrecorded, leaving the next run free to repeat them.

### 8.2 — Build permalinks, then commit everything together

```bash
python3 scripts/build_index.py
git add issues/ state/ index.html <NNN>/
git commit -m "issue <NNN> - <subject of the day>"
```

`build_index.py` publishes `/<NNN>/index.html` and regenerates the archive
index; both are part of the same artefact as the issue and belong in the same
commit. This commit is also what resets GitHub's 60-day scheduled-workflow
inactivity timer.

### 8.3 — Push to `main`, explicitly

```bash
git push origin HEAD:main
```

A cloud routine starts on an auto-created feature branch. GitHub Pages serves
**only the default branch**, so an issue committed and left on the feature
branch produces a permalink that 404s — in a mail that has already been sent.
A bare `git push` is not sufficient and was the single largest defect of the
2026-08-05 run.

### 8.4 — Verify the push landed, before delivering

```bash
git fetch origin main
git rev-parse HEAD origin/main    # the two hashes MUST match
```

The mail embeds the permalink, so delivery must not happen until the content
behind that permalink exists. If the hashes differ, stop: leave the dead-man
alert armed and report the failure. If the push was rejected by branch
protection, that is a configuration problem for the operator, not something to
work around by delivering anyway.

### 8.5 — Deliver

```bash
python3 scripts/deliver.py send issues/<YYYY>/<MM>/<NNN>/ <NNN>
```

Queues the issue for exactly 06:00 Europe/Paris and then attempts to cancel the
dead-man alert. Cancellation needs `RESEND_MGMT_KEY`; if it is absent or the
call fails, the script warns and exits 0 on purpose — the issue is already
queued, and reporting a delivered issue as a failed run costs more than a
spurious alert mail.

### 8.6 — Write the archive manifest to Google Drive

Write `archive/<YYYY>/<MM>/offsec-quotidien-<NNN>.MANIFEST.md` to Google Drive
via the connector, containing: issue number and date, theme, part titles, word
and source counts, the Resend queue id, the commit hash on `main`, the Pages
permalink, and the **SHA-256 sum and byte size of both `full.html` and
`digest.html`**.

The manifest is the specified deliverable here — not a degraded substitute for
the HTML. The Drive connector only accepts content passed as a parameter, with
no path-based upload, so mirroring a 157 KB document would mean retranscribing
it through the model: expensive, and one altered byte produces a silently
corrupt archive, which is worse than no archive. The issue already exists in
three real copies (the repo, the Pages permalink, the mail attachment), so
Drive's job is to be the index that lets any of the three be verified.

If the connector fails, **log it and carry on** — the mail is already queued.
A Drive hiccup must never cost the operator a morning.

---

## Failure handling

If you cannot complete the issue, **stop and leave the dead-man alert armed**.
Do not send a half-issue and do not cancel the alert. A missing issue the
operator knows about is strictly better than a padded one they have to read.
