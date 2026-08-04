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

This does not fail the build. A source being down today is information, not an
error - the run should continue with the sources that answered.

Usage:
    python3 scripts/check_sources.py [--timeout 15] [--quiet]
"""

import argparse
import json
import os
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
                if key in ("url", "feed", "extra", "confidence"):
                    current[key] = value.strip()

    if current and current.get("url"):
        entries.append(current)
    return entries


def probe(url, timeout):
    """
    Return (ok, status, note).

    A HEAD would be cheaper, but a meaningful number of these hosts answer 405
    or 403 to HEAD while serving GET perfectly, so HEAD would misreport healthy
    sources as dead. GET is the honest test.
    """
    request = urllib.request.Request(url, headers=HEADERS, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return True, response.status, ""
    except urllib.error.HTTPError as error:
        # 403/429 mean the host is alive and refusing automation, which is a
        # very different situation from a domain that no longer resolves.
        alive = error.code in (401, 403, 405, 429)
        return alive, error.code, "reachable but refuses automated requests" if alive else "HTTP error"
    except urllib.error.URLError as error:
        return False, None, f"unreachable: {error.reason}"
    except Exception as error:  # noqa: BLE001 - a health check must never crash the run
        return False, None, f"{type(error).__name__}: {error}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    entries = load_sources()
    results = []
    healthy = 0

    for entry in entries:
        target = entry.get("feed") or entry["url"]
        ok, status, note = probe(target, args.timeout)
        healthy += ok
        results.append({
            "name": entry["name"],
            "tier": entry.get("tier"),
            "url": target,
            "ok": ok,
            "status": status,
            "note": note,
        })
        if not args.quiet:
            mark = "ok  " if ok else "DEAD"
            print(f"[{mark}] {status if status else '---':>4}  {entry['name']:<28} {target}")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump({
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "total": len(results),
            "healthy": healthy,
            "dead": [r for r in results if not r["ok"]],
            "results": results,
        }, handle, ensure_ascii=False, indent=1)

    print(f"\n{healthy}/{len(results)} sources reachable -> {OUTPUT_PATH}")
    # Always exit 0: source health is information for the editor, not a build
    # failure. The run continues with whatever answered.
    return 0


if __name__ == "__main__":
    sys.exit(main())
