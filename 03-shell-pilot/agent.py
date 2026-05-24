"""
shell-pilot — Project 03: ReAct Loop
──────────────────────────────────────
Executes natural language tasks in the shell via a Reason→Act→Observe loop.

Key things to notice as you read this:
  - The loop runs until stop_reason == "end_turn" (or MAX_STEPS)
  - The message history grows with each iteration — that's the agent's memory
  - Claude emits text blocks (reasoning) AND tool_use blocks (actions)
  - We print both so you can see the agent thinking
"""

import sys
from anthropic import Anthropic
from tools import DEFINITIONS, dispatch

client = Anthropic()
MODEL = "claude-sonnet-4-6"
MAX_STEPS = 15

SYSTEM_PROMPT = """You are a shell automation expert. You complete tasks by running shell commands and reading files.

For each task:
1. Think about what information you need and what commands will get it
2. Run commands one at a time, reading the results carefully
3. Adapt your approach based on what you find
4. When you have a complete answer, provide a clear summary

Important:
- Always check command results before proceeding — don't assume success
- If a command fails, read the error and try a different approach
- Prefer targeted commands over broad ones (e.g. grep specific patterns, not grep everything)
- When the task is complete, summarize your findings clearly"""


def run(task: str) -> str:
    messages = [{"role": "user", "content": task}]
    step = 0

    print(f"Task: {task}")
    print("─" * 50)

    while step < MAX_STEPS:
        step += 1

        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=DEFINITIONS,
            messages=messages,
        )

        # ── Print Claude's reasoning (text blocks) ─────────────────────────
        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"\n[step {step}] 🧠 {block.text.strip()}")

        # ── Check if done ──────────────────────────────────────────────────
        if response.stop_reason == "end_turn":
            final = next(
                (b.text for b in response.content if b.type == "text"), ""
            )
            print("\n" + "─" * 50)
            return final

        # ── Process tool calls ─────────────────────────────────────────────
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []

        for block in response.content:
            if block.type != "tool_use":
                continue

            args_display = str(block.input)[:80]
            print(f"\n         ⚡ {block.name}({args_display})")

            result = dispatch(block.name, block.input)

            # Show a preview of the result
            preview = result[:200].replace("\n", " ")
            if len(result) > 200:
                preview += f"... [{len(result)} chars total]"
            print(f"         👁 {preview}")

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })

        messages.append({"role": "user", "content": tool_results})

    return f"Task incomplete: reached maximum of {MAX_STEPS} steps."


def main():
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        print("shell-pilot — natural language shell automation")
        print("Examples:")
        print("  python agent.py 'count lines of Python code in this directory'")
        print("  python agent.py 'find all TODO comments and list them'")
        print()
        task = input("Task: ").strip()
        if not task:
            return

    print()
    result = run(task)
    print(result)


if __name__ == "__main__":
    main()
