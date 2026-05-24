"""
Tool definitions for feature-flag-manager.

State machine enforcement lives here — not in the agent prompt.
Claude can request any transition, but the tool rejects invalid ones.

States and valid transitions:
  draft → canary
  canary → rollout | draft   (can roll back to draft)
  rollout → ga | canary       (can roll back to canary)
  ga → deprecated
  deprecated → (terminal, no transitions)
"""

import json
from pathlib import Path
from datetime import datetime

FLAGS_FILE = Path(__file__).parent / "flags.json"

VALID_TRANSITIONS: dict[str, list[str]] = {
    "draft":      ["canary"],
    "canary":     ["rollout", "draft"],
    "rollout":    ["ga", "canary"],
    "ga":         ["deprecated"],
    "deprecated": [],
}

DEFINITIONS = [
    {
        "name": "list_flags",
        "description": (
            "Returns all feature flags with their current state, description, and last updated time. "
            "Use this to get an overview before taking any action."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_flag",
        "description": "Returns details for a specific feature flag including full transition history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Flag name"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "create_flag",
        "description": "Create a new feature flag in the 'draft' state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Flag name (kebab-case)"},
                "description": {"type": "string", "description": "What this flag controls"},
            },
            "required": ["name", "description"],
        },
    },
    {
        "name": "transition_flag",
        "description": (
            "Move a feature flag to a new state. "
            "Valid transitions: draft→canary, canary→rollout or draft, rollout→ga or canary, ga→deprecated. "
            "Invalid transitions are rejected — the state machine enforces the lifecycle."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Flag name"},
                "to_state": {
                    "type": "string",
                    "enum": ["draft", "canary", "rollout", "ga", "deprecated"],
                    "description": "Target state",
                },
                "reason": {"type": "string", "description": "Why this transition is happening"},
            },
            "required": ["name", "to_state"],
        },
    },
]


def _load() -> dict:
    return json.loads(FLAGS_FILE.read_text())


def _save(data: dict) -> None:
    FLAGS_FILE.write_text(json.dumps(data, indent=2))


def list_flags() -> str:
    data = _load()
    lines = [f"{'Flag':<30} {'State':<12} {'Description'}"]
    lines.append("─" * 70)
    for name, flag in data["flags"].items():
        lines.append(f"{name:<30} {flag['state']:<12} {flag['description']}")
    return "\n".join(lines)


def get_flag(name: str) -> str:
    data = _load()
    if name not in data["flags"]:
        return f"Error: flag '{name}' not found."
    flag = data["flags"][name]
    history = "\n".join(
        f"  {h['at'][:16]}  {h['from']} → {h['to']}"
        for h in flag.get("history", [])
    )
    return (
        f"Flag: {name}\n"
        f"State: {flag['state']}\n"
        f"Description: {flag['description']}\n"
        f"Created: {flag['created_at'][:10]}\n"
        f"Updated: {flag['updated_at'][:10]}\n"
        f"History:\n{history or '  (no transitions yet)'}\n"
        f"Valid next states: {', '.join(VALID_TRANSITIONS[flag['state']]) or 'none (terminal)'}"
    )


def create_flag(name: str, description: str) -> str:
    data = _load()
    if name in data["flags"]:
        return f"Error: flag '{name}' already exists."
    now = datetime.utcnow().isoformat() + "Z"
    data["flags"][name] = {
        "state": "draft",
        "description": description,
        "created_at": now,
        "updated_at": now,
        "history": [],
    }
    _save(data)
    return f"Created flag '{name}' in state: draft"


def transition_flag(name: str, to_state: str, reason: str = "") -> str:
    data = _load()
    if name not in data["flags"]:
        return f"Error: flag '{name}' not found."

    flag = data["flags"][name]
    current = flag["state"]
    allowed = VALID_TRANSITIONS.get(current, [])

    # ── State machine enforcement ──────────────────────────────────────
    if to_state not in allowed:
        if not allowed:
            return f"Error: '{name}' is in terminal state '{current}'. No further transitions allowed."
        return (
            f"Error: invalid transition '{current}' → '{to_state}'. "
            f"From '{current}', allowed: {', '.join(allowed)}"
        )

    now = datetime.utcnow().isoformat() + "Z"
    flag["state"] = to_state
    flag["updated_at"] = now
    flag["history"].append({"from": current, "to": to_state, "at": now, "reason": reason})
    _save(data)
    return f"✓ Transitioned '{name}': {current} → {to_state}"


def dispatch(tool_name: str, tool_input: dict) -> str:
    match tool_name:
        case "list_flags":
            return list_flags()
        case "get_flag":
            return get_flag(tool_input["name"])
        case "create_flag":
            return create_flag(tool_input["name"], tool_input["description"])
        case "transition_flag":
            return transition_flag(
                tool_input["name"],
                tool_input["to_state"],
                tool_input.get("reason", ""),
            )
        case _:
            return f"Error: unknown tool '{tool_name}'"
