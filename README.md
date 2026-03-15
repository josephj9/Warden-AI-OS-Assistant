Warden 🛡️
AI-powered file system assistant for your real computer — ask in plain English, and Warden semantically finds, summarizes, organizes, and tracks your files. Backed by Moorcheh for vector search, with local Chroma fallback.

Python 3.12 · CLI · Moorcheh + Chroma · Rich TUI · Windows-first

What is Warden?
Warden is a terminal-based AI assistant that understands your actual filesystem.

You type:

warden "organize the folder with the machine learning power points"

Warden:

Uses Moorcheh semantic search to figure out which folder you mean
Groups files into intelligent categories (e.g. “Slides”, “Readings”, “Code”, “Assignments”)
Actually moves the files on disk
Records everything into a time-travel memory so later you can ask:
“what did I work on yesterday?”
“what did I just summarize?”
“show me my file timeline for today”
Your natural language → Moorcheh semantic search + system tools → real file operations.

Why Moorcheh?
Moorcheh is the central brain of Warden.

All file access events (summaries, edits, moves, monitors) are recorded as small text “memories”
Each memory is embedded & stored in Moorcheh via add_chunk(...)
When you ask questions like:
“what PDF did I read before my ML midterm?”
“where is that discrete math cheat sheet I summarized?”
Warden calls query_chunks(...) on Moorcheh, and if Moorcheh is unavailable, it automatically falls back to local Chroma.
Moorcheh gives Warden:

Semantic recall over your file history (not just filenames)
Robust cross-session memory (it works even after restarts)
A clean separation: Moorcheh = memory layer, Warden = agent + tools

# Organize semantically, no hard paths
warden --yes "organize the folder with the machine learning power points"

# Summarize a file by description
warden "summarize the ML lecture notes"

# Time-travel memory
warden "what did I just summarize?"
warden "what did I work on today?"

Behind the scenes:

Desktop / Documents / Downloads are indexed once into Chroma
Moorcheh stores behavioral memories (what you touched, when, why)
Natural language is turned into concrete tool calls by the agent

Core Capabilities
Plain English → File actions

Semantic organize
organize_folder(folder_path) accepts descriptions:

“organize my lab4721 folder”
“organize the folder with ML powerpoints”
AI groups files into meaningful subfolders (no “misc”, no extension-only folders).

Smart summarize
summarize_file(file_path) works with:

PDF, DOCX, TXT, code files
Path, filename, or description:
“summarize the ML lecture notes”
Creates a PDF summary and stores a memory in Moorcheh.
Semantic move
move_file(source, destination) understands:

“move my resume to the folder with the machine learning power points”
Both source_path and destination_path can be semantic.
Timeline + history (Moorcheh-powered)

time_travel_search(query) — “what PDF did I read before my ML midterm?”
file_timeline(days=1, date=...) — pretty chronological view of file activity
work_history_summary(days=7) — “what did I work on this week?”
Explain & map your disk

explain_folder(folder) — high-level analysis of a folder (types, counts, suggestions)
generate_file_graph(folder) — semantic clusters of related files
explain_computer() — overview of major topics & projects on your machine
Natural language editing

edit_file_nl(file, instruction):
“shorten my resume to one page”
“remove all comments from this script”
Live monitoring

start_folder_monitor(folder, move_to=...):
Indexes new PDFs into Moorcheh/Chroma
Moves them to your preferred folder
Works with semantic paths:
“monitor downloads and move PDFs to my lab4 721 folder”

How Warden Uses Moorcheh
Architecture (simplified):

Plain English prompt
  +
Filesystem (paths, names, content)
  │
  ▼
LLM Agent Planner (JSON tool plan)
  │
  ├── Tools (organize_folder, summarize_file, edit_file_nl, …)
  │ └── FileMemory.record_access(...) → Moorcheh.add_chunk(...)
  │
  └── Advanced tools (time_travel_search, file_timeline, work_history_summary)
   └── Moorcheh.query_chunks(...) → contextual file history

Key decisions:

Moorcheh as primary vector store
memory.py uses vector.moorcheh.add_chunk / query_chunks. If Moorcheh is down or fails:

It falls back to local Chroma (vector.chroma) so the tool still works.
Moorcheh stores why a file matters
Each memory includes:

file_path, file_name, timestamp
user_task (e.g. summarize_file — discrete_math1.pdf)
context and summary snippet
This makes semantic questions about your work possible.
Chroma as a coarse index for filesystem search
vector/indexer.py indexes filenames + paths into Chroma;
vector/search.hybrid_search(...) combines:

