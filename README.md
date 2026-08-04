# OffSec Quotidien

A daily French offensive-security newsletter — four parts, ~10 000 words, fully
sourced — generated autonomously and delivered at 06:00 Europe/Paris.

No server. No always-on machine. A Claude Code Routine writes it on Anthropic's
cloud around 02:00, Resend holds it and delivers it on the second, GitHub Pages
archives it.

**Archive:** <https://rzdhop.github.io/Newsletter/> · **Setup:** [SETUP.md](SETUP.md)

---

## How it works

```
02:00 Paris   Claude Code Routine (Anthropic cloud)
              ├─ clone this repo: brief, prompt, template, sources, state
              ├─ arm the dead-man alert for 06:00        ← before anything else
              ├─ research → write 4 parts in French
              ├─ emit content.json → render → split
              ├─ git commit issues/ + state/
              ├─ mirror to Google Drive
              ├─ queue with Resend, scheduled_at 06:00:00+02:00
              └─ cancel the dead-man alert

06:00:00      Resend delivers. Your laptop was never involved.
```

Two design decisions carry most of the weight:

**Generation time and delivery time are separate problems.** The engine only has
to *finish* before 06:00; Resend's `scheduled_at` owns the clock. That is why a
research run that takes 20 minutes or 90 minutes makes no difference, and why
scheduler drift is irrelevant.

**The model writes content, never HTML.** It emits `content.json`; `render.py`
deterministically produces the markup. Design drift is therefore impossible and
the byte budget is predictable.

---

## Layout

| Path | Role |
|---|---|
| `brief.md` | editorial contract — what a good issue is |
| `prompt.md` | the runbook the routine follows, step by step |
| `sources.yaml` | tiered source registry, with exclusions and reasons |
| `refs/erebos-inventory.md` | Erebos-Zero techniques — drives topic selection |
| `refs/design-tokens.md` | colours, type scale, component reference |
| `state/topics-index.json` | anti-repetition ledger |
| `state/source-health.json` | written by `check_sources.py` |
| `scripts/render.py` | `content.json` → email HTML (13 components) |
| `scripts/split.py` | digest / full split against the 90 KB budget |
| `scripts/deliver.py` | Resend send + dead-man switch |
| `scripts/check_sources.py` | registry health check |
| `scripts/build_index.py` | Pages permalinks + archive index |
| `issues/YYYY/MM/NNN/` | rendered issues |

---

## Constraints this design works around

| Constraint | Handling |
|---|---|
| Gmail clips HTML over ~102 KB | digest ≤ 90 KB inline, full issue attached (attachments are exempt) |
| Raw UTF-8 inflates 20–30% under quoted-printable | renderer emits pure ASCII entities → measured +3.7% |
| Scheduler drift | Resend `scheduled_at` owns the clock, not the scheduler |
| A silent run failure | dead-man alert armed before work, cancelled after success |
| Repeating a subject | `state/topics-index.json`, checked before writing |
| Covering ground already built | `refs/erebos-inventory.md`, reconciled with the live repo each run |
| A source going dark | `check_sources.py` makes decay measurable instead of invisible |

---

## Design

Reproduces the component system of reference issue 412 exactly: 680 px, inline
styles only, `<table role="presentation">` throughout, no flexbox, no grid, no
external CSS, no JavaScript. See `refs/design-tokens.md`.
