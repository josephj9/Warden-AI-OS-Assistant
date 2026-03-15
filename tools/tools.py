import os
import shutil
import json
from tools.llm import genResponse, summerize
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from tools.extract import extract_pdf, chunk_text, extract_text, extract_docx
from pathlib import Path
import uuid
import threading
from collections import defaultdict, Counter
from typing import Dict, List
from memory import file_memory
from tools.advanced_tools import (
    time_travel_search,
    explain_folder,
    edit_file_nl,
    work_history_summary,
    proactive_suggestions,
    explain_computer,
    generate_file_graph
)
from fpdf import FPDF
from tools.utils import resolve_path, resolve_path_semantic
try:
    from vector.moorcheh import add_chunk
except ImportError:
    def add_chunk(*args, **kwargs): pass  # fallback no-op


# TOOL 1: Organize Folder (AI-Semantic)
def organize_folder(folder_path: str):
    """
    Scans a folder and uses AI to intelligently sort files
    into semantically meaningful subfolders based on content and name.
    folder_path can be a path, a folder name, or a semantic description
    (e.g. "the folder with the machine learning power points").
    Returns a human-readable summary of what was organized.
    """
    resolved = resolve_path(folder_path)
    path = Path(resolved)
    if not path.exists():
        semantic = resolve_path_semantic(folder_path, prefer_folder=True)
        if semantic:
            path = Path(semantic)
        else:
            return {"status": "error", "message": f"I couldn't find the folder '{folder_path}'. Please check the name or try describing it (e.g. 'folder with ML slides')."}

    if path == Path("/"):
        return {"status": "error", "message": "For safety, I won't organize the root directory."}

    # Gather all files
    files_in_folder = [f for f in path.iterdir() if f.is_file()]

    if not files_in_folder:
        return {"status": "success", "message": f"The folder '{path.name}' is already empty, nothing to organize!"}

    # Build a list of filenames for the LLM
    file_names_str = "\n".join(f"- {f.name}" for f in files_in_folder)

    # Ask the LLM to semantically group these files
    prompt = f"""
    You are a smart file organizer. Below is a list of files in a folder called "{path.name}".
    Your job is to group these files into logical, meaningful category names (e.g. "Resumes", "Python Scripts", "PDFs", "Images", "Study Notes").
    Do NOT use generic names like "other", "misc", or file extensions as folder names.
    
    Files:
    {file_names_str}
    
    Respond ONLY in JSON format:
    {{
        "categories": {{
            "Category Name": ["filename1.ext", "filename2.ext"],
            "Another Category": ["filename3.ext"]
        }}
    }}
    """

    try:
        ai_response = genResponse(prompt)
        categories = ai_response.get("categories", {})
    except Exception:
        # Fallback: group by extension if LLM fails
        categories = defaultdict(list)
        for f in files_in_folder:
            ext = f.suffix.lower().lstrip(".") or "other"
            categories[ext].append(f.name)

    moves = []
    errors = []

    for category_name, filenames in categories.items():
        # Sanitize folder name: remove invalid path chars
        safe_category = "".join(c for c in category_name if c not in r'\/:*?"<>|').strip()
        if not safe_category:
            safe_category = "Other"

        target_dir = path / safe_category
        target_dir.mkdir(exist_ok=True)

        for filename in filenames:
            source = path / filename
            if not source.exists():
                continue
            destination = target_dir / filename
            try:
                shutil.move(str(source), str(destination))
                moves.append((str(source), str(destination), safe_category))
            except Exception as e:
                errors.append(f"Could not move '{filename}': {e}")

    # Build a readable summary
    if not moves:
        summary_msg = f"No files were moved in '{path.name}'. Everything may already be organized."
    else:
        category_counts = defaultdict(int)
        for _, _, cat in moves:
            category_counts[cat] += 1
        summary_lines = [f"✅ Organized {len(moves)} file(s) in '{path.name}' into {len(category_counts)} folder(s):"]
        for cat, count in category_counts.items():
            summary_lines.append(f"   📁 {cat}: {count} file(s)")
        if errors:
            summary_lines.append(f"⚠️ {len(errors)} file(s) had issues: {'; '.join(errors[:3])}")
        summary_msg = "\n".join(summary_lines)

    return {"status": "success", "message": summary_msg, "moves": [(m[0], m[1]) for m in moves]}


