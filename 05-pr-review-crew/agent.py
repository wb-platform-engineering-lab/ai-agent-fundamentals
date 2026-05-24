"""
pr-review-crew — Project 05: Multi-Agent Orchestration
────────────────────────────────────────────────────────
Usage:
  python agent.py sample.diff          # review a diff file
  python agent.py /path/to/file.diff   # review any diff file
  git diff HEAD~1 | python agent.py -  # pipe from git
"""

import sys
from orchestrator import review


def main():
    # Read diff from file or stdin
    if len(sys.argv) > 1 and sys.argv[1] != "-":
        path = sys.argv[1]
        try:
            with open(path) as f:
                diff = f.read()
        except FileNotFoundError:
            print(f"Error: file not found: {path}")
            sys.exit(1)
    else:
        # Read from stdin (piped input)
        diff = sys.stdin.read()

    if not diff.strip():
        print("Error: empty diff. Stage some changes or provide a .diff file.")
        sys.exit(1)

    print(f"\nReviewing diff ({len(diff)} chars, ~{len(diff.split(chr(10)))} lines)\n")

    result = review(diff)

    print("\n" + result)


if __name__ == "__main__":
    main()
