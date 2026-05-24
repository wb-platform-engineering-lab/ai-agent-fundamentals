"""
codebase-navigator — Project 08: Hierarchical Summarization
─────────────────────────────────────────────────────────────
Answers questions about a codebase too large to fit in one context window.

How to read this file:
  1. Phase 1 (Map):    For each source file, ask Claude to summarize it in 3 bullets
  2. Phase 2 (Reduce): Give all summaries to Claude and ask it to answer the question
  3. The key insight:  We never send all the code at once — only summaries

This is the map-reduce pattern applied to LLMs:
  map:    file → summary        (many small Claude calls)
  reduce: summaries → answer    (one final Claude call)
"""

import sys
from pathlib import Path
from anthropic import Anthropic

client = Anthropic()
MODEL = "claude-sonnet-4-6"


def summarize_file(file_path: str, content: str) -> str:
    """Phase 1 (Map): Summarize a single file in 3 bullets."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        system="You are a code summarizer. Be brief and precise.",
        messages=[{
            "role": "user",
            "content": (
                f"Summarize this file in exactly 3 bullet points. "
                f"Focus on: what it does, key functions/classes, dependencies.\n\n"
                f"File: {file_path}\n\n{content}"
            ),
        }],
    )
    return response.content[0].text


def answer_question(question: str, summaries: dict[str, str]) -> str:
    """Phase 2 (Reduce): Answer a question using all file summaries."""
    summary_block = "\n\n".join(
        f"### {path}\n{summary}" for path, summary in summaries.items()
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=(
            "You are a codebase expert. Answer questions using the file summaries provided. "
            "Be specific — reference file names and function names in your answer. "
            "If you can't answer from the summaries, say so."
        ),
        messages=[{
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"Codebase summaries:\n\n{summary_block}"
            ),
        }],
    )
    return response.content[0].text


def run(question: str, path: str = ".") -> str:
    """Main entry point: map-reduce over the codebase."""
    # ── Discover files ────────────────────────────────────────────────────
    root = Path(path)
    files = sorted(root.rglob("*.py"))

    # Exclude common non-meaningful files
    files = [
        f for f in files
        if not any(part.startswith((".venv", "__pycache__", ".git")) for part in f.parts)
    ]

    if not files:
        return f"No Python files found in {path}"

    print(f"Found {len(files)} Python file(s). Summarizing...\n")

    # ── Phase 1: Map ─────────────────────────────────────────────────────
    summaries = {}
    for f in files:
        content = f.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            continue
        print(f"  → summarizing {f}")
        summaries[str(f)] = summarize_file(str(f), content[:3000])  # cap at 3k chars per file

    # ── Phase 2: Reduce ──────────────────────────────────────────────────
    print(f"\nSynthesizing {len(summaries)} summaries to answer your question...\n")
    return answer_question(question, summaries)


def main():
    if len(sys.argv) < 2:
        print("codebase-navigator — answer questions about a codebase")
        print()
        print("Usage:")
        print("  python3 agent.py 'What does this codebase do?'")
        print("  python3 agent.py 'Where is error handling?' ../some-project")
        print("  python3 agent.py 'List all entry points'")
        return

    question = sys.argv[1]
    path = sys.argv[2] if len(sys.argv) > 2 else "."

    print("codebase-navigator — hierarchical summarization")
    print("─" * 50)
    print(f"Question: {question}")
    print(f"Path:     {path}")
    print()

    answer = run(question, path)
    print("─" * 50)
    print(answer)


if __name__ == "__main__":
    main()
