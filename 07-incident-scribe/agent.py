"""
incident-scribe — Project 07: Structured Output
─────────────────────────────────────────────────
Parses raw incident logs into a validated, structured report.

How to read this file:
  1. main() feeds raw incident text to the agent
  2. The system prompt instructs Claude to call save_incident_report
  3. Claude MUST call the tool — the tool's schema enforces the output shape
  4. We capture the structured data from the tool call, never from text

The key insight: tool_use is a structured output mechanism, not just an
action mechanism. Claude can't return malformed JSON — the schema rejects it.
"""

import json
from anthropic import Anthropic
from tools import DEFINITIONS, get_saved_report, dispatch

client = Anthropic()
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are an incident response engineer creating post-incident reports.

Analyze the incident log and call save_incident_report with your findings.
You MUST call save_incident_report — do not write the report as text.

Extract:
- title: short descriptive title (under 60 chars)
- severity: one of P1, P2, P3, P4
- affected_services: list of service names mentioned
- timeline: list of {time, event} objects in chronological order
- root_cause: one clear sentence
- action_items: list of concrete follow-up tasks"""


def run_agent(incident_log: str) -> dict:
    """
    Run the agent. Returns structured report dict (captured from tool call).
    The agent MUST call save_incident_report — loop ends when it does.
    """
    messages = [{"role": "user", "content": f"Parse this incident log:\n\n{incident_log}"}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=DEFINITIONS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            # Claude gave text instead of calling the tool — shouldn't happen
            # with a strong system prompt, but handle gracefully
            print("Warning: agent responded with text instead of tool call.")
            return {}

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  → calling tool: {block.name}({list(block.input.keys())})")
                    result = dispatch(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})

            # If save_incident_report was called, we're done
            report = get_saved_report()
            if report:
                return report


def main():
    print("incident-scribe — structured incident report generator")
    print("─" * 50)

    # Sample incident log
    incident_log = """
[14:03:22] ALERT: payments-service error rate > 5% (currently 23%)
[14:03:45] On-call engineer paged
[14:05:11] payments-service pod restarts detected (3 in 2 minutes)
[14:06:30] Investigation started — checking logs
[14:08:15] Found: database connection pool exhausted (max_connections=20, active=20)
[14:09:00] Temporary fix: restarted payments-service pods — error rate dropping
[14:11:00] Error rate back to 0.1% — service recovering
[14:15:00] Root cause confirmed: surge in checkout requests (3x normal) after flash sale
           email sent at 14:02 exhausted DB connection pool
[14:20:00] Permanent fix identified: increase max_connections to 100, add connection pooler
[14:25:00] Incident resolved. Duration: 22 minutes. Impact: ~340 failed checkouts
"""

    print("Analyzing incident log...\n")
    report = run_agent(incident_log)

    if report:
        print("\n" + "─" * 50)
        print("Structured Incident Report")
        print("─" * 50)
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
