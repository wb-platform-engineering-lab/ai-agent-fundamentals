#!/bin/bash
# Demo script — creates a fake file, stages it, runs the agent, then cleans up

set -e

echo "=== git-narrator demo ==="
echo ""

# Make sure we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: not in a git repository."
  echo "Run: git init && git commit --allow-empty -m 'initial commit'"
  exit 1
fi

# Create a fake change to demonstrate the agent
cat > /tmp/demo_auth.py << 'EOF'
def rotate_refresh_token(user_id: str) -> str:
    """
    Invalidates the current refresh token and issues a new one.
    Prevents token reuse attacks.
    """
    old_token = get_refresh_token(user_id)
    revoke_token(old_token)
    new_token = generate_secure_token()
    store_refresh_token(user_id, new_token)
    return new_token
EOF

cp /tmp/demo_auth.py ./demo_auth.py
git add -f demo_auth.py

echo "Staged file: demo_auth.py (JWT refresh token rotation)"
echo ""

# Run the agent
python3 agent.py

# Cleanup
git restore --staged demo_auth.py
rm -f demo_auth.py

echo ""
echo "=== demo complete ==="
