#!/usr/bin/env python3
"""
OffSec Quotidien - delivery stage (Resend).

Two subcommands, called at opposite ends of the generation run:

    python3 scripts/deliver.py arm
    python3 scripts/deliver.py send <out_dir> <issue-number>

`arm` queues a failure alert for the next 06:00 Europe/Paris BEFORE any
research begins. `send` queues the real issue for that same instant and then
tries to cancel the alert. If the run dies anywhere in between, the alert is
still scheduled and the operator learns about it at 06:00 rather than by
noticing an absence.

This is deliberately not a fallback delivery path - it is a health signal on
the single path, so there is no second system to keep in sync and no risk of
a duplicate send.

Environment:
    RESEND_API_KEY    required. "Sending access" is enough to queue mail.
    RESEND_MGMT_KEY   optional. Full-access key, used ONLY to cancel the alert.
                      Without it the alert cannot be cancelled and a spurious
                      "no issue" mail arrives alongside a perfectly good issue.
    NEWSLETTER_FROM   default "OffSec Quotidien <newsletter@rzdhop.com>"
    NEWSLETTER_TO     fallback only, used when subscribers.txt is absent or
                      empty (comma-separated for many). The distribution list
                      itself lives in subscribers.txt at the repository root.
    NEWSLETTER_ALERT_TO  optional. Where the dead-man alert goes. Defaults to
                      OPERATOR_FALLBACK below. Never the readership: readers
                      must not receive failure notices for a console they
                      cannot open.

Readers above one are blind-copied, so no subscriber ever sees another
subscriber's address. See envelope().
"""

import base64
import datetime
import json
import os
import sys
import urllib.error
import urllib.request
import zoneinfo

RESEND_ENDPOINT = "https://api.resend.com/emails"
PARIS = zoneinfo.ZoneInfo("Europe/Paris")

# Written by arm(), consumed by send(). Lives in the run workspace and is
# gitignored: it is a handle to a pending send, not project state.
ALERT_ID_FILE = ".resend-alert-id"

# Resolved from this file rather than from the working directory: the routine
# invokes the scripts from the workspace root, but a manual debug re-run from
# scripts/ must read the same distribution list.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBSCRIBERS_PATH = os.path.join(REPO_ROOT, "subscribers.txt")

# The dead-man alert is an operational signal, not an issue: it must reach the
# person who can re-run the routine and nobody else. Pinned here rather than
# read from subscribers.txt so that editing the reader list can never redirect
# the alerts. Override with NEWSLETTER_ALERT_TO.
OPERATOR_FALLBACK = "verdu.rida@gmail.com"

# Resend sits behind Cloudflare, which rejects the stock "Python-urllib/3.x"
# agent with HTTP 403 and Cloudflare error 1010 ("browser signature banned").
# On the 2026-08-05 run this failed `arm` outright, which disarmed the entire
# dead-man switch before any work started - the one failure mode the switch
# exists to prevent. Every request must therefore carry a plausible agent.
USER_AGENT = "OffSecQuotidien/1.0 (+https://github.com/rzdhop/Newsletter)"


class ResendError(RuntimeError):
    """
    An API or transport failure from Resend, carrying the HTTP status.

    A dedicated exception rather than a bare SystemExit inside the request
    helper: `arm` must abort the run on failure, while `send` must NOT abort
    when only the cancel call fails. The caller is the only place that knows
    which of the two applies, so the helper reports and the caller decides.
    """

    def __init__(self, status, detail):
        super().__init__(f"{status} {detail}")
        self.status = status
        self.detail = detail


def _env(name, default=None):
    value = os.environ.get(name, default)
    if value is None:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def _request(method, url, payload=None, api_key=None):
    """
    Minimal Resend client built on urllib.

    Deliberately no third-party HTTP library: the cloud environment rebuilds
    from a cached setup script, and depending on zero installed packages
    removes an entire class of "worked yesterday, broke today" failures from a
    job that must not miss a morning.

    `api_key` is an explicit parameter rather than being read from the
    environment inside this function because the pipeline uses two keys with
    different rights, and which one applies is a property of the call, not of
    the process.
    """
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Bearer {api_key or _env('RESEND_API_KEY')}")
    request.add_header("Content-Type", "application/json")
    request.add_header("User-Agent", USER_AGENT)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise ResendError(error.code, detail) from error
    except urllib.error.URLError as error:
        raise ResendError(None, f"unreachable: {error.reason}") from error