# TOOL 2: Summarize File
def summarize_file(file_path: str):
    """
    Summarizes the content of a file based on its extension.
    file_path can be a path, filename, or semantic description (e.g. "the ML lecture notes").
    Supports PDF, TXT, and various code/text-based formats.
    """
    resolved = resolve_path(file_path)
    if not os.path.exists(resolved):
        semantic = resolve_path_semantic(file_path, prefer_folder=False)
        if semantic:
            resolved = semantic
    file_path = resolved
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"File not found: {file_path}"}

    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    content = ""
    try:
        if extension == ".pdf":
            content = extract_pdf(file_path)
        elif extension == ".docx":
            content = extract_docx(file_path)
        elif extension in [".txt", ".py", ".js", ".html", ".css", ".md", ".csv"]:
            content = extract_text(file_path)
        else:
            return {"status": "error", "message": f"Unsupported file type: {extension}"}

        if not content.strip():
             return {"status": "error", "message": "No content extracted from file."}

    except Exception as e:
        return {"status": "error", "message": f"Error extracting content: {str(e)}"}

    chunks = chunk_text(content)
    summary = summerize(chunks)
    
    # Create PDF summary
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    # FPDF only supports latin-1, so replace unsupported characters
    safe_summary = summary.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, safe_summary)
    pdf_filename = f"summaries/summary_{os.path.basename(file_path)}.pdf"
    pdf.output(pdf_filename)
    
    # Record file access in memory
    try:
        file_memory.record_access(
            file_path=file_path,
            user_task="file_summarization",
            context="User requested summary",
            summary=summary[:200] if isinstance(summary, str) else str(summary)[:200]
        )
    except Exception as e:
        print(f"Warning: Could not record file access: {e}")

    return {"status": "success", "summary": summary, "pdf_path": pdf_filename}

