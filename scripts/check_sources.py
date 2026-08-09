#!/usr/bin/env python3
"""
OffSec Quotidien - source registry health check.

Walks sources.yaml, requests every URL, and writes the outcome to
state/source-health.json. Run it weekly (or at the start of any run where the
newsletter came out thin).

Why this exists: a dead source does not announce itself. It just quietly stops
contributing, the sweep gets narrower every month, and the first visible
symptom is a newsletter that has less to say. Making decay measurable is the
cheapest possible fix.

Reachability is not contribution. Checking only the status code is what let the
registry rot undetected until the 2026-08-09 revalidation: SpecterOps, NCC Group
and Phrack were all answering HTTP 200 while returning zero usable entries,
because the feed had moved, been withdrawn, or been replaced by an HTML page at
the same URL. Every one of them was reported healthy here, every week, while
contributing nothing to the sweep - and a feed that yields nothing is
indistinguishable from a quiet week unless something counts the entries. So when
the registry declares a `feed:`, this script parses it and counts.

Three states are therefore worth telling apart, and the whole point of the
script is that they look identical from the status code alone:

    ok      the feed parsed and carries entries
    EMPTY   HTTP 200, zero entries - the feed is broken, not the lab quiet
    quiet   entries present but all old - the lab really has published nothing

`quiet` is advisory and never counted as a defect: Paged Out!, Phrack and
tmp.0ut are irregular by nature, so any source carrying a `cadence:` of rare or
irregular is exempt from the staleness window entirely.

The newest date is the maximum over every entry, not the date on the first one.
Feeds are not reliably ordered - fluxsec's leads with an April 2025 post while
carrying six from 2026 - and reading entry[0] would have declared an active blog
dormant.

This does not fail the build. A source being down today is information, not an
error - the run should continue with the sources that answered.

Usage:
    python3 scripts/check_sources.py [--timeout 15] [--quiet] [--stale-days 90]
"""

import argparse
import email.utils
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_PATH = os.path.join(REPO_ROOT, "sources.yaml")
OUTPUT_PATH = os.path.join(REPO_ROOT, "state", "source-health.json")

# Several research blogs reject requests without a plausible User-Agent, which
# would otherwise show up here as a false "dead source" and slowly strip the
# registry of exactly the Tier 1/2 entries that matter most.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; OffSecQuotidien/1.0; +https://github.com/rzdhop/Newsletter)",
    "Accept": "text/html,application/xhtml+xml,application/xml,application/rss+xml;q=0.9,*/*;q=0.8",
}

# Atom calls them <entry>, RSS calls them <item>. Nothing else in either format
# uses those tag names, so a regex is enough and keeps the zero-dependency rule.
ENTRY_RE = re.compile(r"<(entry|item)\b.*?</\1>", re.S)

# Publication dates, in every spelling the registry's feeds actually use.
#
# The backreferenced close tag is load-bearing twice over. It skips self-closing
# elements - Synacktiv's feed emits a bare `<pubDate/>` on every item, and a
# looser pattern captures the *following* element's text as if it were a date.
# And `[^<]*` stops the capture at the next tag, so a date can never absorb the
# markup after it. Both mistakes fail the same way: a confident wrong answer.
DATE_RE = re.compile(r"<(published|updated|pubDate|dc:date)\b[^>]*>([^<]*)</\1>", re.S)

# A source whose cadence is declared irregular is never "stale": it is simply
# how that publication works, and flagging it weekly would train the reader to
# ignore the report - which costs more than the check is worth.
IRREGULAR = {"rare", "irregular"}

# Read only when the whole body is needed; feeds are small, but a misconfigured
# URL pointing at something enormous should not stall the weekly check.
MAX_BODY_BYTES = 8 * 1024 * 1024


