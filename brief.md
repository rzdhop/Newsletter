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
One advanced subject: malware technique, hardware hacking, or web exploitation.
**Advanced only.** No introductions to XSS, no "what is a buffer overflow".
Ends with concrete proposed improvements to the technique.

### Partie 03 — Deep-dive
A second subject, same treatment, **a different domain from Partie 02**. Two
Windows-maldev deep-dives in one issue is a weaker edition than one maldev plus
one hardware or web subject.

### Partie 04 — Autopsie d'attaque
A recent attack, judged technically, as an expert would. Every aspect explained
to the depth where a reader could **approach reproduction** in a lab. Timestamped
phases. Say plainly when the public reporting is thin — reconstructing a chain
from a vendor blog post is inference, and inference must be labelled.

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

**3. Never repeat a subject.**
`state/topics-index.json` records everything ever covered. A subject already
there may only be **mentioned** — and a mention is a written summary of what
was said and why it matters again, never a bare link back.

**4. Erebos-aware topic selection.**
Read `refs/erebos-inventory.md`. Techniques the operator has already
implemented are not deep-dive subjects; they are prior work, referenced in one
sentence. Deep-dives go to the gaps. BOF loader is the flagged priority.

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
- At least one thing the reader could go and *do* today.
- No paragraph that could be deleted without losing information.
- Parties 02 and 03 in different domains.
- Partie 04 tied to at least one Tier 5 factual anchor (KEV, ZDI, LOLDrivers).
- Nothing repeated from `topics-index.json` without being explicitly framed as
  a callback.
