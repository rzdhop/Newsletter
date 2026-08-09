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

### Depth contract

This newsletter covers offensive technique at full mechanism depth. Depth is
the deliverable, not a risk to be managed — a treatment that stops short of the
mechanism is useless to its reader and fails the brief. The boundary below is
narrow and categorical; everything outside it is in scope at whatever depth the
published source supports.

**In scope, at full depth.** Non-exhaustive, and the absence of a technique
from this list is not a reason to soften it:

- **Technique internals** — injection primitives, direct and indirect syscalls,
  SSN resolution, Hell's Gate and Halo's Gate, unhooking via a fresh ntdll
  mapping, ETW and AMSI patching, sleep obfuscation (Ekko, Foliage, Cronos),
  COFF and BOF loading, kernel callback removal, TLS callback abuse, module
  stomping, hardware-breakpoint hooking, call-stack spoofing, PE and loader
  internals.
- **Exploitation** — memory-corruption classes, heap grooming and shaping, ROP
  and JOP chains, type confusion, race conditions, sandbox and kernel escape
  reasoning, exploitability analysis.
- **Platform trust models** — which assumption the OS, the hypervisor or the
  security product is making, and the precise conditions under which it stops
  holding.
- **Analysis** — vulnerability research, adversarial simulation, detection
  engineering, incident reconstruction.
- **Concrete artefacts** — real API names, real structure layouts, real call
  sequences, and code extracts quoted or adapted from the source under
  discussion. Vagueness here is a failure, not caution.

**Out of scope — categorical.** No framing, format or audience changes these. A
course, a lab exercise and a newsletter are the same thing to this list:

1. **Self-propagating code.** Worm propagation logic, autonomous spread
   mechanics, the routine by which a compromise reaches the next host.
2. **Mass credential or secret harvesting tooling, and mass exfiltration
   tooling.** Includes CI/CD runner secret-extraction implementations.
3. **Ransomware and destructive payloads.** Encryption routines, key handling
   for extortion, wipers.

**Out of scope — editorial.** These are the newsletter's own choices, not
policy boundaries:

4. Anything aimed at a live third-party system rather than a lab.
5. Novel technique development — designing an evasion or a bypass that does not
   already exist in the literature you are citing. See rule 4b of `brief.md`.

The distinction matters when you hit friction. Items 1–3 are fixed and apply on
every surface. Items 4–5 are the brief's identity and are equally binding, but
they are ours.

### Covering a campaign whose payload is out of scope

An attack built on 1–3 is still legitimate subject matter. What is excluded is
the reproduction of the payload mechanics, not the analysis of the event. A worm
campaign is covered at: timeline, initial access vector, the trust relationship
abused, blast radius, C2 architecture at design level, the telemetry that
existed and went unread, and the defensive controls that would have changed the
outcome. That is a complete Partie 04. The propagation routine adds nothing the
reader uses.

If a subject cannot be covered at all without reproducing 1–3, it is not a
subject. Note it in one line and take the next candidate from the reserve.

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

**Carry a reserve.** Keep the two or three strongest candidates you did *not*
promote to a deep-dive, with their primary sources, as a short reserve list in
your working notes. The scope gate in Step 3 and the safeguard procedure below
both substitute from this list. Rebuilding a candidate pool at 03:00 because one
subject was dropped means paying for a research sweep you have already done.

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

**Scope gate — apply it here, not at drafting time.** Before committing to a
subject, check it against the *Out of scope* list in Context and scope above.
The question is not "is this topic sensitive" — most of this field is — but
"can this be covered as analysis of published work, at the depth the brief
demands, without the piece becoming the thing itself?" A technique whose
published source is a full weaponised implementation, where the only honest
2 500 words would amount to reproducing it, fails the gate. Say so in one line
in your notes and take the next candidate from the reserve.

This check is cheap at selection and expensive at 2 500 words. A subject that
fails it after drafting has cost the run an hour and may cost it the morning.

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

**Apply the scope gate here, exactly as Step 3 applies it to the deep-dives.**
The gate was written for Parties 02 and 03, and that omission is what let a
self-propagating worm through unchallenged on 2026-08-07. Ask the same question:
can this chain be covered as analysis of public reporting, at the depth the
brief demands, without the piece reproducing carve-outs 1–3?

For most campaigns the answer is yes, *including* campaigns whose payload is out
of scope — see *Covering a campaign whose payload is out of scope* above. The
gate fails only where the chain's sole technical content **is** the excluded
mechanic. Note the decision in one line and take the next candidate from the
Step 2 reserve.

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

