#!/usr/bin/env python3
"""
Safe CRM contact appender for Hunter.

Usage: python3 add_contacts.py <path_to_contacts_json>

The input file should contain a JSON array of contact objects. Each contact needs at minimum:
  - name, organization, email, lead_score, priority_tag, category, segment,
    s1_segment_match, s2_role_fit, s3_reachability, s4_content_recency, score_rationale

This script:
  1. Reads the current data.json
  2. Assigns new sequential IDs (starting from max existing + 1)
  3. Skips duplicates (by name + organization)
  4. Appends the new contacts
  5. Writes data.json atomically with valid JSON
  6. Reports what was added, what was skipped
"""

import json
import sys
import os
from pathlib import Path

CRM_PATH = Path('/Users/metavision/.openclaw/workspace-hunter/MVICRM/data.json')

REQUIRED_FIELDS = ['name', 'organization', 'lead_score']
DEFAULT_FIELDS = {
    'email': '',
    'phone': '',
    'location': '',
    'region': '',
    'category': 'Uncategorized',
    'notes': '',
    'source': 'Hunter search',
    'linkedin': '',
    'contact_person': '',
    'priority_tag': 'NURTURE',
    'score_rationale': '',
    'segment': None,
    's1_segment_match': 0,
    's2_role_fit': 0,
    's3_reachability': 0,
    's4_content_recency': 0,
}

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 add_contacts.py <contacts.json>", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Load new contacts
    with open(input_path) as f:
        new_contacts = json.load(f)
    if not isinstance(new_contacts, list):
        print("Input must be a JSON array of contact objects", file=sys.stderr)
        sys.exit(1)

    # Load existing CRM
    with open(CRM_PATH) as f:
        data = json.load(f)
    contacts = data.get('contacts', [])

    # Build dedupe set: (name_lower, org_lower)
    existing = {
        (c.get('name', '').strip().lower(), c.get('organization', '').strip().lower())
        for c in contacts
    }

    max_id = max((c.get('id', 0) or 0) for c in contacts) if contacts else 0

    added = []
    skipped = []
    errors = []

    for i, new_c in enumerate(new_contacts):
        # Validate required fields
        missing = [f for f in REQUIRED_FIELDS if not new_c.get(f)]
        if missing:
            errors.append(f"Contact #{i}: missing {missing}")
            continue

        key = (new_c.get('name', '').strip().lower(), new_c.get('organization', '').strip().lower())
        if key in existing:
            skipped.append(f"{new_c['name']} @ {new_c['organization']}")
            continue

        # Apply defaults for missing fields
        full_contact = {**DEFAULT_FIELDS, **new_c}
        max_id += 1
        full_contact['id'] = max_id

        # Auto-calculate priority_tag if not set correctly
        score = full_contact.get('lead_score', 0)
        if score >= 7.0:
            full_contact['priority_tag'] = 'HOT'
        elif score >= 5.0:
            full_contact['priority_tag'] = 'ACTIVE'
        else:
            full_contact['priority_tag'] = 'NURTURE'

        contacts.append(full_contact)
        existing.add(key)
        added.append(f"{full_contact['name']} @ {full_contact['organization']} (ID {max_id}, score {score})")

    data['contacts'] = contacts

    # Atomic write: write to temp file, then rename
    tmp_path = CRM_PATH.with_suffix('.json.tmp')
    with open(tmp_path, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, CRM_PATH)

    # Verify the written file is valid JSON
    with open(CRM_PATH) as f:
        json.load(f)

    print(f"=== CRM Update Summary ===")
    print(f"Added: {len(added)}")
    for a in added:
        print(f"  + {a}")
    if skipped:
        print(f"Skipped (duplicates): {len(skipped)}")
        for s in skipped:
            print(f"  = {s}")
    if errors:
        print(f"Errors: {len(errors)}")
        for e in errors:
            print(f"  ! {e}")
    print(f"Total contacts in CRM: {len(contacts)}")
    print(f"File: {CRM_PATH}")

if __name__ == '__main__':
    main()
