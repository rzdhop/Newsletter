#!/usr/bin/env python3
"""
OffSec Quotidien - delivery stage (Resend).

Two subcommands, called at opposite ends of the generation run:

    python3 scripts/deliver.py arm
    python3 scripts/deliver.py send out/ <issue-number>

`arm` queues a failure alert for the next 06:00 Europe/Paris BEFORE any
research begins. `send` queues the real issue for that same instant and then
cancels the alert. If the run dies anywhere in between, the alert is still
scheduled and you find out at 06:00 rather than by noticing an absence.

This is deliberately not a fallback delivery path - it is a health signal on
the single path, so there is no second system to keep in sync and no risk of
a duplicate send.

Environment:
    RESEND_API_KEY    required; needs BOTH send and cancel rights. A restricted
                      "sending access" key can POST /emails - so `arm` and the
                      issue itself go out fine - but cannot cancel a scheduled
                      send, which leaves the dead-man alert firing next to every
                      successful issue.
    NEWSLETTER_FROM   default "OffSec Quotidien <newsletter@rzdhop.com>"
    NEWSLETTER_TO     default "verdu.rida@gmail.com" (comma-separated for many)
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
USER_AGENT = "OffSecQuotidien-pipeline/1.0"

# Written by arm(), consumed by send(). Lives in the run workspace and is
# gitignored: it is a handle to a pending send, not project state.
ALERT_ID_FILE = ".resend-alert-id"


def _env(name, default=None):
    value = os.environ.get(name, default)
    if value is None:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def _request(method, url, payload=None, fatal=True):
    """
    Minimal Resend client built on urllib.

    Deliberately no third-party HTTP library: the cloud environment rebuilds
    from a cached setup script, and depending on zero installed packages
    removes an entire class of "worked yesterday, broke today" failures from a
    job that must not miss a morning.
    """
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Bearer {_env('RESEND_API_KEY')}")
    request.add_header("Content-Type", "application/json")
    # Resend sits behind Cloudflare, which rejects the stock "Python-urllib/3.x"
    # agent with a 403 (error code 1010) before the request ever reaches the API.
    # Any explicit User-Agent clears it; name the pipeline so the calls are
    # identifiable in Resend's logs.
    request.add_header("User-Agent", USER_AGENT)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        message = f"Resend {method} {url} failed: {error.code} {detail}"
        if fatal:
            raise SystemExit(message)
        print(message)
        return None


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


def recipients():
    return [address.strip() for address in
            _env("NEWSLETTER_TO", "verdu.rida@gmail.com").split(",") if address.strip()]


def sender():
    return _env("NEWSLETTER_FROM", "OffSec Quotidien <newsletter@rzdhop.com>")


def arm():
    """Queue the dead-man alert. Called before any generation work starts."""
    result = _request("POST", RESEND_ENDPOINT, {
        "from": sender(),
        "to": recipients(),
        "subject": "[OffSec Quotidien] Aucun numero ce matin",
        "html": (
            "<p style=\"font-family:sans-serif\">La routine de g&eacute;n&eacute;ration a "
            "d&eacute;marr&eacute; mais ne s&rsquo;est pas termin&eacute;e.</p>"
            "<p style=\"font-family:sans-serif\">Journal du run&nbsp;: "
            "<a href=\"https://claude.ai/code/routines\">claude.ai/code/routines</a></p>"
        ),
        "scheduled_at": next_six_am(),
    })
    with open(ALERT_ID_FILE, "w", encoding="utf-8") as handle:
        handle.write(result["id"])
    print(f"Dead-man alert armed for {next_six_am()}: {result['id']}")


def send(out_dir, issue):
    """Queue the real issue, then cancel the alert."""
    with open(os.path.join(out_dir, "digest.html"), encoding="utf-8") as handle:
        digest_html = handle.read()
    with open(os.path.join(out_dir, "full.html"), "rb") as handle:
        full_bytes = handle.read()

    today = datetime.datetime.now(PARIS).strftime("%Y-%m-%d")

    payload = {
        "from": sender(),
        "to": recipients(),
        "subject": f"OffSec Quotidien n°{issue} — {today}",
        "html": digest_html,
        "scheduled_at": next_six_am(),
        # Attachments do not count toward Gmail's ~102 KB clipping threshold,
        # so the complete issue always travels intact regardless of its size.
        "attachments": [{
            "filename": f"offsec-quotidien-{issue}.html",
            "content": base64.b64encode(full_bytes).decode("ascii"),
        }],
    }

    result = _request("POST", RESEND_ENDPOINT, payload)
    print(f"Issue {issue} queued for {next_six_am()}: {result['id']}")

    # Cancel only after a confirmed queue id. Reversing this order would mean a
    # failure between the two calls leaves you with neither issue nor alert.
    #
    # The cancel is deliberately non-fatal. The issue is already queued at this
    # point, which is the part that matters; a failure here costs the operator a
    # spurious alert, not a missing edition, and exiting non-zero would misreport
    # a successful send as a failed one. It must still be loud: an alert that
    # cannot be cancelled fires at 06:00 next to the real issue.
    if not os.path.exists(ALERT_ID_FILE):
        print("No dead-man alert on file; nothing to cancel.")
        return

    with open(ALERT_ID_FILE, encoding="utf-8") as handle:
        alert_id = handle.read().strip()

    if _request("POST", f"{RESEND_ENDPOINT}/{alert_id}/cancel", fatal=False) is None:
        # Keep the id file: it is the only handle to a send that still needs
        # cancelling by hand.
        print(
            f"\nWARNING: the dead-man alert {alert_id} could NOT be cancelled.\n"
            f"         Issue {issue} is queued and will arrive normally, but the\n"
            f"         'aucun numero ce matin' alert will arrive alongside it.\n"
            f"         Cancel it in the Resend dashboard, and note that\n"
            f"         RESEND_API_KEY needs cancel rights (a send-only restricted\n"
            f"         key can POST /emails but cannot cancel a scheduled send).\n"
        )
        return

    os.remove(ALERT_ID_FILE)
    print(f"Dead-man alert cancelled: {alert_id}")


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
