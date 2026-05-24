"""
mcp-server — Project 11: MCP Server for Claude Code
─────────────────────────────────────────────────────
A custom MCP server that exposes git tools to Claude Code.

Once connected, Claude Code can call these tools directly in any conversation
without any agent code — just like it uses built-in tools.

Run this server:
  python3 server.py

Connect it to Claude Code:
  See README.md for claude_desktop_config.json setup
"""

import subprocess
from mcp.server.fastmcp import FastMCP

# Create the MCP server — the name appears in Claude's tool list
mcp = FastMCP("git-tools")


@mcp.tool()
def get_staged_diff() -> str:
    """
    Returns the currently staged git diff (git diff --staged).
    Use this to see exactly which lines of code are about to be committed.
    """
    result = subprocess.run(
        ["git", "diff", "--staged"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return f"git error: {result.stderr}"
    return result.stdout.strip() or "No staged changes found."


@mcp.tool()
def get_branch_name() -> str:
    """
    Returns the current git branch name.
    Use this when the branch name provides context for a commit message.
    """
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return f"git error: {result.stderr}"
    return result.stdout.strip() or "No branch name found."


@mcp.tool()
def get_commit_history(count: int = 5) -> str:
    """
    Returns the last N git commit messages.
    Use this to understand the project's commit style before writing a new message.
    """
    result = subprocess.run(
        ["git", "log", "--oneline", f"-{count}"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return f"git error: {result.stderr}"
    return result.stdout.strip() or "No commit history found."


@mcp.tool()
def get_repo_status() -> str:
    """
    Returns the current git status (staged, unstaged, untracked files).
    Use this to understand the overall state of the repository.
    """
    result = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return f"git error: {result.stderr}"
    return result.stdout.strip() or "Working tree clean."


if __name__ == "__main__":
    mcp.run()
