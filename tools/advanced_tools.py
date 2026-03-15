"""
Advanced Tools for Warden AI Assistant
Implements the 7 impressive hackathon features
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List
from tools.llm import summerize
from tools.extract import extract_pdf, extract_docx, extract_text
from memory import file_memory
from tools.utils import resolve_path


# TOOL: File Timeline
def file_timeline(days: int = 1, date: str = None):
    """
    Shows a beautiful chronological timeline of file activity.
    Groups events by date and hour.

    Examples:
      "What did I work on today?"     -> file_timeline(days=1)
      "Show me yesterday's activity"  -> file_timeline(days=2)
      "What did I do on March 14?"    -> file_timeline(date='2025-03-14')
    """
    try:
        all_accesses = file_memory.get_accesses_in_range("", "~") or []
        if not all_accesses:
            all_accesses = file_memory.get_recent_accesses(limit=200)

        if not all_accesses:
            return {
                "status": "success",
                "message": (
                    "\n⏳  **No file activity recorded yet.**\n\n"
                    "Try summarizing a file or using organize_folder first — "
                    "Warden tracks everything you do!\n"
                ),
                "timeline": []
            }

        # --- Filter by date or day range ---
        now = datetime.now()
        if date:
            try:
                target = datetime.strptime(date, "%Y-%m-%d")
                start = target.replace(hour=0, minute=0, second=0)
                end   = target.replace(hour=23, minute=59, second=59)
            except ValueError:
                return {"status": "error", "message": f"Invalid date format: '{date}'. Use YYYY-MM-DD."}
        else:
            start = now - timedelta(days=days)
            end   = now

        filtered = []
        for a in all_accesses:
            try:
                ts = datetime.fromisoformat(a.get("timestamp", ""))
                if start <= ts <= end:
                    filtered.append((ts, a))
            except Exception:
                pass

        if not filtered:
            period = date if date else f"the last {days} day(s)"
            return {
                "status": "success",
                "message": f"\n📭  No activity recorded for {period}.\n",
                "timeline": []
            }

        # --- Group by date then by hour ---
        by_day: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
        for ts, a in sorted(filtered):
            day_key  = ts.strftime("%A, %B %d %Y")          # "Saturday, March 14 2025"
            hour_key = ts.strftime("%I:%M %p")               # "03:21 PM"
            by_day[day_key][hour_key].append({
                "time":    hour_key,
                "action":  a.get("user_task", "File accessed"),
                "file":    a.get("file_name", ""),
                "path":    a.get("file_path", ""),
            })

        # --- Build output ---
        ACTION_EMOJI = {
            "summarize": "📄",
            "organize":  "📂",
            "move":      "🚀",
            "search":    "🔍",
            "edit":      "✏️",
            "monitor":   "👁️",
        }

        lines = ["\n🗓️  **File Activity Timeline**\n"]
        timeline_data = []

        for day, hours in by_day.items():
            lines.append(f"## 📅 {day}")
            lines.append("")
            day_entries = []
            for hour, events in sorted(hours.items()):
                for ev in events:
                    action = ev["action"].lower()
                    emoji = next((e for k, e in ACTION_EMOJI.items() if k in action), "📌")
                    file_label = f" — **{ev['file']}**" if ev["file"] else ""
                    lines.append(f"  **{ev['time']}**  {emoji}  {ev['action']}{file_label}")
                    day_entries.append(ev)
            lines.append("")
            timeline_data.append({"day": day, "events": day_entries})

        total = sum(len(h) for d in by_day.values() for h in d.values())
        lines.append(f"_Total: {total} event(s) recorded_\n")

        return {
            "status":   "success",
            "timeline": timeline_data,
            "output":   "\n".join(lines)
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# TOOL 6: Time-Travel File Search
def time_travel_search(query: str, limit: int = 5):
    """
    Searches file history using semantic search and context.
    Example: "What PDF did I read before my ML midterm?"
    Returns files with timestamps, context, and summaries.
    """
    try:
        results = file_memory.search_by_context(query, limit)
        
        if not results:
            return {
                "status": "success",
                "message": "No matching files found in history.",
                "files": []
            }
        
        formatted_results = []
        for result in results:
            timestamp_str = result.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(timestamp_str)
                readable_time = dt.strftime("%B %d, %Y at %I:%M %p")
            except:
                readable_time = timestamp_str
            
            formatted_results.append({
                "file_name": result.get("file_name", ""),
                "file_path": result.get("file_path", ""),
                "accessed": readable_time,
                "context": result.get("user_task", ""),
                "relevance": result.get("relevance_score", 0)
            })
        
        return {
            "status": "success",
            "query": query,
            "files": formatted_results
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# TOOL 7: Explain Folder (Auto-Understanding)
def explain_folder(folder_path: str):
    """
    Analyzes a folder and provides intelligent insights:
    - File count and categorization
    - Topic clustering
    - Organization suggestions
    """
    try:
        folder_path = resolve_path(folder_path)
        if not os.path.isdir(folder_path):
            return {"status": "error", "message": f"Folder not found: {folder_path}"}
        
        # Collect all files
        files = []
        for root, dirs, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                files.append(filepath)
        
        if not files:
            return {"status": "success", "message": "Folder is empty.", "analysis": {}}
        
        # Categorize by extension
        extensions = Counter()
        categories = defaultdict(list)
        
        category_map = {
            "Documents": [".pdf", ".docx", ".doc", ".txt", ".md", ".rtf"],
            "Code": [".py", ".js", ".java", ".cpp", ".c", ".html", ".css", ".ts", ".jsx", ".tsx"],
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico"],
            "Data": [".csv", ".json", ".xml", ".xlsx", ".xls", ".db", ".sql"],
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv"],
            "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg"]
        }
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            extensions[ext] += 1
            
            # Categorize
            categorized = False
            for category, exts in category_map.items():
                if ext in exts:
                    categories[category].append(file)
                    categorized = True
                    break
            
            if not categorized and ext:
                categories["Other"].append(file)
        
        # Build summary
        summary = {
            "total_files": len(files),
            "categories": {cat: len(files) for cat, files in categories.items()},
            "top_extensions": dict(extensions.most_common(5)),
        }
        
        # Generate organization suggestions
        suggestions = []
        for category, cat_files in categories.items():
            if len(cat_files) >= 3:
                suggestions.append({
                    "category": category,
                    "file_count": len(cat_files),
                    "suggested_folder": category
                })
        
        return {
            "status": "success",
            "folder": folder_path,
            "summary": summary,
            "organization_suggestions": suggestions
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


# TOOL 8: Natural Language File Editing
def edit_file_nl(file_path: str, instruction: str):
    """
    Edit files using natural language instructions.
    Examples:
    - "Shorten my resume to one page"
    - "Turn my project report into a presentation"
    - "Remove all comments from this code"
    """
    try:
        file_path = resolve_path(file_path)
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"File not found: {file_path}"}
        
        # Extract current content
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()
        
        if extension == ".pdf":
            content = extract_pdf(file_path)
        elif extension == ".docx":
            content = extract_docx(file_path)
        elif extension in [".txt", ".py", ".js", ".html", ".css", ".md", ".csv"]:
            content = extract_text(file_path)
        else:
            return {"status": "error", "message": f"Unsupported file type: {extension}"}
        
        # Use LLM to perform the edit
        prompt = f"""
