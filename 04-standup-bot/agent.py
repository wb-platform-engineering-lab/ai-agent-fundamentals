"""
standup-bot — Project 04: Episodic Memory
──────────────────────────────────────────
A daily work assistant that remembers across sessions.

Usage:
  python agent.py morning   ← start the day with context from yesterday
  python agent.py evening   ← end the day, log what happened
  python agent.py weekly    ← weekly summary for your manager
"""

import json
import sys
from anthropic import Anthropic
from memory import DayEntry, build_context, load_entry, save_entry, today, yesterday

client = Anthropic()
MODEL = "claude-sonnet-4-6"

BASE_SYSTEM = """You are a friendly standup assistant helping a developer track their daily work.

Be concise and practical. Ask one or two focused questions at a time.
When the user is done, extract their key points (completed tasks, blockers, plan).

Today's date: {date}

{memory_context}"""


def _chat(system: str, opening: str) -> list[dict]:
    """Simple interactive chat loop. Returns the full conversation history."""
    messages = []
    print(f"\n{opening}\n")

    # Print opening message as assistant
    messages.append({"role": "assistant", "content": opening})

    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() in ("done", "bye", "exit", "quit"):
            break

        messages.append({"role": "user", "content": user_input})

        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=system,
            messages=messages,
        )
        reply = response.content[0].text
        messages.append({"role": "assistant", "content": reply})
        print(f"\nBot: {reply}\n")

    return messages


def _extract_structured(conversation: list[dict]) -> dict:
    """Ask Claude to extract structured data from the conversation."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system="Extract structured data from this conversation. Return ONLY valid JSON.",
        messages=[
            *conversation,
            {
                "role": "user",
                "content": (
                    "Extract from this conversation:\n"
                    "- plan: string (what they plan to work on, or empty)\n"
                    "- completed: list of strings (tasks completed)\n"
                    "- blockers: list of strings (current blockers)\n"
                    "- notes: string (other relevant notes)\n\n"
                    "Return JSON only. Example: "
                    '{"plan": "...", "completed": [...], "blockers": [...], "notes": "..."}'
                ),
            },
        ],
    )
    try:
        return json.loads(response.content[0].text)
    except json.JSONDecodeError:
        return {"plan": "", "completed": [], "blockers": [], "notes": ""}


def morning():
    """Morning standup — recall yesterday, plan today."""
    system = BASE_SYSTEM.format(
        date=today(),
        memory_context=build_context(days_back=3),
    )

    # Load yesterday's entry to surface blockers
    prev = load_entry(yesterday())
    if prev and prev.blockers:
        opening = (
            f"Good morning! 👋\n\n"
            f"Yesterday you were blocked on: {', '.join(prev.blockers)}\n\n"
            f"What are you working on today?"
        )
    elif prev and prev.completed:
        opening = (
            f"Good morning! 👋\n\n"
            f"Yesterday you completed: {', '.join(prev.completed)}\n\n"
            f"What's on your plate today?"
        )
    else:
        opening = "Good morning! 👋 What are you working on today?"

    conversation = _chat(system, opening)

    # Extract and save
    data = _extract_structured(conversation)
    entry = load_entry(today()) or DayEntry(date=today())
    entry.plan = data.get("plan", "")
    entry.blockers = data.get("blockers", [])
    save_entry(entry)

    print("\n✔ Morning standup saved.")


def evening():
    """Evening check-in — log what happened, update blockers."""
    system = BASE_SYSTEM.format(
        date=today(),
        memory_context=build_context(days_back=2),
    )

    # Load today's morning plan to reference it
    today_entry = load_entry(today())
    if today_entry and today_entry.plan:
        opening = (
            f"Evening! 🌆\n\n"
            f"This morning you planned: {today_entry.plan}\n\n"
            f"How did it go?"
        )
    else:
        opening = "Evening! 🌆 How did your day go?"

    conversation = _chat(system, opening)

    # Extract and save
    data = _extract_structured(conversation)
    entry = load_entry(today()) or DayEntry(date=today())
    entry.notes = data.get("notes", "")
    entry.completed = data.get("completed", [])
    entry.blockers = data.get("blockers", [])
    save_entry(entry)

    print("\n✔ Evening notes saved.")


def weekly():
    """Generate a weekly summary."""
    context = build_context(days_back=7)

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system="You are a helpful assistant writing a concise weekly work summary.",
        messages=[{
            "role": "user",
            "content": (
                f"Based on these standup entries, write a clear weekly summary "
                f"for a manager. Include: what was completed, what's in progress, "
                f"any recurring blockers, and overall progress.\n\n{context}"
            ),
        }],
    )

    print("\n📋 Weekly Summary")
    print("─" * 40)
    print(response.content[0].text)


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "morning"
    match command:
        case "morning":
            morning()
        case "evening":
            evening()
        case "weekly":
            weekly()
        case _:
            print("Usage: python agent.py [morning|evening|weekly]")


if __name__ == "__main__":
    main()
