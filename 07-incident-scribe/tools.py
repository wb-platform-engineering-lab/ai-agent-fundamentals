"""
Tool definitions for incident-scribe.

One tool: save_incident_report
This tool's schema IS the output schema — Claude must conform to it.
"""

from datetime import datetime

# Module-level storage for the captured report
_saved_report: dict = {}


DEFINITIONS = [
    {
        "name": "save_incident_report",
        "description": (
            "Save the structured incident report. Call this once after analyzing "
            "the incident log. This is the ONLY way to submit your findings."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short descriptive title for the incident (under 60 chars)",
                },
                "severity": {
                    "type": "string",
                    "enum": ["P1", "P2", "P3", "P4"],
                    "description": "P1=critical/outage, P2=major degradation, P3=minor, P4=informational",
                },
                "affected_services": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of service names affected",
                },
                "timeline": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "time": {"type": "string"},
                            "event": {"type": "string"},
                        },
                        "required": ["time", "event"],
                    },
                    "description": "Chronological list of events with timestamps",
                },
                "root_cause": {
                    "type": "string",
                    "description": "One clear sentence describing the root cause",
                },
                "action_items": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of concrete follow-up tasks to prevent recurrence",
                },
            },
            "required": ["title", "severity", "affected_services", "timeline", "root_cause", "action_items"],
        },
    },
]


def save_incident_report(
    title: str,
    severity: str,
    affected_services: list,
    timeline: list,
    root_cause: str,
    action_items: list,
) -> str:
    global _saved_report
    _saved_report = {
        "title": title,
        "severity": severity,
        "affected_services": affected_services,
        "timeline": timeline,
        "root_cause": root_cause,
        "action_items": action_items,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    return "Report saved successfully."


def get_saved_report() -> dict:
    """Called by agent.py to retrieve the captured report."""
    return _saved_report.copy() if _saved_report else {}


def dispatch(tool_name: str, tool_input: dict) -> str:
    match tool_name:
        case "save_incident_report":
            return save_incident_report(**tool_input)
        case _:
            return f"Error: unknown tool '{tool_name}'"