You are an expert file editor. 

Original file content:
{content[:4000]}  

User instruction: {instruction}

Please perform the requested edit and return ONLY the edited content, without any explanations or markdown formatting.
"""
        
        edited_content = summerize(prompt)  # Using summerize as general LLM call
        
        # Save edited version
        base, ext = os.path.splitext(file_path)
        new_file_path = f"{base}_edited{ext}"
        
        with open(new_file_path, 'w', encoding='utf-8') as f:
            f.write(edited_content)
        
        return {
            "status": "success",
            "original_file": file_path,
            "edited_file": new_file_path,
            "instruction": instruction
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


# TOOL 9: Work History Summary
def work_history_summary(days: int = 7):
    """
    Summarizes what you worked on in the last N days.
    Shows main focus areas, files used, and estimated time.
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        accesses = file_memory.get_accesses_in_range(
            start_date.isoformat(),
            end_date.isoformat()
        )
        
        if not accesses:
            return {
                "status": "success",
                "message": f"No file activity in the last {days} days.",
                "summary": {}
            }
        
        # Analyze patterns
        file_types = Counter()
        tasks = Counter()
        files_used = []
        
        for access in accesses:
            ext = os.path.splitext(access.get("file_name", ""))[1]
            if ext:
                file_types[ext] += 1
            
            task = access.get("user_task", "")
            if task:
                tasks[task] += 1
            
            files_used.append({
                "file": access.get("file_name", ""),
                "path": access.get("file_path", ""),
                "accessed": access.get("timestamp", "")
            })
        
        # Estimate time (rough heuristic: 30 min per file access)
        estimated_hours = len(accesses) * 0.5
        
        summary = {
            "period": f"Last {days} days",
            "total_file_accesses": len(accesses),
            "unique_files": len(set(a.get("file_path", "") for a in accesses)),
            "estimated_hours": round(estimated_hours, 1),
            "main_tasks": dict(tasks.most_common(5)),
            "file_types": dict(file_types.most_common(5)),
            "recent_files": files_used[-10:]  # Last 10
        }
        
        return {
            "status": "success",
            "summary": summary
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


# TOOL 10: Proactive Suggestions
def proactive_suggestions(scan_path: str = None):
    """
    Analyzes system state and suggests helpful actions.
    - Detects messy folders
    - Suggests summarization for related files
    - Identifies patterns
    """
    try:
        suggestions = []
        
        # If no path specified, check common locations
        if not scan_path:
            common_paths = [
                os.path.expanduser("~/Desktop"),
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Documents")
            ]
        else:
            common_paths = [resolve_path(scan_path)]
        
        for path in common_paths:
            if not os.path.exists(path):
                continue
            
            # Count files
            files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            
            if len(files) > 20:
                suggestions.append({
                    "type": "organization",
                    "priority": "high",
                    "message": f"Your {os.path.basename(path)} has {len(files)} files. Would you like me to organize them?",
                    "action": "organize_folder",
                    "args": {"folder_path": path}
                })
            
            # Check for multiple PDFs
            pdfs = [f for f in files if f.endswith('.pdf')]
            if len(pdfs) >= 3:
                suggestions.append({
                    "type": "summarization",
                    "priority": "medium",
                    "message": f"I noticed {len(pdfs)} PDF files in {os.path.basename(path)}. Would you like a summary?",
                    "action": "batch_summarize",
                    "args": {"files": [os.path.join(path, p) for p in pdfs[:5]]}
                })
        
        # Check recent activity
        recent = file_memory.get_recent_accesses(5)
        if len(recent) >= 3:
            # Check if they're related
            file_names = [r.get("file_name", "") for r in recent]
            suggestions.append({
                "type": "insight",
                "priority": "low",
                "message": f"You recently accessed: {', '.join(file_names[:3])}. Want me to find related files?",
                "action": "semantic_search",
                "args": {}
            })
        
        return {
            "status": "success",
            "suggestions": suggestions
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


# TOOL 11: Explain Computer
def explain_computer(scan_paths: List[str] = None, depth: int = 2):
    """
    Generates a high-level overview of your entire computer.
    Shows main topics, projects, and knowledge areas.
    """
    try:
        if not scan_paths:
            # Default to user directories
            home = os.path.expanduser("~")
            scan_paths = [
                os.path.join(home, "Documents"),
                os.path.join(home, "Desktop"),
                os.path.join(home, "Downloads"),
                os.path.join(home, "Projects") if os.path.exists(os.path.join(home, "Projects")) else None
            ]
        
        scan_paths = [resolve_path(p) for p in scan_paths if p]
        scan_paths = [p for p in scan_paths if os.path.exists(p)]
        
        # Collect all files
        all_files = []
        for base_path in scan_paths:
            for root, dirs, files in os.walk(base_path):
                # Limit depth
                if root[len(base_path):].count(os.sep) >= depth:
                    dirs[:] = []
                    continue
                
                for file in files:
                    all_files.append(os.path.join(root, file))
        
        # Categorize
        categories = defaultdict(list)
        category_map = {
            "Machine Learning": [".ipynb", ".h5", ".pkl", ".pth"],
            "Web Development": [".html", ".css", ".js", ".tsx", ".jsx"],
            "Data Analysis": [".csv", ".xlsx", ".json", ".xml"],
            "Documents": [".pdf", ".docx", ".doc", ".txt"],
            "Code Projects": [".py", ".java", ".cpp", ".c"],
            "Media": [".jpg", ".png", ".mp4", ".mp3"],
        }
        
        for file in all_files:
            ext = os.path.splitext(file)[1].lower()
            for category, exts in category_map.items():
                if ext in exts:
                    categories[category].append(file)
                    break
        
        # Find project directories (directories with many code files)
        project_dirs = defaultdict(int)
        code_extensions = [".py", ".js", ".java", ".cpp", ".c", ".go", ".rs"]
        
        for file in all_files:
            if any(file.endswith(ext) for ext in code_extensions):
                dir_path = os.path.dirname(file)
                project_dirs[dir_path] += 1
        
        # Top projects (directories with most code files)
        top_projects = sorted(project_dirs.items(), key=lambda x: x[1], reverse=True)[:5]
        
        knowledge_map = {
            "total_files": len(all_files),
            "main_topics": {cat: len(files) for cat, files in categories.items() if len(files) > 0},
            "top_projects": [
                {
                    "path": path,
                    "name": os.path.basename(path),
                    "code_files": count
                }
                for path, count in top_projects
            ],
            "scanned_locations": scan_paths
        }
        
        return {
            "status": "success",
            "knowledge_map": knowledge_map
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


# TOOL 12: Generate Semantic File Graph
def generate_file_graph(folder_path: str, max_files: int = 50):
    """
    Creates a graph showing relationships between files based on:
    - Topic similarity
    - File type
    - Access patterns
    Returns a hierarchical structure.
    """
    try:
        folder_path = resolve_path(folder_path)
        if not os.path.isdir(folder_path):
            return {"status": "error", "message": f"Folder not found: {folder_path}"}
        
        # Collect files
        files = []
        for root, dirs, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                files.append(filepath)
                if len(files) >= max_files:
                    break
            if len(files) >= max_files:
                break
        
        if not files:
            return {"status": "success", "message": "No files found.", "graph": {}}
        
        # Build hierarchical structure
        graph = {
            "name": os.path.basename(folder_path),
            "type": "folder",
            "children": []
        }
        
        # Group by category
        categories = defaultdict(list)
        category_map = {
            "Documents": [".pdf", ".docx", ".doc", ".txt", ".md"],
            "Code": [".py", ".js", ".java", ".cpp", ".html", ".css"],
            "Data": [".csv", ".json", ".xml", ".xlsx"],
            "Images": [".jpg", ".png", ".gif", ".svg"],
            "Other": []
        }
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            categorized = False
            
            for category, exts in category_map.items():
                if ext in exts:
                    categories[category].append(file)
                    categorized = True
                    break
            
            if not categorized:
                categories["Other"].append(file)
        
        # Build tree
        for category, cat_files in categories.items():
            if not cat_files:
                continue
            
            category_node = {
                "name": category,
                "type": "category",
                "children": []
            }
            
            for file in cat_files[:10]:  # Limit per category
                file_node = {
                    "name": os.path.basename(file),
                    "type": "file",
                    "path": file,
                    "extension": os.path.splitext(file)[1]
                }
                category_node["children"].append(file_node)
            
            graph["children"].append(category_node)
        
        return {
            "status": "success",
            "graph": graph,
            "total_files": len(files)
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