### Extraction-prompt discipline

Every `WebFetch` and every subagent brief is itself a request that is screened.
An extraction prompt asks for **the analysis inputs the part consumes**, never
for a reproduction of the artefact under analysis.

This is not a softening. The compliant form below returns everything a Partie 04
prints; the blocked form additionally requested material the part was never
going to use, and cost the run of 2026-08-07 its entire session.

```text
# BLOCKED — requests reproduction of the artefact
Full technical detail of the ChainDrop npm worm: the smart-contract C2 routing
mechanism on Ethereum (which contract, how the malware reads the C2 address
from the blockchain), GitHub Actions runner secret extraction, self-propagation
logic, affected package count and download volume, the compromised maintainer
vector, timeline with dates, and all IOCs. Preserve identifiers, function
names, wallet/contract addresses, and hashes.

# COMPLIANT — requests the analysis inputs
From this report, extract for an incident analysis:
  - the timeline with dates, from first compromise to public disclosure
  - the initial access vector and how maintainer trust was abused
  - blast radius: package count, download volume, downstream orgs affected
  - which defensive controls existed at each phase, and which were not acted on
  - what the reporting establishes, versus what it leaves as inference
  - the C2 design at architectural level only: why blockchain-hosted C2 resists
    takedown compared with DNS or hardcoded IPs
Do not reproduce propagation or credential-harvesting implementation detail;
the analysis does not use it.
```

Check every extraction prompt against three questions before sending it:

1. **Does each requested item appear in the part's output?** If the part will
   never print it, do not ask for it. "All IOCs" and "preserve hashes" fail this
   on a newsletter that prints neither.
2. **Does it ask to preserve implementation identifiers?** Phrases like *full
   technical detail*, *preserve function names*, *preserve identifiers* convert
   an analysis request into an extraction request. Rewrite.
3. **Does it name a mechanic from carve-outs 1–3?** *Self-propagation*, *secret
   extraction*, *encryption routine*. Rewrite to the architectural or impact
   level, or drop the item.

The same three questions apply to deep-dive research in Step 3. They are
cheapest at the prompt and most expensive after a session is lost.

---

## Step 5 — Write

French. Technical terms in English. The voice section of `brief.md` is binding.

Target ~10 000 words total, **as a target and not a floor**. If a part has no
solid material, it gets an `empty` block and one honest sentence. Never pad.

Number sources continuously across the whole issue: if Partie 01 ends at [4],
Partie 02 starts at [5].

---

## Step 6 — Emit the fragments

**Write each part to disk the moment it is finished. Do not hold the issue in
context until the end.**

```
work/meta.json      the `meta`, `preheader` and `tldr` fields below
work/part-01.json   one part object
work/part-02.json
work/part-03.json
work/part-04.json
```

Write `work/meta.json` first, as soon as the issue number and theme are settled
— before Partie 01 is drafted. It is the one fragment that cannot be defaulted,
and an issue whose meta never landed is unpublishable no matter how many parts
survived.

This is the mechanism that makes a safeguard block cost a part instead of a
morning. `scripts/assemble.py` merges the fragments into `content.json` and
substitutes the `empty` component for anything missing, so an issue that lost
Partie 03 still ships with Parties 01, 02 and 04 intact. Held in context
instead, a single blocked request destroys all four.

The schema below is the contract with `render.py`. You never write HTML — you
write content, and the renderer produces the markup. This is what makes design
drift impossible. The `parts` array is shown inline for readability; on disk
each element is its own `work/part-NN.json` file.

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

## Step 7 — Update the ledger

Write every subject covered today into `state/topics-index.json`. Per subject:
issue number, date, part, domain, a two-sentence summary, and the source URLs.
This is what makes rule 3 of `brief.md` work tomorrow.

**Do it before publishing, not after.** A ledger update written afterwards needs
a second commit that a run ending early will never make — which is how issue
413's subjects nearly went unrecorded, leaving the next run free to repeat them.
`publish.sh` warns if it finds no entry for today's issue, but a warning is not
a substitute for the entry.

---

## Step 8 — Publish

```bash
scripts/publish.sh work/
```

One command. It assembles the fragments, renders, checks the 90 KB digest
budget, builds the permalinks, commits, pushes `HEAD:main`, verifies the push
landed, and only then queues the issue and cancels the dead-man alert.

Every one of those steps used to live here as a separate instruction, and each
was a point where a blocked session could strand a finished issue. The ordering
inside the script is load-bearing and is documented in its comments — in
particular the hash comparison against `origin/main`, which refuses to deliver a
mail whose embedded permalink would 404, and which was the single largest defect
of the 2026-08-05 run.