semantic search via Chroma
keyword search over paths This powers resolve_path_semantic(...) which turns:
“folder with ML slides” → a concrete folder path.

Tech Stack
Layer	Technology
Agent + CLI	Python 3.12
Memory backend	Moorcheh SDK (primary) + Chroma (fallback)
Vector embedding	SentenceTransformers (all-MiniLM-L6-v2)
Terminal UI	Rich (panels, rules, Markdown)
File watching	watchdog
PDF / DOCX parsing	pdfplumber, pdfminer.six, python-docx
LLM calls	tools.llm (OpenAI/Google-compatible wrapper)
CLI install	setuptools console_scripts (warden)

Installation
Prerequisites

Python 3.12 on Windows (tested)
Pip available (python -m pip --version)
Moorcheh API key set as MOORCHEH_API_KEY in your environment or .env
From c:\Users\Balantech\Desktop\Agent:

# Install dependencies + global `warden` CLI
python -m pip install -e .

This:

Installs everything from requirements.txt
Registers the warden command pointing at warden_cli:main


Usage
Global CLI (recommended)
From any directory:

# Semantic organize
warden --yes "organize my lab4721 folder"

# Summarize by description
warden "summarize the ML lecture notes"

# Time-travel queries
warden "what did I just summarize?"
warden "what did I work on today?"

# Dry run (hackathon demo safe)
warden --dry-run "monitor downloads and move PDFs to my lab4 721 folder"
warden --dry-run "explain my computer"

Flags:

--yes / -y — auto-confirm, skip the plan prompt.
--dry-run — print plan + actions, no filesystem changes (powered by run_agent(..., dry_run=True)).


Local interactive mode
cd c:\YOUR\FILE\PATH
python main.py

On first run:

Warden indexes Desktop, Documents, Downloads into Chroma.
It writes index_state.json so this heavy step never repeats.

Prompt:

Ask the agent:
> organize the folder with the machine learning power points
> summarize the ML lecture notes
> what did I just summarize?

Testing & Sample Folders
See TESTING.md for a step-by-step manual test plan.

Quick version:

On your Desktop, create:

Desktop/WardenTest/ML Slides/lecture1_powerpoint.pdf
Desktop/WardenTest/ML Slides/lecture2_powerpoint.pdf
Desktop/WardenTest/Resumes/resume_v1.docx
Desktop/WardenTest/Random/notes.txt

You’ll exercise:

Semantic path resolution
Organize / summarize / move
Moorcheh-backed file memory and timeline
How the Agent Works (high level)
Context building

Conversational history (conversation_history.json)
File memory (file_memory.json + Moorcheh)
Filesystem hints via resolve_path + resolve_path_semantic
Planning

agent.run_agent(...) prompts the LLM to return JSON:
{"plan": "...", "actions": [{"tool": "...", "args": {...}}, ...]}
Dry-run or execution

If --dry-run or WARDEN_DRY_RUN=1:
Warden prints the plan + actions only.
Otherwise:
Shows the plan in a Rich table
Asks for confirmation (skipped if --yes)
Executes tools via execute_tool(...)
Memory logging (Moorcheh)

Tools like summarize_file, organize_folder, edit_file_nl, etc. call:
file_memory.record_access(...)
Which:
Appends to file_memory.json
Pushes a chunk to Moorcheh with searchable text + metadata
Recall

time_travel_search and file_timeline call file_memory.search_by_context(...)
This uses Moorcheh.query_chunks(...) (or Chroma fallback) to find relevant past events.

Agent/
├── agent/
│   └── agent.py            # LLM agent, tool registry, planner, dry-run
├── tools/
│   ├── tools.py            # Core tools: organize, summarize, move, monitor, prefs
│   ├── advanced_tools.py   # Time-travel search, explain_folder, file_timeline, etc.
│   ├── utils.py            # resolve_path + resolve_path_semantic (Moorcheh/Chroma)
│   └── llm.py              # LLM wrapper
├── vector/
│   ├── moorcheh.py         # Moorcheh client: add_chunk, query_chunks
│   ├── chroma.py           # Local Chroma store and embedding
│   ├── indexer.py          # One-time filesystem indexing into Chroma
│   └── search.py           # hybrid_search (semantic + keyword)
├── memory.py               # FileMemory: logs file access + Moorcheh integration
├── conversation_memory.py  # Persistent conversational history
├── main.py                 # Interactive REPL + initial indexing (once)
├── warden_cli.py           # Global CLI entrypoint (`warden`)
├── setup.py                # setuptools config, console_scripts, requirements wiring
├── requirements.txt
├── TESTING.md              # Manual test plan
└── file_memory.json / conversation_history.json / index_state.json
