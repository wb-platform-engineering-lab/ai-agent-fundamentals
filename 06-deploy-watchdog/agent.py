"""
deploy-watchdog — Project 06: Human-in-the-Loop
─────────────────────────────────────────────────
Monitors a CI/CD pipeline and gates deployments behind human approval.

How to read this file:
  1. main() asks the agent to assess the pipeline and recommend action
  2. Agent calls tools to gather pipeline state and test results
  3. If deployment is warranted, agent calls trigger_deployment
  4. trigger_deployment pauses and asks the human to approve before acting

The human-in-the-loop gate lives inside the tool — not in the agent loop.
This is the simplest pattern: the tool itself is the checkpoint.
"""

from anthropic import Anthropic
from tools import DEFINITIONS, dispatch

client = Anthropic()
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a deployment watchdog agent responsible for monitoring a CI/CD pipeline
and recommending safe deployments.

Your process:
1. Call get_pipeline_status to see the current state of all services
2. Call get_test_results for any service that shows failures or is pending deployment
3. Summarize what you find — which services are healthy, which are failing and why
4. If a service looks safe to deploy (tests passing, no blockers), call trigger_deployment
   for that service — but warn the user upfront that this tool will pause and ask for confirmation

Important rules:
- Never recommend deploying a service with failing tests
- Always check test results before recommending or triggering a deployment
- Be specific about which tests are failing and why
- When calling trigger_deployment, use the version shown in the pipeline status
- Target environment is "production" unless told otherwise
- The trigger_deployment tool will ask for human approval — this is expected and required"""


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
            max_tokens=2048,
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
    print("deploy-watchdog — CI/CD pipeline monitor with human-in-the-loop")
    print("─" * 65)

    user_message = (
        "Check the current pipeline status. Identify any failures and "
        "investigate their root cause. If any service is ready to deploy "
        "and it's safe to do so, proceed with the deployment — but I know "
        "you'll ask me to confirm before anything actually happens."
    )

    print("Assessing pipeline...\n")
    result = run_agent(user_message)
    print("\n" + result)


if __name__ == "__main__":
    main()