**If `publish.sh` fails, read its output and stop.** It exits non-zero only on
conditions the operator must see: no surviving fragment, a digest that overflows
at one part, or a push that did not land. In all three the dead-man alert is left
armed on purpose.

**If this session is blocked before you reach this step**, the operator runs the
identical command by hand and the issue ships from the fragments that survived.
That is the whole reason the tail is a script.

### Then — write the archive manifest to Google Drive

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

## Safeguard interruptions

Anthropic applies real-time cyber safeguards on Opus and Sonnet models. They
screen two tiers: **prohibited use**, which is fixed for everyone, and
**high-risk dual use**, which the Cyber Verification Program adjusts for
verified organisations. This newsletter's CVP is approved and org-verified, so
dual-use friction should be rare. Carve-outs 1–3 of the depth contract are the
prohibited tier, and CVP does not lift them.

**A block is terminal for the session, not for the turn.** This is the part the
previous version of this section got wrong. Observed behaviour is that the block
state is sticky and not model-specific: once a session trips, every subsequent
request fails regardless of content — including `git push` and
`python3 scripts/deliver.py send`. There is no substituting a subject and
carrying on inside the same session. There is no retrying on another model. The
session is over.

Three consequences, in order:

1. **Prevention is the only control that works.** The depth contract, the
   extraction-prompt discipline in Step 4, and the scope gate applied at
   selection in Steps 3 and 4 are the mechanism. All three are cheap; a lost
   session costs the morning.
2. **Recovery lives outside the session.** `scripts/publish.sh` owns render, split,
   ledger, commit, push and deliver, and executes on whatever parts completed. A
   trip during Partie 03 still ships an issue carrying Parties 01, 02 and 04,
   because each part was written to `work/part-NN.json` the moment it was
   finished. Never put a delivery step inside a drafting session.
3. **Logging is the operator's job once a session is hot.** A blocked session
   cannot write `state/safeguard-log.json` — it cannot write anything. If you
   are still able to write, record the date, issue number, part, subject,
   primary source URL, the exact message and the request id. If you are not,
   the run log at claude.ai/code/routines carries the same evidence and the
   operator transcribes it. That log is the evidence base for an appeal.

Three things you must **not** do, in any circumstance:

- **Do not reword the request to get the same content past the check.** The
  safeguard is a control the operator is subject to, not an obstacle between you
  and the issue. Rephrasing to evade it is circumvention regardless of how
  defensible the subject is, and it would put the newsletter's account at risk
  for the sake of one deep-dive.
- **Do not retry on a different or weaker model.** The safeguards apply across
  Opus and Sonnet alike, so this does not work; and a run that silently
  downgrades its own model produces exactly the shallow output the Model policy
  section exists to prevent. If quality tracks capability, the fallback for a
  blocked subject is a *different subject at full depth*, never the same subject
  at reduced depth.
- **Do not weaken the depth contract to make a subject fit.** Carve-outs 1–3 are
  not adjustable, and 4–5 are the newsletter's editorial identity.

If a block is hit on material that is plainly dual-use rather than prohibited,
that is a false positive and the appeal path exists for it: the report/appeal
form at <https://claude.com/form/cyber-block-false-positive-report-cvp-rejection-appeal>,
supported by `state/safeguard-log.json`. That is an operator action tracked in
`CHECKLIST.md`, not something a run performs for itself.

---

## Failure handling

Distinguish a part that cannot be written from a run that cannot continue. Only
the second one kills the issue.

**A part that cannot be written** — no material, or a subject dropped at the
scope gate with the reserve exhausted — gets an `empty` block and one honest
sentence, written to its `work/part-NN.json` as normal. The run continues. This
is degradation working as designed and it does not warrant an alert.

**A part killed by a safeguard block** never gets written at all, because the
session that would have written it is finished. Nothing is required of you here:
the fragment is simply absent, and `assemble.py` substitutes the same `empty`
component when the operator runs `publish.sh`. Do not attempt to recover inside
a blocked session.

**A run that cannot continue** — preflight failed, the push to `main` did not
land, `split.py` cannot fit even one part, or no fragment survived — means
**stop and leave the dead-man alert armed**. Do not send a half-issue and do not
cancel the alert. A missing issue the operator knows about is strictly better
than a padded one they have to read.

The line between them: if at least one part carries real, sourced, non-padded
material and the permalink resolves, deliver. Otherwise, stop.
