"""
Tool definitions for config-drift-detector.

Tools:
  read_desired_state  — loads desired_state.yaml
  read_current_state  — loads current_state.json (simulates live API call)
  file_drift_report   — saves the structured drift report
"""

import json
from pathlib import Path
from datetime import datetime

try:
    import yaml
    _yaml_available = True
except ImportError:
    _yaml_available = False

_drift_report: dict = {}

DEFINITIONS = [
    {
        "name": "read_desired_state",
        "description": (
            "Reads the desired infrastructure state from desired_state.yaml. "
            "This is the source of truth for what SHOULD be running."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_current_state",
        "description": (
            "Reads the current live infrastructure state from current_state.json. "
            "This simulates a call to the infrastructure API (Kubernetes, Terraform, etc). "
            "Use this to see what IS actually running."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "file_drift_report",
        "description": (
            "Save the drift report after comparing desired vs current state. "
            "Call this once you have identified all drifts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "One-sentence summary of the overall drift situation",
                },
                "drift_count": {
                    "type": "integer",
                    "description": "Total number of drifts found",
                },
                "drifts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "resource": {"type": "string"},
                            "field": {"type": "string"},
                            "desired": {"type": "string"},
                            "actual": {"type": "string"},
                            "severity": {"type": "string", "enum": ["critical", "warning", "info"]},
                        },
                        "required": ["resource", "field", "desired", "actual", "severity"],
                    },
                    "description": "List of individual drift items",
                },
                "recommendation": {
                    "type": "string",
                    "description": "What action should be taken to remediate",
                },
            },
            "required": ["summary", "drift_count", "drifts", "recommendation"],
        },
    },
]


def read_desired_state() -> str:
    path = Path(__file__).parent / "desired_state.yaml"
    content = path.read_text()
    if _yaml_available:
        data = yaml.safe_load(content)
        return json.dumps(data, indent=2)
    # fallback: return raw YAML if PyYAML not installed
    return content


def read_current_state() -> str:
    path = Path(__file__).parent / "current_state.json"
    return path.read_text()


def file_drift_report(summary: str, drift_count: int, drifts: list, recommendation: str) -> str:
    global _drift_report
    _drift_report = {
        "summary": summary,
        "drift_count": drift_count,
        "drifts": drifts,
        "recommendation": recommendation,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    return f"Drift report filed. {drift_count} drift(s) recorded."


def get_drift_report() -> dict:
    return _drift_report.copy()


def dispatch(tool_name: str, tool_input: dict) -> str:
    match tool_name:
        case "read_desired_state":
            return read_desired_state()
        case "read_current_state":
            return read_current_state()
        case "file_drift_report":
            return file_drift_report(**tool_input)
        case _:
            return f"Error: unknown tool '{tool_name}'"