def next_six_am():
    """
    The next 06:00:00 Europe/Paris, as an offset-aware ISO 8601 string.

    zoneinfo resolves the offset for that specific calendar date, so the value
    is +02:00 under CEST and +01:00 under CET automatically. Computing this in
    UTC would silently deliver an hour late for half the year.
    """
    now = datetime.datetime.now(PARIS)
    target = now.replace(hour=6, minute=0, second=0, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    return target.isoformat()


def _dedupe(addresses):
    """
    Order-preserving, case-insensitive dedupe.

    A line pasted twice into subscribers.txt would otherwise become a second
    delivery to that reader, and Resend counts it twice against its documented
    50-address ceiling on `to`. Order is preserved so the payload stays
    diffable between runs instead of reshuffling with set iteration.
    """
    seen = set()
    unique = []
    for address in addresses:
        key = address.lower()
        if key not in seen:
            seen.add(key)
            unique.append(address)
    return unique


def recipients():
    """
    The distribution list, read from subscribers.txt at the repository root.

    A committed file rather than NEWSLETTER_TO because the routine environment
    is configured through a web UI and is therefore NOT version-controlled -
    the known cost of engine A1, already compensated for elsewhere by
    preflight.py. Adding a reader through the env var means editing a text box
    no `git diff` will ever show; a file makes the list reviewable, revertible
    and editable from anywhere git reaches.

    Plain text rather than YAML: check_sources.py already hand-parses
    sources.yaml specifically to keep this pipeline free of third-party
    packages, and a list of addresses has no structure worth a parser.

    NEWSLETTER_TO survives as the fallback so a workspace without the file, or
    a one-off test run, still has a defined destination - and so preflight's
    existing check on that variable keeps its meaning instead of becoming a
    lie about where mail actually goes.
    """
    if os.path.exists(SUBSCRIBERS_PATH):
        with open(SUBSCRIBERS_PATH, encoding="utf-8") as handle:
            # split("#", 1)[0] strips trailing comments, so a line can carry a
            # name: "alice@example.com  # Alice, joined 2026-08".
            addresses = [line.split("#", 1)[0].strip() for line in handle]
        addresses = [address for address in addresses if address]
        if addresses:
            return _dedupe(addresses)

    return _dedupe([address.strip() for address
                    in _env("NEWSLETTER_TO", "verdu.rida@gmail.com").split(",")
                    if address.strip()])


def sender():
    return _env("NEWSLETTER_FROM", "OffSec Quotidien <newsletter@rzdhop.com>")


def operator():
    """
    Where the dead-man alert goes: the operator, never the readership.

    arm() used to reuse recipients(), which was harmless with a list of one and
    becomes a defect at the second address - every reader would receive a
    French failure notice linking to a private routine console they cannot
    open, on exactly the mornings when the product already looks broken.

    Deliberately NOT recipients()[0]: deriving the operator from list order
    means a reordered or alphabetised subscribers.txt silently redirects the
    alerts to a reader. The address is pinned instead, and overridable through
    the environment for anyone who forks this pipeline.
    """
    return [address.strip() for address
            in os.environ.get("NEWSLETTER_ALERT_TO", OPERATOR_FALLBACK).split(",")
            if address.strip()]


def envelope(addresses):
    """
    Split the distribution list into a (to, bcc) pair.

    Every address in `to` is disclosed to every other recipient, and Resend
    documents a ceiling of 50 there. With one reader that is irrelevant; with a
    dozen it publishes the readership of a newsletter about offensive security
    to the readership itself. The issue is therefore addressed to the sending
    identity and everyone else is blind-copied.

    Bcc rather than one send per reader: a per-recipient loop would re-upload
    the ~157 KB base64 attachment once per person and multiply the number of
    calls that can fail between arming and cancelling the dead-man switch. One
    call, one upload, one id to reason about.

    A single recipient short-circuits to the previous behaviour exactly, so
    this changes nothing until the second address exists.
    """
    if len(addresses) <= 1:
        return addresses, []
    return [sender()], addresses


def arm():
    """
    Queue the dead-man alert. Called before any generation work starts.

    A failure here is fatal on purpose: continuing would mean running the whole
    pipeline with no health signal at all, which is exactly the silent-failure
    mode the switch was designed to remove.
    """
    scheduled = next_six_am()
    try:
        result = _request("POST", RESEND_ENDPOINT, {
            "from": sender(),
            "to": operator(),
            "subject": "[OffSec Quotidien] Aucun numero ce matin",
            "html": (
                "<p style=\"font-family:sans-serif\">La routine de g&eacute;n&eacute;ration a "
                "d&eacute;marr&eacute; mais ne s&rsquo;est pas termin&eacute;e.</p>"
                "<p style=\"font-family:sans-serif\">Journal du run&nbsp;: "
                "<a href=\"https://claude.ai/code/routines\">claude.ai/code/routines</a></p>"
            ),
            "scheduled_at": scheduled,
        })
    except ResendError as error:
        raise SystemExit(f"Cannot arm the dead-man alert, aborting run: {error}")

    with open(ALERT_ID_FILE, "w", encoding="utf-8") as handle:
        handle.write(result["id"])
    print(f"Dead-man alert armed for {scheduled}: {result['id']}")


def _cancel_alert():
    """
    Cancel the dead-man alert. Never fatal.

    POST /emails/:id/cancel requires a full-access key, while RESEND_API_KEY is
    intentionally restricted to sending. RESEND_MGMT_KEY carries the cancel
    right and nothing else in the pipeline uses it.

    Every failure path here is reported and swallowed. By the time this runs the
    issue is already queued for 06:00, so raising would turn a delivered issue
    into a run marked failed - and a run marked failed is the signal the
    operator uses to decide whether to intervene. A spurious "no issue" mail is
    an annoyance; a false failure report costs a morning of trust.

    The handle file is removed only on a confirmed cancel, so a failed attempt
    leaves the id on disk and a later manual retry still knows what to cancel.
    """
    if not os.path.exists(ALERT_ID_FILE):
        print("No dead-man alert on file; nothing to cancel.")
        return

    with open(ALERT_ID_FILE, encoding="utf-8") as handle:
        alert_id = handle.read().strip()

    mgmt_key = os.environ.get("RESEND_MGMT_KEY")
    if not mgmt_key:
        print(f"WARNING: RESEND_MGMT_KEY unset - alert {alert_id} cannot be "
              f"cancelled and WILL fire at 06:00 alongside the issue.")
        print(f"         Cancel it manually at https://resend.com/emails/{alert_id}")
        return

    try:
        _request("POST", f"{RESEND_ENDPOINT}/{alert_id}/cancel", api_key=mgmt_key)
    except ResendError as error:
        print(f"WARNING: could not cancel alert {alert_id}: {error}")
        print(f"         Cancel it manually at https://resend.com/emails/{alert_id}")
        return

    os.remove(ALERT_ID_FILE)
    print(f"Dead-man alert cancelled: {alert_id}")


def send(out_dir, issue):
    """Queue the real issue, then try to cancel the alert."""
    with open(os.path.join(out_dir, "digest.html"), encoding="utf-8") as handle:
        digest_html = handle.read()
    with open(os.path.join(out_dir, "full.html"), "rb") as handle:
        full_bytes = handle.read()

    today = datetime.datetime.now(PARIS).strftime("%Y-%m-%d")
    scheduled = next_six_am()

    to_addresses, bcc_addresses = envelope(recipients())

    payload = {
        "from": sender(),
        "to": to_addresses,
        "subject": f"OffSec Quotidien n°{issue} — {today}",
        "html": digest_html,
        "scheduled_at": scheduled,
        # Attachments do not count toward Gmail's ~102 KB clipping threshold,
        # so the complete issue always travels intact regardless of its size.
        "attachments": [{
            "filename": f"offsec-quotidien-{issue}.html",
            "content": base64.b64encode(full_bytes).decode("ascii"),
        }],
    }

    # Omitted rather than sent empty: a single-recipient run must still produce
    # the payload that shipped issue 413, so this change is a no-op until the
    # list actually grows.
    if bcc_addresses:
        payload["bcc"] = bcc_addresses

    try:
        result = _request("POST", RESEND_ENDPOINT, payload)
    except ResendError as error:
        raise SystemExit(f"Delivery failed, dead-man alert left armed: {error}")

    print(f"Issue {issue} queued for {scheduled}: {result['id']}")

    # Cancel only after a confirmed queue id. Reversing this order would mean a
    # failure between the two calls leaves neither the issue nor the alert.
    _cancel_alert()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    command = sys.argv[1]
    if command == "arm":
        arm()
    elif command == "send":
        if len(sys.argv) < 4:
            print("usage: deliver.py send <out_dir> <issue-number>")
            return 1
        send(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {command}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
