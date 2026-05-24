"""
tools.py — Shell tools for shell-pilot.

Safety note: run_command blocks dangerous patterns.
For a real agent, you'd want a sandbox (Docker, etc.).
"""

import subprocess
from pathlib import Path

# Commands that will be blocked regardless of what the agent requests
BLOCKED_PATTERNS = [
    "rm -rf /",
    "rm -rf ~",
    "sudo rm",
    ":(){:|:&};:",  # fork bomb
    "> /dev/sd",
    "curl | bash",
    "wget | sh",
    "| sudo",
]

DEFINITIONS = [
    {
        "name": "run_command",
        "description": (
            "Executes a shell command and returns stdout + stderr. "
            "Use for: finding files (find, ls, grep), running scripts, "
            "checking system state. Commands run in the current directory. "
            "Avoid destructive commands — prefer read-only operations."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute",
                }
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file. Use to inspect source code, configs, or any text file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum lines to return (default: 100). Use to avoid reading huge files.",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file. Creates the file if it doesn't exist, overwrites if it does.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
]


def run_command(command: str) -> str:
    # Safety check
    for pattern in BLOCKED_PATTERNS:
        if pattern in command:
            return f"[BLOCKED] Command contains unsafe pattern: '{pattern}'"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr] {result.stderr}"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 30 seconds"
    except Exception as e:
        return f"Error: {e}"


def read_file(path: str, max_lines: int = 100) -> str:
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        if len(lines) > max_lines:
            shown = "\n".join(lines[:max_lines])
            return f"{shown}\n\n[...{len(lines) - max_lines} more lines not shown. Use max_lines to increase.]"
        return "\n".join(lines) or "(empty file)"
    except FileNotFoundError:
        return f"Error: file not found: {path}"
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path: str, content: str) -> str:
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")
        return f"Written {len(content)} characters to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


def dispatch(tool_name: str, tool_input: dict) -> str:
    match tool_name:
        case "run_command":
            return run_command(tool_input["command"])
        case "read_file":
            return read_file(tool_input["path"], tool_input.get("max_lines", 100))
        case "write_file":
            return write_file(tool_input["path"], tool_input["content"])
        case _:
            return f"Error: unknown tool '{tool_name}'"
