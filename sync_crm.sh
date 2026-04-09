#!/bin/bash
# One-shot CRM sync: reads contacts from /tmp/new_contacts.json, appends to CRM, commits, pushes.
# Usage: ./sync_crm.sh "optional commit message"
# Hunter only needs to run THIS single script after writing /tmp/new_contacts.json.

set -e

REPO_DIR="/Users/metavision/.openclaw/workspace-hunter/MVICRM"
INPUT_FILE="/tmp/new_contacts.json"
cd "$REPO_DIR"

MSG="${1:-Update CRM via Hunter}"

# Validate input file
if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: $INPUT_FILE not found — write the contacts JSON there first"
    exit 1
fi

# Validate it's valid JSON
/usr/bin/python3 -c "import json; json.load(open('$INPUT_FILE'))" || {
    echo "ERROR: $INPUT_FILE is not valid JSON"
    exit 1
}

# Step 1: Pull latest
git pull origin main --rebase || true

# Step 2: Append contacts via add_contacts.py
echo "=== Appending contacts ==="
/usr/bin/python3 "$REPO_DIR/add_contacts.py" "$INPUT_FILE" || {
    echo "ERROR: add_contacts.py failed"
    exit 1
}

# Step 3: Validate resulting data.json
/usr/bin/python3 -c "import json; json.load(open('$REPO_DIR/data.json'))" || {
    echo "ERROR: data.json is broken after append — aborting push"
    exit 1
}

# Step 4: Configure git identity
git config user.email "cnuddelouis4@gmail.com" 2>/dev/null || true
git config user.name "Metavision" 2>/dev/null || true

# Step 5: Stage and commit
git add data.json
if git diff --cached --quiet; then
    echo "No changes to commit (contacts may have been duplicates)"
    exit 0
fi

git commit -m "$MSG"

# Step 6: Push to main and gh-pages
git push origin main
git push origin main:gh-pages --force

# Step 7: Clean up input file
rm -f "$INPUT_FILE"

echo "=== Sync complete ==="
git log --oneline -3
