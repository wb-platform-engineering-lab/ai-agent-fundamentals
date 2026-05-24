# 01 · git-narrator

> **Concept: Tool Use** — Claude calls functions you define and uses their results to build its answer.

---

## What you will build

An agent that reads your staged git changes and automatically writes:
- A conventional commit message
- A pull request description
- A one-line changelog entry

```bash
$ python agent.py
✔ Reading staged changes...
✔ Generating commit message...

Commit message:
  feat(auth): add JWT refresh token rotation

PR description:
  ## What
  Implements refresh token rotation to improve session security...

Changelog:
  - feat: JWT refresh token rotation (auth-service)
```

---

## The concept: Tool Use

Before agents, LLMs were input/output machines. You send text, you get text back.

Tool use changes this: Claude can **call functions** in your code, get their results, and incorporate them into its reasoning.

### How it works — step by step

```mermaid
sequenceDiagram
    participant You
    participant Claude
    participant Tools

    You->>Claude: "Summarize my staged changes"<br/>+ list of available tools

    Note over Claude: I need to see the diff first.<br/>I'll call run_git_diff().

    Claude->>Tools: run_git_diff()
    Tools-->>Claude: "diff --git a/auth.py...\n+def rotate_token()..."

    Note over Claude: Now I have the diff.<br/>I can write the commit message.

    Claude->>You: "feat(auth): add JWT refresh token rotation\n\n..."
```

### The critical piece: tool definition

Claude does not magically know what tools exist. You tell it — in the API call — by passing a list of tool definitions. Each definition has:

1. **name** — what Claude calls it: `"run_git_diff"`
2. **description** — why Claude would use it: `"Returns the staged git diff"`
3. **input_schema** — what arguments it takes (JSON Schema)

```python
{
    "name": "run_git_diff",
    "description": "Returns the staged git diff (git diff --staged). "
                   "Use this to see exactly what code changes are about to be committed.",
    "input_schema": {
        "type": "object",
        "properties": {}   # no arguments needed
    }
}
```

Claude reads this description and decides: *"the user wants a commit message, I need the diff first, I should call run_git_diff."*

**The description is everything.** A bad description = Claude won't call the tool at the right time.

### What the API response looks like

When Claude wants to call a tool, it returns a response with `stop_reason = "tool_use"` and a `tool_use` block:

```python
# Claude's response when it wants to call a tool
{
  "stop_reason": "tool_use",
  "content": [
    {
      "type": "tool_use",
      "id": "toolu_01abc123",
      "name": "run_git_diff",
      "input": {}
    }
  ]
}
```

Your code then:
1. Sees `stop_reason == "tool_use"`
2. Finds the tool in its registry
3. Calls the actual Python function
4. Sends the result back to Claude as a `tool_result` message
5. Claude continues and produces its final answer

---

## Architecture

```mermaid
flowchart TD
    A["agent.py\nmain loop"] --> B["Anthropic API\nwith tools list"]
    B -->|stop_reason = tool_use| C{"Which tool?"}
    C -->|run_git_diff| D["subprocess\ngit diff --staged"]
    C -->|read_file| E["open() file"]
    D --> F["tool_result\nsent back to Claude"]
    E --> F
    F --> B
    B -->|stop_reason = end_turn| G["Final answer\nprinted to user"]

    style A fill:#1a3a5c,color:#fff,stroke:none
    style B fill:#1a3a5c,color:#fff,stroke:none
    style G fill:#2d4a22,color:#fff,stroke:none
```

---

## File structure

```
01-git-narrator/
├── README.md       ← you are here
├── tools.py        ← tool definitions + implementations
├── agent.py        ← the agent loop (30 lines)
└── run.sh          ← demo script
```

---

## Step-by-step walkthrough

### Step 1 — Define a tool

Open `tools.py`. A tool has two parts:

**Part A: the definition** (what Claude sees)
```python
{
    "name": "run_git_diff",
    "description": "Returns the currently staged git diff.",
    "input_schema": {"type": "object", "properties": {}}
}
```

**Part B: the implementation** (what your code runs)
```python
def run_git_diff() -> str:
    result = subprocess.run(
        ["git", "diff", "--staged"],
        capture_output=True, text=True
    )
    return result.stdout or "No staged changes found."
```

### Step 2 — Call Claude with tools

In `agent.py`, you pass the tool definitions alongside your message:

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=TOOL_DEFINITIONS,        # ← Claude knows these tools exist
    messages=[{"role": "user", "content": user_message}]
)
```

### Step 3 — Handle the tool call

```python
if response.stop_reason == "tool_use":
    for block in response.content:
        if block.type == "tool_use":
            # Call the actual Python function
            result = dispatch(block.name, block.input)

            # Send the result back to Claude
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                }]
            })
```

### Step 4 — Claude produces the final answer

After receiving the tool result, Claude now has everything it needs and returns `stop_reason = "end_turn"` with the final text.

---

## Run it

```bash
cd 01-git-narrator

# Stage some changes in any git repo
git add some_file.py

# Run the agent
ANTHROPIC_API_KEY=your_key python agent.py

# Or use the demo script (creates fake changes to show the flow)
bash run.sh
```

---

## Exercises

Once you have it running, try these modifications:

1. **Add a tool** — create a `get_branch_name()` tool that runs `git branch --show-current` and include the branch name in the commit message context.

2. **Change the description** — deliberately write a bad tool description (e.g. "this tool does stuff") and see how Claude's behavior changes.

3. **Add an argument** — modify `run_git_diff` to accept a `file_path` argument so Claude can request the diff for a specific file.

---

## Key takeaways

- Claude **never calls your Python functions directly** — it returns a structured JSON request, you run the function, you send back the result
- The **description is the interface** — Claude decides when and how to use tools based purely on your descriptions
- Tools are **stateless** — each tool call is independent; Claude maintains the reasoning context, not the tools
