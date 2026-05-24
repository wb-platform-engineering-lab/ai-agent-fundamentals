"""
orchestrator.py — Runs 3 specialists in parallel, then synthesizes.

The orchestrator's two jobs:
  1. Dispatch: send the diff to all specialists simultaneously
  2. Synthesize: combine their outputs into one coherent review
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

from anthropic import Anthropic
from specialists import performance_agent, security_agent, style_agent

client = Anthropic()
MODEL = "claude-sonnet-4-6"

SYNTHESIS_PROMPT = """You are synthesizing three independent code reviews into one final PR review.

Your job:
1. Deduplicate — if multiple reviewers flagged the same issue, mention it once
2. Prioritize — list blocking issues first (security critical/high), then suggestions
3. Be concrete — keep the line numbers and fix suggestions from the specialists
4. Give a verdict: APPROVE / REQUEST CHANGES / COMMENT

Format:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PR Review
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 SECURITY    (N issues)   OR   ✅ SECURITY    (no issues)
🟡 PERFORMANCE (N issues)   OR   ✅ PERFORMANCE  (no issues)
🟢 STYLE       (N issues)   OR   ✅ STYLE        (no issues)

[findings listed under each section]

Overall: APPROVE / REQUEST CHANGES / COMMENT"""


SPECIALISTS = {
    "security":    security_agent,
    "performance": performance_agent,
    "style":       style_agent,
}

ICONS = {
    "security":    "🔴",
    "performance": "🟡",
    "style":       "🟢",
}


def run_parallel(diff: str) -> dict[str, str]:
    """
    Run all three specialists in parallel.
    Returns a dict: {"security": "...", "performance": "...", "style": "..."}

    Why parallel? The three agents are independent — they all read the same
    diff and produce independent output. No reason to wait for one before
    starting the next. This cuts total time from ~15s to ~5s.
    """
    results = {}

    with ThreadPoolExecutor(max_workers=3) as pool:
        # Submit all three at once
        future_to_name = {
            pool.submit(fn, diff): name
            for name, fn in SPECIALISTS.items()
        }

        # Collect as they complete (not necessarily in submission order)
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                results[name] = future.result()
                print(f"  ✔ {name}-reviewer done")
            except Exception as e:
                results[name] = f"Error: {e}"
                print(f"  ✗ {name}-reviewer failed: {e}")

    return results


def synthesize(reviews: dict[str, str]) -> str:
    """
    Send all three reviews to a synthesis agent that produces the final output.

    The synthesis agent sees all three reviews as context and combines them.
    It deduplicates, prioritizes, and formats.
    """
    combined = "\n\n".join([
        f"=== {name.upper()} REVIEW ===\n{text}"
        for name, text in reviews.items()
    ])

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYNTHESIS_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Synthesize these three specialist reviews:\n\n{combined}",
        }],
    )
    return response.content[0].text


def review(diff: str) -> str:
    """Full pipeline: dispatch → collect → synthesize."""
    print("🔍 Dispatching to specialist agents...")
    reviews = run_parallel(diff)

    print("\nSynthesizing results...")
    return synthesize(reviews)
