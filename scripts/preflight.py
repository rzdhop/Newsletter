#!/usr/bin/env python3
"""
OffSec Quotidien - pre-flight environment check.

Runs as the very first command of Step 0, before `deliver.py arm`. Each check
below corresponds to a failure that actually happened in production and cost
either a morning or a silently degraded issue.

The routine's environment is configured through a web UI and is therefore NOT
version-controlled - the known cost of engine A1. This script is the
compensating control: it turns a silent environment drift into a loud, early,
pre-work abort.

Exit codes:
    0  all blocking checks passed (warnings may still have been printed)
    1  a blocking check failed - the run must not continue

Usage:
    python3 scripts/preflight.py
"""

import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

RESEND_ENDPOINT = "https://api.resend.com/emails"
USER_AGENT = "OffSecQuotidien/1.0 (+https://github.com/rzdhop/Newsletter)"

# Accepts a bare family alias ("opus") or a fully qualified model id
# ("claude-opus-5"). Rejects near-misses such as "opus5", which is what the
# routine environment actually held on 2026-08-05: it is not a valid alias, so
# every spawned subagent died at spawn time and the research sweep silently
# lost all parallelism. A regex rather than a hardcoded list, so that a new
# model release does not turn this guard into a false positive.
SUBAGENT_MODEL_RE = re.compile(r"^(opus|sonnet|haiku|claude-[a-z]+-[0-9][a-z0-9-]*)$")

failures = []
warnings = []


def blocking(label, ok, detail=""):
    """Record a check whose failure must abort the run before any work starts."""
    print(f"[{'PASS' if ok else 'FAIL'}] {label}{(' - ' + detail) if detail else ''}")
    if not ok:
        failures.append(label)


def advisory(label, ok, detail=""):
    """Record a check whose failure degrades the run but does not invalidate it."""
    print(f"[{'PASS' if ok else 'WARN'}] {label}{(' - ' + detail) if detail else ''}")
    if not ok:
        warnings.append(label)


def check_required_env():
    for name in ("RESEND_API_KEY", "NEWSLETTER_FROM", "NEWSLETTER_TO"):
        present = bool(os.environ.get(name))
        blocking(f"env {name}", present, "" if present else "unset")


def check_subagent_model():
    value = os.environ.get("CLAUDE_CODE_SUBAGENT_MODEL")
    if value is None:
        advisory("env CLAUDE_CODE_SUBAGENT_MODEL", False,
                 "unset - subagents inherit the main model instead of being pinned")
        return
    blocking("env CLAUDE_CODE_SUBAGENT_MODEL", bool(SUBAGENT_MODEL_RE.match(value)),
             f"'{value}' is not a valid alias or model id")


def check_resend_reachable():
    """
    Prove that Resend answers *us*, specifically.

    An unauthenticated-shaped request is enough: a 401, 403, 404 or 405 carrying
    a JSON body means the API is alive and simply refusing these credentials for
    this verb, which is a healthy answer. What this really tests is the layer in
    front of the API - Cloudflare returns an HTML 403 containing "1010" to the
    stock urllib agent, which is indistinguishable from an auth failure if you
    only look at the status code. That distinction is the entire point: on
    2026-08-05 it silently disarmed the dead-man switch.
    """
    request = urllib.request.Request(RESEND_ENDPOINT, method="GET")
    request.add_header("Authorization", f"Bearer {os.environ.get('RESEND_API_KEY', '')}")
    request.add_header("User-Agent", USER_AGENT)
    try:
        urllib.request.urlopen(request, timeout=15)
        blocking("resend.com reachable", True)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        blocked = "1010" in body or "Cloudflare" in body
        blocking("resend.com reachable", not blocked,
                 "Cloudflare is rejecting our User-Agent" if blocked
                 else f"API answered {error.code}, transport healthy")
    except urllib.error.URLError as error:
        blocking("resend.com reachable", False, f"unreachable: {error.reason}")


def check_cancel_rights():
    advisory("env RESEND_MGMT_KEY", bool(os.environ.get("RESEND_MGMT_KEY")),
             "unset - the dead-man alert cannot be cancelled and will fire "
             "at 06:00 even on a fully successful run")


def check_git_target():
    """
    Report the branch this run started on.

    A cloud routine begins on an auto-created feature branch. GitHub Pages only
    serves the default branch, so an issue committed and left there produces a
    permalink that 404s in a mail that has already been sent - which is exactly
    what happened to issue 413. Advisory rather than blocking: the branch is
    legitimate, what matters is that Step 8 pushes to main explicitly, and this
    line exists to remind the run to do it.
    """
    try:
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception as error:  # noqa: BLE001 - a preflight must never crash the run
        advisory("git branch", False, f"{type(error).__name__}: {error}")
        return
    advisory("git branch", branch == "main",
             f"on '{branch}' - Step 8 MUST use 'git push origin HEAD:main'")


def main():
    print("OffSec Quotidien - preflight\n")
    check_required_env()
    check_subagent_model()
    check_resend_reachable()
    check_cancel_rights()
    check_git_target()

    print()
    if failures:
        print(f"{len(failures)} blocking check(s) failed: {', '.join(failures)}")
        print("Aborting before arming. Nothing was queued and nothing was written.")
        return 1
    if warnings:
        print(f"{len(warnings)} advisory warning(s): {', '.join(warnings)}")
    print("Preflight OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
