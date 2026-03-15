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


# TOOL 1: Organize Folder
def organize_folder(folder_path: str):
    """
    Scans a folder and automatically sorts files
    into categorized subfolders based on file type.
    Returns {"status": "success", "moves": list of (old_path, new_path)}
    """
    path = Path(folder_path)

    if not path.exists():
        return {"status": "error", "message": f"Folder not found: {folder_path}"}

    if path == Path("/"):
        return {"status": "error", "message": "Refusing to organize root directory."}
    
    moved_files = 0
    moves = []

    for file in path.iterdir():
        if file.is_file():
            ext = file.suffix.lower().replace(".", "")
            if not ext:
                ext = "other"

            target_dir = path / ext
            target_dir.mkdir(exist_ok=True)

            old_path = str(file)
            new_path = str(target_dir / file.name)
            
            shutil.move(old_path, new_path)
            moves.append((old_path, new_path))
            moved_files += 1

    return {"status": "success", "moves": moves}


# TOOL 2: Summarize File
def summarize_file(file_path: str):
    """
    Summarizes the content of a file based on its extension.
    Supports PDF, TXT, and various code/text-based formats.
    """
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
    pdf.multi_cell(0, 10, summary)
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
    Moves a file or folder from a source path to a destination path.
    """
    try:
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
    sort_by: 'created' or 'modified'.
    reverse: True for descending order, False for ascending.
    file_extension: Optional filter for file extension (e.g., '.txt').
    """
    try:
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


# TOOL 5: Start Folder Monitor (existing)
def start_folder_monitor(folder_path: str, actions: list):
    """
    Monitors a folder for new files and performs actions on them.
    Currently supports indexing PDF files.
    """
    class IndexHandler(FileSystemEventHandler):
        def on_created(self, event):
            if not event.is_directory and event.src_path.endswith('.pdf'):
                index_file(event.src_path)

    def index_file(file):
        if file.endswith(".pdf"):
            text = extract_pdf(file)
            chunks = chunk_text(text)
            for i, chunk in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                metadata = {"file_path": os.path.abspath(file)}
                add_chunk(chunk_id, chunk, metadata)

    path = Path(folder_path)
    if not path.exists():
        return f"Folder not found: {folder_path}"
    
    event_handler = IndexHandler()
    observer = Observer()
    observer.schedule(event_handler, str(path), recursive=True)
    observer.start()
    
    def run_observer():
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    
    thread = threading.Thread(target=run_observer, daemon=True)
    thread.start()
    return f"Started monitoring {folder_path} for new PDFs."


# TOOL REGISTRY
# This dictionary maps tool names to their corresponding functions.
TOOL_REGISTRY = {
    "organize_folder": organize_folder,
    "summarize_file": summarize_file,
    "move_file": move_file,
    "list_files_by_date": list_files_by_date,
    "start_folder_monitor": start_folder_monitor,
    "time_travel_search": time_travel_search,
    "explain_folder": explain_folder,
    "edit_file_nl": edit_file_nl,
    "work_history_summary": work_history_summary,
    "proactive_suggestions": proactive_suggestions,
    "explain_computer": explain_computer,
    "generate_file_graph": generate_file_graph,
}
