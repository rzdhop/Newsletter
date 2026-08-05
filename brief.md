# OffSec Quotidien — editorial contract

The newsletter this repository produces. `prompt.md` is the runbook; this file
is the standard the runbook is judged against.

Language: **French**. Technical terms stay in English — *shellcode, syscall,
EDR, call stack spoofing, BOF, hooking*. Do not translate them; French offsec
writing does not.

---

## The four parts

### Partie 01 — Le fil de la semaine
News from the **current week**. Announced upcoming events and the subjects they
concern. Each item: a tag badge, a title, one "Pourquoi ça compte" sentence,
and a dated link.

Tags: `[quick]` cheap to read · `[deep-dive]` costly but worth it ·
`[PoC/lab]` reproducible today · `[archive]` older but newly relevant.
The tag signals **cost of entry, not importance**.

If the week is genuinely thin: take an older red-team subject — the more recent
the better — and break it down as a blogpost instead. A thin week is not a
licence to pad; it is a licence to go to the archive.

### Partie 02 — Deep-dive
One advanced subject drawn from published research: malware technique, hardware
hacking, web exploitation, platform internals. **Advanced only.** No
introductions to XSS, no "what is a buffer overflow".

Ends with an honest account of the technique's **limits and tradeoffs** — what
it costs in reliability, footprint or complexity, where the published work says
it breaks, which variants the literature treats as superseded. Critique of
existing work, not a design brief for the next version of it.

### Partie 03 — Deep-dive
A second subject, same treatment, **a different domain from Partie 02**. Two
Windows-maldev deep-dives in one issue is a weaker edition than one maldev plus
one hardware or web subject.

### Partie 04 — Autopsie d'attaque
A recent attack, judged technically, as an expert would. Every phase explained
to the depth the **public reporting supports** — the technique used, why it
worked against that target, where the chain was fragile. Timestamped phases.
Say plainly when the reporting is thin: reconstructing a chain from a vendor
blog post is inference, inference must be labelled, and a gap in the reporting
is not an invitation to design the missing step.

---

## Rules that override everything else

**1. No padding — ever.**
The word target is ~10 000. It is a target, not a floor. A part with no solid
material uses the "surface à vide" component (`{"type": "empty"}`) and says so
in one honest sentence. Handoff rule 7 wins over the word count, always. An
8 000-word issue where every paragraph earns its place beats a 10 000-word issue
with 2 000 words of filler.

**2. No unsourced claims.**
Every part ends with a sources block. Numbering is continuous across the whole
issue: Partie 01 might end at [4], so Partie 02 starts at [5]. A claim you
cannot cite is a claim you do not make.

**2b. A source you have not read is not a source.**
Never ship a citation marked "non consulté", and never characterise a body of
work you have only seen summarised. Either open the advisory, the paper or the
repository and let what it actually says change the text, or drop the claim
that depended on it.

This rule was written after issue 413. Four Binarly advisories went out marked
unread, and reading them forced a correction: BRLY-2026-038 scores 6.8 and does
claim code execution, which made the line "aucun contournement de secure boot
revendiqué" too strong. The correction was only possible because the advisories
were opened before publication. An unread citation is not a weaker source — it
is an unverified claim wearing a source's clothes, and rule 2 already forbids it.

**3. Never repeat a subject.**
`state/topics-index.json` records everything ever covered. A subject already
there may only be **mentioned** — and a mention is a written summary of what
was said and why it matters again, never a bare link back.

**4. Subjects come from the field; Erebos filters them.**
The candidate pool is what the labs in `sources.yaml` actually published — this
week's papers, talks, advisories and write-ups, or the archive when the week is
thin. Choose the subject whose published work is most worth 2 500 words.

`refs/erebos-inventory.md` is then applied as a filter, not as a selector: a
technique the reader has already implemented is not a deep-dive subject, it is
prior work referenced in one sentence. The inventory says what to *skip*. It
does not say what to write, and a gap in it is not a reason to pick a topic.

**4b. The source sets the ceiling.**
A deep-dive goes as deep as its primary source establishes, and cites it.
Reasoning past the source is inference and gets the `warning` component.
Designing what the source left undone is not this newsletter's job.

**5. Mark what you have not verified.**
Anything not personally tested goes in the `warning` component
(⚠️ Hypothèse non testée). Being wrong is survivable; being confidently wrong
is not. This component existing in the design is a signal about the standard.

**6. Prefer primary sources.**
Tier 4 news exists to *discover* a story. Follow it up to the Tier 1/2 lab that
published the research and cite that. Never cite a news article summarising a
paper when the paper is reachable.

**7. Weekend cadence.**
Saturday and Sunday take lighter subjects — Paged Out! one-pagers, archive
material, hardware entry points, tooling round-ups. This is deliberate load
management across the week, not a drop in standards.

---

## Voice

Written by a practitioner, for one practitioner who already knows the field.

- Assume the reader knows what a syscall is. Do not explain it.
- Prefer the measured number to the adjective. "4 to 40 ms" beats "a brief window".
- When something is uncertain, say which part is uncertain and why.
- No marketing register, no vendor superlatives, no "threat actors leveraged".
- Short sentences carry technical weight better than long ones.

---

## Definition of a good issue

- Every claim traceable to a source in its part's block.
- At least one thing the reader could go and *read* today that he would not
  have found himself.
- No paragraph that could be deleted without losing information.
- Parties 02 and 03 in different domains.
- Partie 04 tied to at least one Tier 5 factual anchor (KEV, ZDI, LOLDrivers).
- Nothing repeated from `topics-index.json` without being explicitly framed as
  a callback.
- Nothing asserted past what its source establishes without a `warning`.
