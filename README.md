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
              ├─ clone this repo: brief, prompt, sources, state, refs
              ├─ preflight the environment, then arm the dead-man alert
              │                                          ← before anything else
              ├─ research → write 4 parts in French
              ├─ emit content.json → render → split
              ├─ update state/topics-index.json          ← before the commit
              ├─ git commit issues/ + state/ + permalinks
              ├─ git push origin main, then verify      ← Pages serves main only
              ├─ queue with Resend, scheduled_at 06:00:00+02:00
              ├─ cancel the dead-man alert
              └─ write the SHA-256 archive manifest to Google Drive

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
| `scripts/preflight.py` | environment validation, runs before anything is armed |
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
| An environment that is not version-controlled | `preflight.py` aborts loudly before any work is spent |
| Cloudflare rejecting the stock urllib agent | explicit `User-Agent` on every Resend call |
| A cancel right the sending key does not have | `RESEND_MGMT_KEY`, used for nothing else; failure to cancel is non-fatal |
| Pages serving only the default branch | the project works on `main` only — `preflight.py` fails on any other branch, before work is spent |
| Repeating a subject | `state/topics-index.json`, updated before the commit, checked before writing |
| Covering ground already built | `refs/erebos-inventory.md`, reconciled with the live repo each run |
| A source going dark | `check_sources.py` makes decay measurable instead of invisible |
| No path-based upload on the Drive connector | Drive carries a SHA-256 manifest; the repo, Pages and the attachment carry the bytes |

---

## Design

Reproduces the component system of reference issue 412 exactly: 680 px, inline
styles only, `<table role="presentation">` throughout, no flexbox, no grid, no
external CSS, no JavaScript. See `refs/design-tokens.md`.