# TOOL 3: Move File
def move_file(source_path: str, destination_path: str):
    """
    Moves a file or folder from source to destination.
    Both paths can be exact paths or semantic descriptions (e.g. "my resume", "Desktop").
    """
    try:
        src = resolve_path(source_path)
        if not os.path.exists(src):
            semantic_src = resolve_path_semantic(source_path, prefer_folder=False)
            if semantic_src:
                src = semantic_src
        source_path = src
        dest = resolve_path(destination_path)
        if not os.path.isdir(dest) and not os.path.isfile(dest):
            semantic_dest = resolve_path_semantic(destination_path, prefer_folder=True)
            if semantic_dest:
                dest = semantic_dest
        destination_path = dest

        if not os.path.exists(source_path):
            return {"status": "error", "message": f"Source path not found: {source_path}"}
        
        # If destination is a folder, move the file inside it
        if os.path.isdir(destination_path):
            dest_file_path = os.path.join(destination_path, os.path.basename(source_path))
        else:
            dest_file_path = destination_path

        shutil.move(source_path, dest_file_path)
        return {"status": "success", "message": f"Moved {source_path} to {dest_file_path}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# TOOL 4: List Files by Date
def list_files_by_date(folder_path: str, sort_by: str = 'created', reverse: bool = False, file_extension: str = None):
    """
    Lists files in a directory sorted by date.
    folder_path can be a path, folder name, or semantic description.
    sort_by: 'created' or 'modified'.
    reverse: True for descending order, False for ascending.
    file_extension: Optional filter for file extension (e.g., '.txt').
    """
    try:
        resolved = resolve_path(folder_path)
        if not os.path.isdir(resolved):
            semantic = resolve_path_semantic(folder_path, prefer_folder=True)
            if semantic:
                resolved = semantic
        folder_path = resolved
        if not os.path.isdir(folder_path):
            return {"status": "error", "message": f"Folder not found: {folder_path}"}

        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

        if file_extension:
            files = [f for f in files if f.lower().endswith(file_extension.lower())]

        if sort_by == 'created':
            key = os.path.getctime
        elif sort_by == 'modified':
            key = os.path.getmtime
        else:
            return {"status": "error", "message": "Invalid sort_by value. Use 'created' or 'modified'."}

        sorted_files = sorted(files, key=key, reverse=reverse)
        
        file_list = []
        for f in sorted_files:
            stat = os.stat(f)
            file_list.append({
                "path": f,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "size_bytes": stat.st_size
            })

        return {"status": "success", "files": file_list}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# TOOL 5: Start Folder Monitor
def start_folder_monitor(folder_path: str, move_to: str = None, actions: list = None):
    """
    Monitors a folder for new files and automatically:
    - Indexes new PDFs into the vector search database
    - Moves new PDFs to move_to folder (or pdf_destination preference if set)
    folder_path and move_to can be paths, short names, or semantic descriptions.
    """
    from pathlib import Path as _Path

    resolved_folder = resolve_path(folder_path)
    if not os.path.isdir(resolved_folder):
        semantic = resolve_path_semantic(folder_path, prefer_folder=True)
        if semantic:
            resolved_folder = semantic
    if not os.path.isdir(resolved_folder):
        return {"status": "error", "message": f"Folder to monitor not found: {folder_path}"}

    # Resolve the destination: explicit arg > stored preference
    destination = None
    if move_to:
        destination = resolve_path(move_to)
        if not os.path.isdir(destination):
            semantic_dest = resolve_path_semantic(move_to, prefer_folder=True)
            if semantic_dest:
                destination = semantic_dest
    else:
        pref = file_memory.get_preference("pdf_destination")
        if pref:
            destination = resolve_path(pref)

    if destination and not os.path.isdir(destination):
        return {"status": "error", "message": f"Destination folder not found: {destination}"}

    def _wait_for_file_ready(path: str, timeout: float = 60.0, stable_time: float = 1.0, stable_checks: int = 2) -> bool:
        """Wait until a file is fully written, stable in size, and can be opened for read."""
        start = time.time()
        last_size = -1
        stable_count = 0

        while time.time() - start < timeout:
            if not os.path.exists(path):
                time.sleep(0.5)
                stable_count = 0
                continue

            # Skip temporary download file extensions while browser is still downloading
            _, ext = os.path.splitext(path)
            if ext.lower() in {".crdownload", ".part", ".tmp", ".temp"}:
                time.sleep(0.5)
                stable_count = 0
                continue

            try:
                size = os.path.getsize(path)
            except OSError:
                time.sleep(0.5)
                stable_count = 0
                continue

            # Check that we can open the file for reading (not locked)
            try:
                with open(path, "rb") as f:
                    f.read(1)
            except Exception:
                time.sleep(0.5)
                stable_count = 0
                continue

            if size == last_size and size > 0:
                stable_count += 1
                if stable_count >= stable_checks:
                    return True
            else:
                stable_count = 0

            last_size = size
            time.sleep(stable_time)

        return False

    def index_and_move(file_path: str):
        """Index a new PDF and move it to the destination if configured."""
        try:
            # Some browsers download to a temp extension (e.g. .crdownload, .part) then rename.
            # If we see a temp file, wait for the final PDF to appear.
            temp_exts = {".crdownload", ".part", ".tmp"}
            orig_path = file_path
            _, ext = os.path.splitext(file_path)
            if ext.lower() in temp_exts:
                file_path = file_path[: -len(ext)]

            # If the final file isn't a PDF, ignore it.
            if not file_path.lower().endswith(".pdf"):
                return

            # Wait until the file is fully downloaded / stable before processing.
            if not _wait_for_file_ready(file_path):
                return

            # Give the system a short buffer to finalize file handles (e.g., installer finish).
            time.sleep(5)

            if not os.path.exists(file_path):
                return

            # Try to extract PDF text, retrying briefly if the file is still being finalized.
            text = None
            for attempt in range(3):
                try:
                    text = extract_pdf(file_path)
                    break
                except Exception:
                    time.sleep(0.5)

            if text:
                chunks = chunk_text(text)
                for chunk in chunks:
                    add_chunk(str(uuid.uuid4()), chunk, {"file_path": os.path.abspath(file_path)})

            if destination:
                dest_file = os.path.join(destination, os.path.basename(file_path))
                # Generate unique name if exists to prevent overwrite errors
                base, ext = os.path.splitext(dest_file)
                counter = 1
                while os.path.exists(dest_file):
                    dest_file = f"{base} ({counter}){ext}"
                    counter += 1

                # Copy first (to avoid losing the source if move happens too early)
                try:
                    shutil.copy2(file_path, dest_file)

                    # Verify the copied file looks valid
                    if os.path.getsize(dest_file) == os.path.getsize(file_path):
                        try:
                            with open(dest_file, "rb") as f:
                                f.read(1)
                            os.remove(file_path)
                        except Exception:
                            # Keep the original if destination is still locked / invalid
                            pass
                    else:
                        # If sizes diverge, keep the original and retry later
                        pass
                except Exception:
                    # If copy fails, leave original in place and try later
                    pass
        except Exception:
            pass  # Silent fail per file — don't crash the monitor thread

    class IndexHandler(FileSystemEventHandler):
        def on_created(self, event):
            if not event.is_directory:
                # Run in a separate thread so time.sleep doesn't block the observer
                threading.Thread(target=index_and_move, args=(event.src_path,), daemon=True).start()

        def on_moved(self, event):
            if not event.is_directory:
                threading.Thread(target=index_and_move, args=(event.dest_path,), daemon=True).start()

    event_handler = IndexHandler()
    observer = Observer()
    observer.schedule(event_handler, resolved_folder, recursive=False)
    observer.start()

    def run_observer():
        try:
            while True:
                import time as _time
                _time.sleep(1)
        except Exception:
            observer.stop()
        observer.join()

    threading.Thread(target=run_observer, daemon=True).start()

    dest_msg = f" New files will be moved to: **{os.path.basename(destination or '')}**" if destination else ""
    return {
        "status": "success",
        "message": f"👁️ Now monitoring **{os.path.basename(resolved_folder)}** for new files.{dest_msg}"
    }

# TOOL 13: Set User Preference

def set_user_preference(category: str, preference: str):
    """
    Stores a persistent user preference in memory.
    Supported Categories:
    - 'pdf_destination': Folder to automatically move PDFs to when monitored.
    - 'general': Any general text memory the agent should remember.
    """
    try:
        file_memory.set_preference(category, preference)
        return {"status": "success", "message": f"Successfully remembered preference: {category} -> {preference}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to save preference: {str(e)}"}

# TOOL REGISTRY
# This dictionary maps tool names to their corresponding functions.
TOOL_REGISTRY = {
    "organize_folder": organize_folder,
    "summarize_file": summarize_file,
    "move_file": move_file,
    "list_files_by_date": list_files_by_date,
    "start_folder_monitor": start_folder_monitor,
    "set_user_preference": set_user_preference,
    "time_travel_search": time_travel_search,
    "explain_folder": explain_folder,
    "edit_file_nl": edit_file_nl,
    "work_history_summary": work_history_summary,
    "proactive_suggestions": proactive_suggestions,
    "explain_computer": explain_computer,
    "generate_file_graph": generate_file_graph,
}
