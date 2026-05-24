"""
specialists.py — Three focused review agents.

Each agent is a single API call with a specialized system prompt.
The "intelligence" is in the prompt — not in any framework magic.
"""

from anthropic import Anthropic

client = Anthropic()
MODEL = "claude-sonnet-4-6"

# ─────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPTS — this is where specialization happens
# ─────────────────────────────────────────────────────────────────────────

SECURITY_PROMPT = """You are a security-focused code reviewer. Your ONLY job is to find security vulnerabilities.

Look for:
- Injection attacks (SQL, command, LDAP, XPath)
- Authentication and authorization issues
- Hardcoded secrets, API keys, passwords
- Insecure deserialization
- Sensitive data exposure (PII in logs, unencrypted storage)
- Missing input validation
- Insecure dependencies

Format your response as:
SEVERITY: [CRITICAL|HIGH|MEDIUM|LOW|NONE]
FINDINGS:
- Line X: <issue description> → <recommended fix>

If no security issues found, say: SEVERITY: NONE — No security issues found."""

PERFORMANCE_PROMPT = """You are a performance-focused code reviewer. Your ONLY job is to find performance issues.

Look for:
- N+1 query problems
- Missing database indexes (implied by query patterns)
- Unnecessary loops or nested iterations
- Large objects loaded into memory
- Missing caching opportunities
- Blocking I/O in hot paths
- Inefficient data structures

Format your response as:
SEVERITY: [HIGH|MEDIUM|LOW|NONE]
FINDINGS:
- Line X: <issue description> → <recommended fix>

If no performance issues found, say: SEVERITY: NONE — No performance issues found."""

STYLE_PROMPT = """You are a style and maintainability code reviewer. Your ONLY job is to check code quality and conventions.

Look for:
- Missing or incomplete docstrings on public functions/classes
- Missing type hints in Python code
- Functions that are too long (>50 lines) or doing too many things
- Unclear variable names
- Duplicate code that could be extracted
- Missing error handling for obvious failure cases
- Inconsistent naming conventions

Format your response as:
SEVERITY: [HIGH|MEDIUM|LOW|NONE]
FINDINGS:
- Line X: <issue description> → <recommended fix>

If no style issues, say: SEVERITY: NONE — Code follows conventions well."""


# ─────────────────────────────────────────────────────────────────────────
# AGENT FUNCTIONS — each is an independent API call
# ─────────────────────────────────────────────────────────────────────────

def security_agent(diff: str) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SECURITY_PROMPT,
        messages=[{"role": "user", "content": f"Review this code diff:\n\n```diff\n{diff}\n```"}],
    )
    return response.content[0].text


def performance_agent(diff: str) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=PERFORMANCE_PROMPT,
        messages=[{"role": "user", "content": f"Review this code diff:\n\n```diff\n{diff}\n```"}],
    )
    return response.content[0].text


def style_agent(diff: str) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=STYLE_PROMPT,
        messages=[{"role": "user", "content": f"Review this code diff:\n\n```diff\n{diff}\n```"}],
    )
    return response.content[0].text