def load_sources():
    """
    Parse sources.yaml without PyYAML.

    The cloud environment is rebuilt from a cached setup script; depending on
    zero third-party packages removes a whole class of "worked yesterday"
    failures. The file only ever uses the small subset of YAML handled here:
    two-space nesting, list items introduced by '- name:', and 'key: value'.
    """
    entries = []
    tier = None
    current = None

    with open(SOURCES_PATH, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            indent = len(line) - len(line.lstrip(" "))

            if indent == 2 and stripped.endswith(":") and stripped.startswith("tier_"):
                tier = stripped[:-1]
                continue

            if stripped.startswith("- name:"):
                if current and current.get("url"):
                    entries.append(current)
                current = {"tier": tier, "name": stripped.split(":", 1)[1].strip()}
                continue

            if current is not None and ": " in stripped and not stripped.startswith("- "):
                key, value = stripped.split(": ", 1)
                key = key.strip().lstrip("- ")
                if key in ("url", "feed", "extra", "confidence", "cadence"):
                    current[key] = value.strip()

    if current and current.get("url"):
        entries.append(current)
    return entries


def probe(url, timeout):
    """
    Return (ok, status, note, body).

    A HEAD would be cheaper, but a meaningful number of these hosts answer 405
    or 403 to HEAD while serving GET perfectly, so HEAD would misreport healthy
    sources as dead. GET is the honest test - and it is now also the only test
    that can count entries, so the body comes back with the verdict.
    """
    request = urllib.request.Request(url, headers=HEADERS, method="GET")
    # One retry, and only on a transport failure. An HTTPError is a decision the
    # server made and repeating it just doubles the load; a reset connection or a
    # timeout is noise, and reporting a live source DEAD over one dropped socket
    # is the false positive most likely to get a good source deleted from the
    # registry by someone tidying up.
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read(MAX_BODY_BYTES).decode("utf-8", errors="replace")
                return True, response.status, "", body
        except urllib.error.HTTPError as error:
            # 403/429 mean the host is alive and refusing automation, which is a
            # very different situation from a domain that no longer resolves.
            alive = error.code in (401, 403, 405, 429)
            return (alive, error.code,
                    "reachable but refuses automated requests" if alive else "HTTP error", "")
        except urllib.error.URLError as error:
            if attempt == 2:
                return False, None, f"unreachable: {error.reason}", ""
        except Exception as error:  # noqa: BLE001 - a health check must never crash the run
            if attempt == 2:
                return False, None, f"{type(error).__name__}: {error}", ""
    return False, None, "unreachable", ""


def parse_date(raw):
    """
    Parse one feed date, or return None.

    Both spellings are tried because the registry mixes Atom and RSS, and both
    are wrapped: real feeds carry malformed dates. fluxsec's has an entry whose
    hour field is out of range, which raises straight out of the stdlib parser -
    and one bad entry must not cost the whole feed its verdict.
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(raw)
        if parsed is not None:
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:  # noqa: BLE001 - a malformed date is data, not a crash
        pass
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:  # noqa: BLE001
        return None


def inspect_feed(body):
    """
    Return (entry_count, newest_datetime_or_None).

    The newest date is the maximum across every date in the document rather than
    the first one encountered, because feed ordering cannot be relied on. This
    is the difference between "dormant since April 2025" and "six posts this
    year" for a feed the registry already depends on.
    """
    count = len(ENTRY_RE.findall(body))
    if not count:
        return 0, None
    dates = [d for d in (parse_date(raw) for _, raw in DATE_RE.findall(body)) if d]
    return count, (max(dates) if dates else None)


def _n(count):
    """'1 entry' / '3 entries' - this text is read weekly, so it should read."""
    return f"{count} entry" if count == 1 else f"{count} entries"


def classify(entry, ok, status, body, stale_days, now):
    """
    Turn a raw probe into a state, a human note, and the numbers behind it.

    Entry counting applies only where the registry declares a `feed:`. When the
    probe fell back to the source's `url`, an HTML landing page with no <item>
    elements is the expected and correct answer, so counting there would invent
    failures for every feedless source - which, after the 2026-08-09 pass, is a
    deliberate and documented category rather than an oversight.
    """
    if not ok:
        return "DEAD", "unreachable" if status is None else "HTTP error", None, None
    if status in (401, 403, 405, 429):
        return "guard", "reachable but refuses automated requests", None, None
    if not entry.get("feed"):
        return "ok", "page reachable (no feed declared)", None, None

    count, newest = inspect_feed(body)
    if count == 0:
        return ("EMPTY",
                "declared a feed but returned 0 entries - moved, withdrawn, "
                "or now serving HTML at the same URL",
                0, None)

    # Clamped at zero: aggregators routinely carry entries stamped slightly in
    # the future (r/netsec did at the last run), and a negative age reads as a
    # bug in this script rather than as the freshest possible feed.
    age = None if newest is None else max(0, (now - newest).days)
    if entry.get("cadence", "").lower() in IRREGULAR:
        return "ok", f"{_n(count)} (irregular cadence, staleness not checked)", count, age
    if age is not None and age > stale_days:
        return "quiet", f"{_n(count)}, newest {age}d ago (nothing new in {stale_days}d)", count, age
    if age is None:
        return "ok", f"{_n(count)} (no parsable dates)", count, None
    return "ok", f"{_n(count)}, newest {age}d ago", count, age


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--stale-days", type=int, default=90,
                        help="flag a feed as quiet when its newest entry is older than this")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    entries = load_sources()
    results = []

    for entry in entries:
        target = entry.get("feed") or entry["url"]
        ok, status, note, body = probe(target, args.timeout)
        state, detail, count, age = classify(entry, ok, status, body, args.stale_days, now)
        results.append({
            "name": entry["name"],
            "tier": entry.get("tier"),
            "url": target,
            "kind": "feed" if entry.get("feed") else "page",
            "ok": ok,
            "state": state,
            "status": status,
            "entries": count,
            "newest_age_days": age,
            "note": detail or note,
        })
        if not args.quiet:
            print(f"[{state:<5}] {status if status else '---':>4}  "
                  f"{entry['name']:<28} {detail}")

    reachable = [r for r in results if r["ok"]]
    feeds = [r for r in results if r["kind"] == "feed"]
    empty = [r for r in results if r["state"] == "EMPTY"]
    quiet = [r for r in results if r["state"] == "quiet"]
    dead = [r for r in results if r["state"] == "DEAD"]
    contributing = [r for r in feeds if r["state"] in ("ok", "quiet")]

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump({
            "checked_at": now.isoformat(),
            "stale_days": args.stale_days,
            "total": len(results),
            "reachable": len(reachable),
            "feeds": len(feeds),
            "feeds_contributing": len(contributing),
            "dead": dead,
            # Kept as its own key rather than folded into `dead`: an empty feed
            # needs a URL fixed, a dead one may just need waiting out, and the
            # two want different work from whoever reads this file.
            "empty": empty,
            "quiet": quiet,
            "results": results,
        }, handle, ensure_ascii=False, indent=1)

    print(f"\n{len(reachable)}/{len(results)} reachable  |  "
          f"{len(contributing)}/{len(feeds)} feeds returning entries -> {OUTPUT_PATH}")
    for row in empty:
        print(f"  EMPTY  {row['name']}: {row['url']}")
    for row in dead:
        print(f"  DEAD   {row['name']}: {row['url']}")
    if quiet:
        print(f"  quiet  {', '.join(r['name'] for r in quiet)} "
              f"(no entry newer than {args.stale_days}d - verify before assuming decay)")
    # Always exit 0: source health is information for the editor, not a build
    # failure. The run continues with whatever answered.
    return 0


if __name__ == "__main__":
    sys.exit(main())
