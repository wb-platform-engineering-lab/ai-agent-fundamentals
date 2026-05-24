"""
feature-flag-manager — Project 10: State Machine Agents
─────────────────────────────────────────────────────────
Manages feature flags through a defined state machine lifecycle.

How to read this file:
  1. main() accepts a natural language command about feature flags
  2. Agent lists flags, gets details, and performs transitions
  3. The state machine lives in tools.py — invalid transitions are rejected
  4. Claude interprets intent; the tool enforces validity

Key insight: the agent doesn't know the state machine rules — the tool does.
Claude can request any transition, but invalid ones fail with a clear error,
and Claude recovers by reading the error and trying a valid path.
"""

import sys
from anthropic import Anthropic
from tools import DEFINITIONS, dispatch

client = Anthropic()
MODEL = "claude-sonnet-4-6"
MAX_STEPS = 10

SYSTEM_PROMPT = """You are a feature flag manager. You help engineers manage the lifecycle of feature flags.

Feature flag states (in order): draft → canary → rollout → ga → deprecated
Rollbacks allowed: canary → draft, rollout → canary

For each request:
1. Call list_flags to see the current state of all flags
2. If you need details on a specific flag, call get_flag
3. Perform the requested action (create, transition, or report)
4. Confirm what was done and the new state

When a transition is rejected, read the error carefully — it tells you what's valid.
Never guess at state names — use exactly: draft, canary, rollout, ga, deprecated."""


def run_agent(command: str) -> str:
    messages = [{"role": "user", "content": command}]
    step = 0

    while step < MAX_STEPS:
        step += 1
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=DEFINITIONS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return next(
                (b.text for b in response.content if b.type == "text"), ""
            )

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  → calling tool: {block.name}({block.input or ''})")
                    result = dispatch(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})

    return "Reached maximum steps."


def main():
    print("feature-flag-manager — state machine agent")
    print("─" * 45)

    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
    else:
        print("Examples:")
        print("  python3 agent.py 'promote new-checkout-flow to rollout'")
        print("  python3 agent.py 'deprecate dark-mode'")
        print("  python3 agent.py 'create flag payment-v3 for new payment processor'")
        print("  python3 agent.py 'show me all flags and their states'")
        print("  python3 agent.py 'try to skip canary on new-checkout-flow'")
        print()
        command = input("Command: ").strip()
        if not command:
            return

    print(f"\nCommand: {command}\n")
    result = run_agent(command)
    print(f"\n{result}")


if __name__ == "__main__":
    main()
