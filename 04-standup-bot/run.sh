#!/bin/bash
# Simulates a week of standup entries to demo the memory feature

echo "=== standup-bot demo (simulated week) ==="
echo "This script pre-populates 5 days of entries to show memory in action."
echo ""

python - << 'EOF'
from memory import DayEntry, save_entry

entries = [
    DayEntry("2026-05-18", plan="Backend API refactor", completed=["Setup dev environment"], blockers=[]),
    DayEntry("2026-05-19", plan="Continue API refactor + write tests", completed=["Backend API refactor"], blockers=["Flaky auth test — can't reproduce"]),
    DayEntry("2026-05-20", plan="Fix flaky test, start Vault integration", completed=["Fixed flaky test (race condition)"], blockers=["Vault config — KMS not auto-unsealing"]),
    DayEntry("2026-05-21", plan="Resolve Vault KMS issue", completed=["Vault KMS auto-unseal fixed", "Dynamic creds working"], blockers=[]),
    DayEntry("2026-05-22", plan="Vault audit logging + revoke root token", completed=["Vault audit log", "Root token revoked"], blockers=[]),
]
for e in entries:
    save_entry(e)
    print(f"  ✔ Saved entry for {e.date}")

print("\nSample week loaded.")
EOF

echo ""
echo "Now generating weekly summary from memory..."
echo ""
python agent.py weekly
