### Warden Manual Test Plan (Hackathon)

Run these from the repo root unless noted.

---
### 1. Basic CLI / Agent

- **Global CLI (after `pip install -e .`)**
  - `warden "organize my desktop"  --dry-run`
  - `warden --yes "organize my desktop"`
  - `warden "what did I work on today?"`

- **Local main.py**
  - `python main.py` → interactive REPL.
  - Inside REPL:
    - `organize the folder with the machine learning power points`
    - `summarize the ML lecture notes`
    - `what did I just summarize?`

---
### 2. Tools (create this test folder)

On your Desktop create a folder `WardenTest` with:

- `WardenTest/ML Slides/lecture1_powerpoint.pdf` (any PDF, name is what matters)
- `WardenTest/ML Slides/lecture2_powerpoint.pdf`
- `WardenTest/Resumes/resume_v1.docx`
- `WardenTest/Random/notes.txt`

Then run:

- **Organize**
  - `warden --yes "organize the folder with the machine learning power points"`
  - Expect: files regrouped into semantic subfolders under `WardenTest`.

- **Summarize**
  - `warden "summarize the ML lecture notes"`
  - Expect: summary text + a PDF path in `summaries/`.

- **List by date**
  - `warden "list files by date in the folder with ML slides"`

- **Move file (semantic)**
  - `warden --yes "move my resume to the folder with the machine learning power points"`

---
### 3. Memory / Timeline

- After running summarize + organize:
  - `warden "what did I just summarize?"`
  - `warden "what have I been doing for the last 1 days?"`
  - `warden "show me the file timeline for today"`

---
### 4. Dry Run Demo

- `warden --dry-run "monitor downloads and move PDFs to my lab4 721 folder"`
- `warden --dry-run "explain my computer"`

These should print the **plan** and **actions** but make **no changes**.

