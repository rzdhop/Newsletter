#!/usr/bin/env bash
#
# OffSec Quotidien - publication tail.
#
# Everything from "the parts are drafted" to "the issue is queued for 06:00",
# as a single script that does not need a live model session to run.
#
# Why this is a script and not steps in prompt.md
# -----------------------------------------------
# A cyber-safeguard block is terminal for the session that trips it: every
# subsequent request fails regardless of content, including `git push` and
# `deliver.py send`. When those steps lived inside the drafting session, a
# flagged subject in Partie 03 did not cost a part - it cost the morning,
# because nothing downstream could run.
#
# Moving the tail here makes the failure survivable in two ways:
#   1. the drafting session calls this once at the end, as before;
#   2. if the session dies first, the operator runs the identical command by
#      hand and the issue still ships from the fragments that survived.
#
# Usage:
#     scripts/publish.sh [work_dir]
#
# Defaults to ./work. Safe to re-run: assemble, render and index are pure
# functions of the fragments, and delivery is the last step.

set -euo pipefail

WORK_DIR="${1:-work}"
CONTENT="content.json"

cd "$(dirname "$0")/.."

if [[ ! -f "${WORK_DIR}/meta.json" ]]; then
  echo "FATAL: ${WORK_DIR}/meta.json not found. Nothing to publish."
  exit 1
fi

# --- 1. Assemble whatever the drafting session managed to write ---------------
# Exits non-zero if no part survived, which leaves the dead-man alert armed.
python3 scripts/assemble.py "${WORK_DIR}" "${CONTENT}"

# Read the issue coordinates back out of the assembled content rather than
# passing them in. The fragments are the single source of truth; a mismatch
# between an argument and the file would publish an issue under the wrong
# number and poison the archive index.
ISSUE=$(python3 -c "import json;print(json.load(open('${CONTENT}'))['meta']['issue'])")
YEAR=$(python3 -c "import json,datetime;print(datetime.date.today().year)")
MONTH=$(python3 -c "import json,datetime;print(f'{datetime.date.today().month:02d}')")
OUT_DIR="issues/${YEAR}/${MONTH}/${ISSUE}"

echo "==> Issue ${ISSUE} -> ${OUT_DIR}"

# --- 2. Render and check the byte budget --------------------------------------
# split.py returns 2 when even a single part overflows the digest budget. That
# is a content problem the operator must see, not something to publish around.
python3 scripts/split.py "${CONTENT}" "${OUT_DIR}"

# --- 3. Ledger before commit --------------------------------------------------
# topics-index.json is written by the drafting session (Step 8.1). Verify it
# actually mentions this issue: a ledger that missed its update leaves tomorrow's
# run free to repeat today's subjects, and that failure is silent by nature.
if ! grep -q "\"issue\"[[:space:]]*:[[:space:]]*${ISSUE}\b" state/topics-index.json; then
  echo "WARNING: state/topics-index.json has no entry for issue ${ISSUE}."
  echo "         Tomorrow's run may repeat today's subjects. Fix before the next run."
fi

# --- 4. Permalinks, then one commit carrying the whole artefact ----------------
python3 scripts/build_index.py

git add "issues/" "state/" "index.html" "${ISSUE}/" 2>/dev/null || git add -A
if git diff --cached --quiet; then
  echo "Nothing staged - issue ${ISSUE} is already committed. Continuing to delivery."
else
  git commit -m "issue ${ISSUE}"
fi

# --- 5. Push to main, explicitly ----------------------------------------------
# A cloud routine starts on an auto-created feature branch and GitHub Pages
# serves only the default branch, so a bare `git push` publishes a permalink
# that 404s inside a mail that has already been sent.
git push origin HEAD:main

# --- 6. Verify the push landed BEFORE delivering ------------------------------
# The mail embeds the permalink, so delivery must not happen until the content
# behind it exists. A mismatch here is a hard stop with the alert left armed:
# a missing issue the operator knows about beats a delivered dead link.
git fetch origin main --quiet
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)
if [[ "${LOCAL}" != "${REMOTE}" ]]; then
  echo "FATAL: HEAD (${LOCAL}) does not match origin/main (${REMOTE})."
  echo "       Push did not land. Dead-man alert left armed on purpose."
  exit 1
fi
echo "==> Push verified on main: ${LOCAL}"

# --- 7. Deliver, and cancel the dead-man alert --------------------------------
python3 scripts/deliver.py send "${OUT_DIR}" "${ISSUE}"

echo "==> Issue ${ISSUE} published and queued."
echo "    Permalink: https://rzdhop.github.io/Newsletter/${ISSUE}"
