"""
Tool definitions and implementations for git-narrator.

Two parts for each tool:
  1. DEFINITION — what Claude sees (name, description, input schema)
  2. IMPLEMENTATION — the actual Python function that runs
"""

import subprocess


# ─────────────────────────────────────────────
# DEFINITIONS (passed to Claude in the API call)
# ─────────────────────────────────────────────

DEFINITIONS = [
    {
        "name": "run_git_diff",
        "description": (
            "Returns the currently staged git diff (git diff --staged). "
            "Use this to see exactly which lines of code are about to be committed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the file to diff (default: current directory)",
                }
            },
        },
    },
    {
        "name": "get_commit_history",
        "description": (
            "Returns the last N commit messages in this repository. "
            "Use this to understand the existing commit style and conventions "
            "before writing a new commit message."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "Number of recent commits to fetch (default: 5)",
                }
            },
        },
    },
    {
        "name": "get_branch_name",
        "description": (
            "Returns the current git branch name (git branch --show-current). "
            "Use this to include the branch name as context when writing the commit message."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
]


# ─────────────────────────────────────────────
# IMPLEMENTATIONS (called by agent.py)
# ─────────────────────────────────────────────

def run_git_diff() -> str:
    result = subprocess.run(
        ["git", "diff", "--staged"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"git error: {result.stderr}"
    return result.stdout.strip() or "No staged changes found."


def get_commit_history(count: int = 5) -> str:
    result = subprocess.run(
        ["git", "log", f"--oneline", f"-{count}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"git error: {result.stderr}"
    return result.stdout.strip() or "No commit history found."



def get_branch_name() -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"git error: {result.stderr}"
    return result.stdout.strip() or "No branch name found."


# ─────────────────────────────────────────────
# DISPATCHER — routes Claude's tool calls to
# the right Python function
# ─────────────────────────────────────────────

def dispatch(tool_name: str, tool_input: dict) -> str:
    match tool_name:
        case "run_git_diff":
            return run_git_diff()
        case "get_commit_history":
            return get_commit_history(tool_input.get("count", 5))
        case "get_branch_name":
            return get_branch_name()
        case _:
            return f"Error: unknown tool '{tool_name}'"
