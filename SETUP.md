# Setup — one pass, then it runs itself

Everything below is done once. After step 7 the newsletter is autonomous and
your machine is never involved again.

---

## 1. Push this repository

```bash
cd "G:\My Drive\Newsletter\repo"
git init
git remote add origin https://github.com/rzdhop/Newsletter.git
git add .
git commit -m "pipeline: renderer, splitter, delivery, source registry"
git branch -M main
git push -u origin main
```

The repo is already public, which is what makes GitHub Pages free.

## 2. Enable GitHub Pages

Repo → **Settings → Pages** → Source: *Deploy from a branch* → Branch: `main`,
folder `/ (root)` → Save.

The archive will be at `https://rzdhop.github.io/Newsletter/`, and each issue
gets a clean permalink like `https://rzdhop.github.io/Newsletter/413`.

## 3. Resend

You already have `rzdhop.com` verified, so there is nothing to configure —
just confirm the sender works:

```bash
curl -X POST https://api.resend.com/emails \
  -H "Authorization: Bearer $RESEND_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"from":"OffSec Quotidien <newsletter@rzdhop.com>",
       "to":["verdu.rida@gmail.com"],
       "subject":"test",
       "html":"<p>ok</p>"}'
```

If that lands in your inbox, delivery is solved. Grab an API key from
**resend.com → API Keys** with *Sending access* only — the pipeline never needs
to read anything.

## 4. Give Claude Code access to GitHub

In a Claude Code session:

```
/web-setup
```

This grants repository cloning for cloud sessions. It is **not** the same as
installing the Claude GitHub App — you only need the App if you later add a
GitHub event trigger, which this design does not use.

## 5. Connect Google Drive for the routine

Go to **[claude.ai/customize/connectors](https://claude.ai/customize/connectors)**
and connect Google Drive on the `verdu.rida@gmail.com` account.

This is a different place from the connector in the desktop app. Routines can
only see connectors attached to your claude.ai account.

## 6. Create the routine

**[claude.ai/code/routines](https://claude.ai/code/routines) → New routine → Cloud**

| Field | Value |
|---|---|
| Name | `offsec-quotidien` |
| Repository | `rzdhop/Newsletter` |
| Trigger | Schedule → Daily → **02:00** (your local time) |
| Environment | new environment, **Network access: Full** |
| Connectors | Google Drive only — remove every other one |
| Model | **Opus** — required, see below |

Environment variables:

```
RESEND_API_KEY             = re_xxxxxxxxxxxx
NEWSLETTER_FROM            = OffSec Quotidien <newsletter@rzdhop.com>
NEWSLETTER_TO              = verdu.rida@gmail.com
CLAUDE_CODE_SUBAGENT_MODEL = opus
```

**The Resend key must not be a "sending access" restricted key.** Such a key can
`POST /emails`, so both `deliver.py arm` and the issue itself go out normally —
and then `deliver.py send` cannot cancel the alert it armed, so the "aucun
numero ce matin" mail lands next to every successful issue. Give the key full
access, or at minimum send plus cancel.

**`CLAUDE_CODE_SUBAGENT_MODEL` must be exactly `opus`.** `opus5` is not a valid
alias: it is rejected at spawn time and every subagent dies immediately with
"There's an issue with the selected model". The run can still complete — the
main loop does the sweep inline — but it loses all parallelism.

**Why Opus.** Issue quality tracks model capability closely here. The research
sweep reads a week of dense primary sources and has to tell a paper from a
press release; the deep-dives are long-context technical writing against a
citation standard. Smaller models produce thinner issues, miss the primary
source behind a news item, and pad when the week is quiet.

`CLAUDE_CODE_SUBAGENT_MODEL` applies the same default to delegated work.
Subagent model resolution order is: environment variable → per-invocation
parameter → frontmatter → main conversation model, so setting the variable
means a research sweep spawned mid-run inherits Opus rather than defaulting
to something cheaper.

To pin a *specific* Opus variant rather than whatever `opus` currently
resolves to, use the full model ID (for example `claude-opus-5`) in both the
model selector and this variable.

Prompt — paste exactly this and nothing more:

```
Generate today's issue of OffSec Quotidien.

Read prompt.md at the repository root and follow it step by step, without
deviation. It is the complete procedure. Read brief.md as well: it is the
editorial standard and it overrides convenience at every step.

Two rules that matter more than finishing:
- Run `python3 scripts/deliver.py arm` FIRST, before any research.
- Never pad. A part with no solid material gets an "empty" block. An 8,000-word
  issue where every paragraph earns its place beats a 10,000-word padded one.

If you cannot complete the issue, stop and leave the dead-man alert armed. Do
not send a half-issue.
```

**Why Full network access.** Deep research means fetching arbitrary security
blogs plus `api.resend.com`; the default *Trusted* allowlist blocks both. The
session runs autonomously with no approval prompts, so the blast radius is:
this repo, your Drive, and your Resend sending key. That is the trade you are
accepting — it is a deliberate choice, not an oversight.

**Why 02:00.** The engine does not need to be punctual, only to finish before
06:00. Resend holds the mail and delivers it to the second, so a slow or
restarted run is invisible. Four hours of slack.

## 7. Test before trusting it

1. **Run now** on the routine page. Do not wait for 02:00.
2. Open the run session and read the transcript. A green status only means the
   container exited cleanly — it does **not** mean the issue is good.
3. Check `issues/2026/…/413/` was committed and the Pages permalink resolves.
4. Read the issue that arrives at 06:00. Judge it against `brief.md`.
5. Repeat for two or three days with manual runs, correcting `prompt.md`
   between attempts.
6. Only then leave the schedule enabled.

## 8. Train Gmail once

`newsletter@rzdhop.com` is SPF/DKIM-aligned so it should land in the inbox, but
create a filter anyway: **from `newsletter@rzdhop.com` → Never send to Spam,
Always mark as important, Categorise as Primary**. Costs thirty seconds and
removes the one remaining way a morning goes missing.

---

## Running it by hand

```bash
python3 scripts/check_sources.py                       # registry health
python3 scripts/split.py content.json issues/2026/08/413/
python3 scripts/build_index.py                          # permalinks + archive index
python3 scripts/deliver.py send issues/2026/08/413/ 413
```

## If a morning goes missing

You will get the dead-man alert at 06:00 instead of silence. Then:

1. Open [claude.ai/code/routines](https://claude.ai/code/routines) → the failed run → read the transcript.
2. Common causes: a Tier 1 source hanging the research step, Resend key expired,
   subscription usage exhausted.
3. `python3 scripts/check_sources.py` tells you if the registry decayed.
4. Fix, then **Run now** — the issue still ships, just later than 06:00.
