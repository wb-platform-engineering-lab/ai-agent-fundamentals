"""
Tool definitions and implementations for deploy-watchdog.

Two parts for each tool:
  1. DEFINITION — what Claude sees (name, description, input schema)
  2. IMPLEMENTATION — the actual Python function that runs

The human-in-the-loop gate is trigger_deployment — it blocks on input()
before doing anything, giving the operator a chance to cancel.
"""


# ─────────────────────────────────────────────
# DEFINITIONS (passed to Claude in the API call)
# ─────────────────────────────────────────────

DEFINITIONS = [
    {
        "name": "get_pipeline_status",
        "description": (
            "Returns the current CI/CD pipeline status for all services. "
            "Shows each service's build status, version, and last deployment time. "
            "Call this first to get an overview of what is passing, failing, or pending."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_test_results",
        "description": (
            "Returns the detailed test results for a specific service. "
            "Use this to investigate why a service is failing or to confirm "
            "a service is safe to deploy. Pass the service name exactly as "
            "it appears in the pipeline status."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "The name of the service to check (e.g. 'payments-service')",
                }
            },
            "required": ["service"],
        },
    },
    {
        "name": "trigger_deployment",
        "description": (
            "Triggers a deployment for a service to the specified environment. "
            "IMPORTANT: This tool will pause and ask the human operator for "
            "approval before doing anything. Only call this when you have "
            "confirmed the service is safe to deploy (tests passing, no blockers). "
            "Do not call this for services with failing tests."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "The name of the service to deploy",
                },
                "version": {
                    "type": "string",
                    "description": "The version to deploy (e.g. 'v3.1.0')",
                },
                "environment": {
                    "type": "string",
                    "description": "The target environment (e.g. 'production', 'staging')",
                },
            },
            "required": ["service", "version", "environment"],
        },
    },
]


# ─────────────────────────────────────────────
# IMPLEMENTATIONS (called by agent.py)
# ─────────────────────────────────────────────

def get_pipeline_status() -> str:
    return """\
Pipeline Status (2026-05-24 14:32 UTC)
───────────────────────────────────────
auth-service      ✓ passing   v2.4.1   last deploy: 2h ago
payments-service  ✗ failing   v1.9.3   2 tests failing
api-gateway       ⏳ pending   v3.1.0   ready to deploy
"""


def get_test_results(service: str) -> str:
    if service == "payments-service":
        return """\
Test Results — payments-service v1.9.3
───────────────────────────────────────
Total: 142 tests   Passed: 140   Failed: 2   Skipped: 0

FAILED tests/unit/test_charge.py::test_charge_exceeds_limit
  AssertionError: Expected PaymentLimitError, got None
  The charge limit guard (MAX_CHARGE_USD = 10000) is no longer enforced
  after the refactor in commit a3f91c2. Charges above the limit now
  succeed silently instead of raising an exception.

  assert result.error == "PaymentLimitError"
  AssertionError: assert None == "PaymentLimitError"

FAILED tests/integration/test_refund_flow.py::test_partial_refund_idempotency
  TimeoutError: Stripe webhook callback not received within 5s
  The refund idempotency key is being generated with a non-deterministic
  UUID suffix, causing duplicate refund attempts on retry. This is a
  regression from the idempotency fix in v1.9.2.

  assert webhook_received is True
  TimeoutError: timed out after 5000ms waiting for POST /webhooks/stripe

────────────────────────────────────────────────────
⚠️  DO NOT DEPLOY — 2 critical payment tests failing
"""
    else:
        return f"Test Results — {service}\n───────────────────────\nAll tests passing. ✓"


def trigger_deployment(service: str, version: str, environment: str) -> str:
    print(f"\n{'─'*50}")
    print(f"  ⚠️  DEPLOYMENT APPROVAL REQUIRED")
    print(f"  Service:     {service}")
    print(f"  Version:     {version}")
    print(f"  Environment: {environment}")
    print(f"{'─'*50}")
    answer = input("  Approve deployment? [y/N]: ").strip().lower()
    if answer != "y":
        return f"Deployment of {service} {version} to {environment} was cancelled by operator."
    return f"✓ Deployment of {service} {version} to {environment} started successfully. ETA: 3 minutes."


# ─────────────────────────────────────────────
# DISPATCHER — routes Claude's tool calls to
# the right Python function
# ─────────────────────────────────────────────

def dispatch(tool_name: str, tool_input: dict) -> str:
    match tool_name:
        case "get_pipeline_status":
            return get_pipeline_status()
        case "get_test_results":
            return get_test_results(tool_input.get("service", ""))
        case "trigger_deployment":
            return trigger_deployment(
                tool_input.get("service", ""),
                tool_input.get("version", ""),
                tool_input.get("environment", "production"),
            )
        case _:
            return f"Error: unknown tool '{tool_name}'"
