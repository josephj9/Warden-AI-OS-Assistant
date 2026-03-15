import os
from pathlib import Path
from typing import Optional


def resolve_path_semantic(description: str, prefer_folder: bool = True) -> Optional[str]:
    """
    Resolve a folder or file by semantic description using vector search.
    E.g. "machine learning power points" -> path to folder containing matching files.
    If prefer_folder is True (default), returns the folder containing the best match;
    otherwise returns the best matching file path.
    """
    try:
        from vector.search import hybrid_search
        paths = hybrid_search(description)
        if not paths:
            return None
        first = paths[0]
        if isinstance(first, dict):
            first = first.get("file_path") or first.get("path") or str(first)
        first = str(first).strip()
        if not first or not os.path.exists(first):
            return None
        if os.path.isdir(first):
            return first
        # It's a file; return its directory if we want a folder
        return os.path.dirname(first) if prefer_folder else first
    except Exception:
        return None


def resolve_path(path_str: str) -> str:
    """
    Intelligently resolves a user-provided file or folder name by searching
    across common user directories if it does not exist at the exact provided path.

    Fallback Search Order:
    1. Direct Path as provided
    2. Desktop
    3. Downloads
    4. Documents
    5. Home directory
    """
    # 1. Check if the path exists exactly as provided (absolute or relative to current dir)
    initial_path = Path(path_str).expanduser().resolve()
    if initial_path.exists():
        return str(initial_path)

    # If it's just a name or relative path that doesn't exist, search common directories
    target_name = os.path.basename(path_str) # To handle generic inputs like "html/test2.py" or "helloword"
    
    # We will mainly search by the provided path_str within these base directories.
    # We want to support both "helloword" and relative paths like "Agent/helloword" (if user types it)
    search_dirs = [
        Path.home() / "Desktop",
        Path.home() / "Downloads",
        Path.home() / "Documents",
        Path.home()
    ]

    for base_dir in search_dirs:
        if not base_dir.exists():
            continue
            
        # First strategy: Append the whole path string directly to the base directory
        # This handles user asking "Desktop/folder" or "folder" natively.
        candidate = base_dir / path_str
        if candidate.exists():
            return str(candidate)
            
        # Second strategy: Just look for the plain filename/foldername directly inside base_dir
        # E.g. user typed "C:\Users\Balantech\Desktop\Agent\helloword" but it's really on Desktop
        candidate_flat = base_dir / target_name
        if candidate_flat.exists():
            return str(candidate_flat)
            
    # If nothing is found, we return the expanded original string
    # The tools will then naturally throw their internal "Not Found" errors
    return str(initial_path)
