# ChatGPT Task Scheduler — Exercise

## How to Use

1. Read `PROMPT.md`
2. Answer the Design Questions (write your answers directly in `PROMPT.md`)
3. Build the prototype:
   - **Challenge Track:** Build from scratch using `PROMPT.md` as your spec
   - **Guided Track:** Go to `scaffold/`, fill in the TODOs
4. Verify with the MCP inspector tests at the bottom of `PROMPT.md`
5. Bring your Design Questions answers to live session for discussion

## Choose Your Track

**Challenge Track** — You decide the architecture, file structure, and implementation. Any language with an MCP SDK works (Python + the official `mcp` SDK recommended). Read `PROMPT.md` to get started.

**Guided Track** — File structure and boilerplate are provided. Fill in the core logic marked with `TODO`. Go to `scaffold/` and follow the instructions below.

## Guided Track Setup

Install [uv](https://docs.astral.sh/uv/), then from the repo root:

```bash
cd scaffold
uv sync
```

This creates `.venv` in `scaffold/` and installs all Python dependencies (MCP server, SQLAlchemy, LLM SDKs, etc.).

Activate the venv when running commands manually:

```bash
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows
```

Or prefix commands with `uv run` (no activation needed):

```bash
uv run python -m app.mcp_server
```

You also need **Node.js** for `npx` (used by the MCP inspector for verification).

### LLM API keys (worker / job execution)

When a scheduled job runs, the worker calls an LLM with the job `description` via `LLMCaller` (`scaffold/app/LLMcaller.py`). Configure keys in a `.env` file at the **repo root** (`chatgpt_task/.env`, next to this README):

```bash
# At least one provider key is required for jobs that call the LLM
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Optional: which provider to use (default: anthropic)
# LLM_PROVIDER=anthropic   # anthropic | openai | gemini
```

| Variable | Used by |
|----------|---------|
| `ANTHROPIC_API_KEY` | Anthropic (`claude-haiku-4-5`) |
| `OPENAI_API_KEY` | OpenAI (`gpt-5.4-mini-2026-03-17`) |
| `GEMINI_API_KEY` | Google Gemini (`gemini-3.5-flash`) |
| `LLM_PROVIDER` | Selects adapter when not passed explicitly |

`.env` is gitignored — do not commit real keys.

**Test an LLM call against a stored job** (reads `scaffold/data/chatgpt_task.db`):

```bash
cd scaffold
uv run python scripts/test_llm_job.py --job-id 1
uv run python scripts/test_llm_job.py --job-id 1 --provider openai
```

The MCP server loads the same `.env` on startup so the background worker can use your keys.

### Files to Fill In

| File | TODO | Design Decision |
|------|------|-----------------|
| `app/scheduler.py` | `get_time_bucket()` + `find_due_jobs()` | Time bucket partitioning for efficient job scanning |
| `app/mcp_server.py` | `TOOL_REGISTRY` + `route_tool_call()` | Registry pattern for MCP tool routing |

### Run and Verify

The prototype is a real MCP stdio server. Verify with the MCP inspector (no Claude needed):

```bash
cd scaffold
npx @modelcontextprotocol/inspector uv run python -m app.mcp_server
```

This opens a browser GUI — see `PROMPT.md` Verification section for the full test flow.

## Claude Desktop

### Configure `claude_desktop_config.json`

Edit Claude Desktop’s config (macOS):

`~/Library/Application Support/Claude/claude_desktop_config.json`

Use **absolute paths** to your venv Python and set **`cwd`** to `scaffold/` so the app module and `data/chatgpt_task.db` resolve correctly:

```json
{
  "mcpServers": {
    "task-scheduler": {
      "command": "/absolute/path/to/chatgpt_task/scaffold/.venv/bin/python3",
      "args": ["-m", "app.mcp_server"],
      "cwd": "/absolute/path/to/chatgpt_task/scaffold"
    }
  }
}
```

Example (replace with your clone path):

```json
{
  "mcpServers": {
    "task-scheduler": {
      "command": "/Users/chenkewei/Desktop/github/build-moat-live-sessions/chatgpt_task/scaffold/.venv/bin/python3",
      "args": ["-m", "app.mcp_server"],
      "cwd": "/Users/chenkewei/Desktop/github/build-moat-live-sessions/chatgpt_task/scaffold"
    }
  }
}
```

1. Run `uv sync` in `scaffold/` and add API keys in `chatgpt_task/.env` (see above).
2. **Quit and restart Claude Desktop** fully (not just the chat window).
3. In chat, open the **tools** (hammer) menu — you should see `task_create`, `task_list`, `task_status`, `task_cancel`, and `task_execute`.

### Add and test jobs in chat

Claude maps natural language to MCP tools. Examples:

**Schedule a job**

> Add a job tomorrow morning 9:00 am: write me a joke

Claude calls **`task_create`** and returns something like `job_id: 3`, `status: pending`.

**Run a job immediately**

> Execute job 3

Claude calls **`task_execute`**, which runs the description through the LLM and saves the result. Example reply:

> Great! Job 3 has been executed successfully! Here's the result:
>
> **Job ID:** 3  
> **Status:** completed  
> **Result:**
>
> Why don't scientists trust atoms?  
> Because they make up everything!
>
> Your joke is ready!

**Check status later**

> What's the status of job 3?

Claude calls **`task_status`** and returns `status` and `result` from the database (including after the background worker runs at `scheduled_at`).

| You say (examples) | MCP tool | What happens |
|--------------------|----------|----------------|
| Schedule … tomorrow 9am … | `task_create` | Job saved as `pending` |
| Execute job 3 | `task_execute` | LLM runs now; `result` saved |
| List my jobs | `task_list` | All jobs (no `result` in list) |
| Status of job 3 | `task_status` | Full row including `result` |
| Cancel job 3 | `task_cancel` | Sets `cancelled` |

Scheduled jobs also run automatically: the watcher queues due jobs and the worker calls the LLM without you typing “execute.” Use **`task_execute`** when you want to run a job **now** without waiting for `scheduled_at`.

## Bonus Challenges

- Connect a real LLM to parse natural language task descriptions before calling `task_create`
- Add recurring job support (cron expressions)
- Add job chaining (Job A completes -> triggers Job B)
- Add MCP `resources` support (e.g., expose job details as readable resources)
- Add MCP `prompts` support (e.g., a `daily_review` prompt template)
