#!/bin/bash
# Safe commit and push for the MVICRM repo.
# Usage: ./commit_and_push.sh "commit message"
# This script handles all git operations in one place so Hunter doesn't need to chain commands.

set -e

REPO_DIR="/Users/metavision/.openclaw/workspace-hunter/MVICRM"
cd "$REPO_DIR"

MSG="${1:-Update CRM via Hunter}"

# Validate we're in a git repo
if [ ! -d .git ]; then
    echo "ERROR: $REPO_DIR is not a git repo"
    exit 1
fi

# Validate data.json is parseable
python3 -c "import json; json.load(open('data.json'))" || {
    echo "ERROR: data.json is not valid JSON — aborting"
    exit 1
}

# Pull latest
git pull origin main --rebase || true

# Configure identity if not set
git config user.email "cnuddelouis4@gmail.com" 2>/dev/null || true
git config user.name "Metavision" 2>/dev/null || true

# Stage and commit
git add data.json
if git diff --cached --quiet; then
    echo "No changes to commit"
    exit 0
fi

git commit -m "$MSG"

# Push to main and gh-pages
git push origin main
git push origin main:gh-pages --force

echo "=== Push complete ==="
git log --oneline -3
