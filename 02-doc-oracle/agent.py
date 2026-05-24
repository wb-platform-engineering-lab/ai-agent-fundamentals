"""
doc-oracle — Project 02: RAG + Semantic Memory
───────────────────────────────────────────────
Answers questions about your docs by searching ChromaDB first.

Flow:
  1. User asks a question
  2. We search ChromaDB for the most relevant doc chunks
  3. We inject those chunks into Claude's context
  4. Claude answers and cites sources
"""

import sys
from anthropic import Anthropic
from memory import search

client = Anthropic()
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a documentation assistant. You answer questions using ONLY the documentation excerpts provided to you.

Rules:
- Always cite the source document for every claim you make
- If the answer is not in the provided excerpts, say "I don't have documentation on this topic."
- Do not use your general training knowledge — only the provided context
- Format citations as: (source: filename.md)
- Be concise and direct"""


def answer(question: str, k: int = 3) -> str:
    # ── Step 1: search for relevant chunks ────────────────────────────────
    print(f"Searching docs for: '{question}'")
    results = search(question, k=k)

    if not results:
        return (
            "No documents found. "
            "Run: python memory.py --ingest docs/"
        )

    print(f"Found {len(results)} relevant chunks:")
    for r in results:
        print(f"  → {r['source']} (relevance: {r['score']})")
    print()

    # ── Step 2: build context from search results ──────────────────────────
    context_parts = []
    for r in results:
        context_parts.append(
            f"[Source: {r['source']} | relevance: {r['score']}]\n{r['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    # ── Step 3: ask Claude with the retrieved context ──────────────────────
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Documentation excerpts:\n\n{context}\n\n"
                f"Question: {question}"
            )
        }],
    )

    return response.content[0].text


def main():
    if len(sys.argv) > 1:
        # One-shot mode: python agent.py "your question"
        question = " ".join(sys.argv[1:])
        print(answer(question))
    else:
        # Interactive mode
        print("doc-oracle — Ask questions about your docs")
        print("Type 'quit' to exit\n")
        while True:
            question = input("Question: ").strip()
            if question.lower() in ("quit", "exit", "q"):
                break
            if question:
                print()
                print(answer(question))
                print()


if __name__ == "__main__":
    main()
