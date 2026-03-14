import os
import shutil
from pathlib import Path
from tools.llm import genResponse, summerize
from vector.chroma import query_chunks
from vector.search import hybrid_search
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import uuid
from tools.extract import extract_pdf, chunk_text
from vector.chroma import add_chunk

# -----------------------------
# TOOL 1: Organize Folder
# -----------------------------

def organize_folder(folder_path: str) -> dict:
    """
    Scans a folder and automatically sorts files
    into categorized subfolders based on file type.
    Returns {"message": str, "moves": list of (old_path, new_path)}
    """
    path = Path(folder_path)

    if not path.exists():
        return {"message": f"Folder not found: {folder_path}", "moves": []}

    if path == Path("/"):
        return {"message": "Refusing to organize root directory.", "moves": []}
    
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

    return {"message": f"Organized {moved_files} files in {folder_path}", "moves": moves}


# -----------------------------
# TOOL 2: Summarize File
# -----------------------------

def summarize_file(file_path: str) -> str:
    """
    Extracts text from a file and returns a concise summary.
    """
    path = Path(file_path)

    if not path.exists():
        return f"File not found: {file_path}"

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        if not content.strip():
            return f"No readable content in {file_path}"

        prompt = f"""
        Summarize the following document concisely:

        {content[:5000]}
        """

        summary = summerize(prompt)

        if isinstance(summary, dict) and "error" in summary:
            return summary["error"]

        return f"Summary of {file_path}:\n{summary}"

    except Exception as e:
        return f"Failed to summarize {file_path}: {str(e)}"
    



def semantic_search(query):

    return hybrid_search(query)

def index_file(file):
    if file.endswith(".pdf"):
        text = extract_pdf(file)
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            metadata = {"file_path": os.path.abspath(file)}
            add_chunk(chunk_id, chunk, metadata)

class IndexHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.pdf'):
            index_file(event.src_path)

def start_folder_monitor(folder_path: str) -> str:
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
                pass
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    
    thread = threading.Thread(target=run_observer, daemon=True)
    thread.start()
    return f"Started monitoring {folder_path} for new PDFs."

# -----------------------------
# TOOL REGISTRY
# -----------------------------

TOOL_REGISTRY = {
    "semantic_search": semantic_search,
    "organize_folder": organize_folder,
    "summarize_file": summarize_file,
    "start_folder_monitor": start_folder_monitor
}