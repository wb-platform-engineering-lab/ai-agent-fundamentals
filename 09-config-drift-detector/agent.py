"""
config-drift-detector — Project 09: Scheduled / Event-Driven Agents
─────────────────────────────────────────────────────────────────────
Compares desired infrastructure state against live state and reports drift.

How to read this file:
  1. main() triggers the agent (simulating a cron job or CI step)
  2. Agent reads desired_state.yaml (what should be)
  3. Agent reads current_state.json (what is)
  4. Agent compares and calls file_drift_report with structured findings

Key insight: this agent has no interactive user. It runs, does its job,
and exits. The trigger could be: cron, CI pipeline, git hook, or webhook.
"""

import json
from anthropic import Anthropic
from tools import DEFINITIONS, get_drift_report, dispatch

client = Anthropic()
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are an infrastructure reliability engineer running an automated drift check.

Your job:
1. Call read_desired_state to get the desired configuration
2. Call read_current_state to get what is actually running
3. Compare every field: replicas, image versions, env vars, feature flags
4. Call file_drift_report with all differences you find

For each drift, assess severity:
  critical = service degradation risk (wrong replicas, wrong image version)
  warning   = config mismatch that could cause issues (wrong env vars)
  info      = minor differences (logging levels, non-critical flags)

Be thorough — compare every field in every service."""


def run_agent() -> dict:
    messages = [{"role": "user", "content": "Run a full infrastructure drift check now."}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=DEFINITIONS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return get_drift_report()

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

            report = get_drift_report()
            if report:
                return report


def main():
    print("config-drift-detector — infrastructure drift check")
    print("─" * 50)
    print("Trigger: manual run (see run.sh for cron setup)")
    print()

    report = run_agent()

    if report:
        print("\n" + "─" * 50)
        drifts = report.get("drifts", [])
        critical = [d for d in drifts if d.get("severity") == "critical"]
        warnings = [d for d in drifts if d.get("severity") == "warning"]

        print(f"Summary: {report.get('summary', '')}")
        print(f"Total drifts: {report.get('drift_count', 0)} ({len(critical)} critical, {len(warnings)} warnings)")
        print()
        print("Drifts found:")
        for d in drifts:
            icon = "🔴" if d["severity"] == "critical" else "🟡" if d["severity"] == "warning" else "🔵"
            print(f"  {icon} {d['resource']}.{d['field']}: {d['desired']} → {d['actual']}")
        print()
        print(f"Recommendation: {report.get('recommendation', '')}")
        print()
        print("Full report (JSON):")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
