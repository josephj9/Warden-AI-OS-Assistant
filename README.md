# Warden 🛡️

AI-powered **filesystem assistant for your real computer**.

Ask in plain English — Warden **semantically finds, summarizes, organizes, and tracks your files.**

Powered by **Moorcheh semantic memory** with **Chroma fallback**.

---

## 🚀 Demo

```bash
# organize files semantically
warden --yes "organize the folder with the machine learning power points"

# summarize by description
warden "summarize the ML lecture notes"

# time-travel memory
warden "what did I just summarize?"
warden "what did I work on today?"
```

---

# What is Warden?

Warden is a **terminal-based AI assistant that understands your actual filesystem**.

Instead of navigating directories manually:

```
cd Desktop
cd Documents
cd lab4721
```

You simply type:

```
warden "organize the folder with the machine learning power points"
```

Warden will:

1. Use **semantic search** to locate the folder
2. Analyze the files
3. Group them into meaningful categories
4. Move the files on disk
5. Record the activity into long-term memory

Later you can ask:

```
warden "what did I work on yesterday?"
warden "what did I just summarize?"
warden "show me the file timeline for today"
```

---

# 🧠 Why Moorcheh?

Warden uses **Moorcheh as its memory layer**.

Every file interaction becomes a searchable memory.

Example memory chunk:

```
User summarized discrete_math1.pdf before ML midterm
Timestamp: 2026-03-14
Task: summarize_file
```

These memories are embedded and stored in Moorcheh.

When you ask:

```
warden "what PDF did I read before my ML midterm?"
```

Warden performs a **semantic memory search**.

If Moorcheh is unavailable, Warden **automatically falls back to Chroma locally.**

---

# Core Capabilities

## Plain English → File Actions

### Semantic Organize

```
warden "organize my lab4721 folder"
```

Warden groups files into categories like:

```
Slides/
Assignments/
Code/
Readings/
```

---

### Smart Summarization

```
warden "summarize the ML lecture notes"
```

Works with:

- PDFs
- DOCX
- TXT
- code files

Creates a **PDF summary** and records the memory.

---

### Semantic Move

```
warden "move my resume to the folder with the machine learning power points"
```

Both paths can be **natural language descriptions**.

---

### Time-Travel Memory

Ask questions about past work:

```
warden "what did I work on today?"
warden "what did I summarize yesterday?"
warden "what PDF did I read before my ML midterm?"
```

Powered by **Moorcheh vector search**.

---

### Explain Your Disk

```
warden "explain my computer"
```

Warden analyzes your filesystem and reports:

- major topics
- projects
- file clusters

---

### Live Folder Monitoring

```
warden "monitor downloads and move PDFs to my lab4721 folder"
```

New files are automatically:

- indexed
- moved
- recorded into memory

---

# Architecture

```
User Prompt
     │
     ▼
LLM Agent Planner
     │
     ▼
Tool Execution Layer
     │
 ┌───────────────┬───────────────┐
 ▼               ▼               ▼
Filesystem      Moorcheh        Chroma
Operations      Memory          Vector Index
```

---

# Tech Stack

| Layer | Technology |
|------|------|
| Agent + CLI | Python 3.12 |
| Memory Backend | Moorcheh |
| Local Vector Store | Chroma |
| Embeddings | SentenceTransformers |
| Terminal UI | Rich |
| File Monitoring | watchdog |
| PDF Parsing | pdfplumber |

---

# Installation

### Requirements

- Python 3.12
- pip
- Moorcheh API key

---

### Install

From the project directory:

```bash
python -m pip install -e .
```

This registers the **global CLI command**:

```
warden
```

---

# Usage

From **any directory**:

```bash
warden "organize my lab4721 folder"

warden "summarize the ML lecture notes"

warden "what did I just summarize?"
```

---

### Dry Run Mode

For safe testing:

```bash
warden --dry-run "organize my downloads"
```

Shows the plan **without modifying files**.

---

# Example Test Folder

Create this structure:

```
Desktop/WardenTest/
├── ML Slides/
│   ├── lecture1_powerpoint.pdf
│   └── lecture2_powerpoint.pdf
├── Resumes/
│   └── resume_v1.docx
└── Random/
    └── notes.txt
```

Run:

```
warden --yes "organize the folder with the machine learning power points"
```

---

# Project Structure

```
Agent/
├── agent/
│   └── agent.py
│
├── tools/
│   ├── tools.py
│   ├── advanced_tools.py
│   └── utils.py
│
├── vector/
│   ├── moorcheh.py
│   ├── chroma.py
│   ├── indexer.py
│   └── search.py
│
├── memory.py
├── conversation_memory.py
├── main.py
├── warden_cli.py
├── setup.py
├── requirements.txt
└── README.md
```

---

# Future Improvements

- GUI launcher (Spotlight-style)
- multi-user memory graphs
- automatic project detection
- codebase understanding

---

# License

MIT License

---
