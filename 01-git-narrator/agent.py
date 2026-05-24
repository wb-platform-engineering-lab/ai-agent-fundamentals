"""
git-narrator — Project 01: Tool Use
────────────────────────────────────
Reads staged git changes and generates commit messages + PR descriptions.

How to read this file:
  1. main() sends the user request + tool definitions to Claude
  2. Claude responds with a tool_use block (it wants to call a tool)
  3. We call the tool, get the result, send it back to Claude
  4. Claude now has what it needs and returns the final answer

This loop is the foundation of every AI agent.
"""

import os
from anthropic import Anthropic
from tools import DEFINITIONS, dispatch

client = Anthropic()
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a senior software engineer helping write clear, conventional git commit messages and PR descriptions.

When asked to summarize staged changes:
1. First call run_git_diff to see the actual changes
2. Optionally call get_commit_history to match the existing commit style
3. Then produce:
   - A conventional commit message (type(scope): description)
   - A short PR description (## What, ## Why)
   - A one-line changelog entry

Be concise and specific. Reference the actual code changes, not generic descriptions."""


def run_agent(user_message: str) -> str:
    """
    The agent loop.

    Keeps calling Claude until stop_reason is "end_turn"
    (meaning Claude has all the info it needs and is done).
    """
    messages = [{"role": "user", "content": user_message}]

    while True:
        # ── Step 1: call Claude ──────────────────────────────────────────
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=DEFINITIONS,
            messages=messages,
        )

        # ── Step 2: check if Claude wants to call a tool ─────────────────
        if response.stop_reason == "end_turn":
            # Claude is done — extract and return the text
            return next(b.text for b in response.content if b.type == "text")

        if response.stop_reason == "tool_use":
            # Add Claude's response (including the tool_use block) to messages
            messages.append({"role": "assistant", "content": response.content})

            # Process each tool call
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  → calling tool: {block.name}({block.input or ''})")

                    # ── Step 3: call the actual Python function ───────────
                    result = dispatch(block.name, block.input)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,  # must match Claude's request
                        "content": result,
                    })

            # ── Step 4: send results back to Claude ───────────────────────
            messages.append({"role": "user", "content": tool_results})
            # Loop continues — Claude will now reason with the tool results


def main():
    print("git-narrator — AI commit message generator")
    print("─" * 45)

    user_message = (
        "Look at my staged git changes and generate: "
        "a conventional commit message, a PR description, "
        "and a changelog entry. Match the existing commit style."
    )

    print("Analyzing staged changes...\n")
    result = run_agent(user_message)
    print(result)


if __name__ == "__main__":
    main()
