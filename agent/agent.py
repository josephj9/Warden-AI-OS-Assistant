import os
import shutil
from pathlib import Path
import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
from tools.llm import genResponse
from tools.tools import (
    organize_folder, 
    summarize_file, 
    start_folder_monitor,
    move_file,
    list_files_by_date,
    set_user_preference
)
from tools.advanced_tools import (
    time_travel_search,
    explain_folder,
    edit_file_nl,
    work_history_summary,
    proactive_suggestions,
    explain_computer,
    generate_file_graph,
    file_timeline,
)
from vector.search import hybrid_search
from memory import file_memory
from conversation_memory import conversation_memory

UNDO_STACK = []

def undo_last() -> str:
    if not UNDO_STACK:
        return "⏪ Nothing to undo — no actions have been recorded yet."
    
    last = UNDO_STACK.pop()
    tool_name = last["tool"]
    
    if tool_name == "organize_folder":
        moves = last["moves"]
        moved_back = 0
        folders_to_check = set()
        
        for old, new in reversed(moves):
            if os.path.exists(new):
                # Track which subfolder the file was in
                folders_to_check.add(os.path.dirname(new))
                os.makedirs(os.path.dirname(old), exist_ok=True)
                shutil.move(new, old)
                moved_back += 1
        
        # Clean up any now-empty folders that were created by organize_folder
        deleted_folders = []
        for folder in folders_to_check:
            try:
                if os.path.isdir(folder) and not os.listdir(folder):
                    os.rmdir(folder)
                    deleted_folders.append(os.path.basename(folder))
            except Exception:
                pass
        
        msg = f"✅ Undo complete! Moved {moved_back} file(s) back to their original locations."
        if deleted_folders:
            msg += f"\n🗑️ Removed {len(deleted_folders)} empty folder(s): {', '.join(deleted_folders)}"
        return msg
    else:
        return f"⚠️ Undo isn't supported for '{tool_name}' yet."

TOOL_REGISTRY = {
    "organize_folder": organize_folder,
    "summarize_file": summarize_file,
    "semantic_search": hybrid_search,
    "undo_last": undo_last,
    "start_folder_monitor": start_folder_monitor,
    "move_file": move_file,
    "list_files_by_date": list_files_by_date,
    "set_user_preference": set_user_preference,
    "time_travel_search": time_travel_search,
    "explain_folder": explain_folder,
    "edit_file_nl": edit_file_nl,
    "work_history_summary": work_history_summary,
    "proactive_suggestions": proactive_suggestions,
    "explain_computer": explain_computer,
    "generate_file_graph": generate_file_graph,
    "file_timeline": file_timeline,
}

def run_agent(user_input: str) -> str:
    console.print("[bold cyan]AI Agent Ready.[/bold cyan]")

    # Save the user's turn to conversation history
    conversation_memory.add_turn("user", user_input)

    # Get the recent conversation context to inject into the prompt
    convo_context = conversation_memory.get_context_block(n=8)
    convo_section = f"""
    Recent Conversation History (use this to answer follow-up questions and resolve pronouns like 'it', 'that file', 'the one I just summarized'):
    {convo_context}
    """ if convo_context else ""

    context = f"""
    You are a system AI agent with advanced file management and intelligence capabilities.

    Available tools:
    - organize_folder(folder_path) - Organizes files into categorized subfolders
    - summarize_file(file_path) - Summarizes PDF, DOCX, TXT, and code files
    - semantic_search(query) - Searches files semantically
    - undo_last() - Undoes the last action
    - start_folder_monitor(folder_path, move_to=None) - Monitors folder for new files and moves them to move_to
    - set_user_preference(category, preference) - Memorize user preference (e.g. category='pdf_destination', preference='Desktop')
    - move_file(source_path, destination_path) - Moves files or folders
    - list_files_by_date(folder_path, sort_by='created', reverse=False) - Lists files sorted by date
    
    ADVANCED TOOLS:
    - time_travel_search(query, limit=5) - Search file history: "What PDF did I read before my ML midterm?"
    - explain_folder(folder_path) - Analyzes folder and provides intelligent insights and organization suggestions. Say "explain folder X" to trigger.
    - edit_file_nl(file_path, instruction) - Edit files with natural language: "Shorten my resume to one page"
    - work_history_summary(days=7) - Summarizes what you worked on recently. Say "what did I work on" to trigger.
    - proactive_suggestions(scan_path=None) - Suggests helpful actions based on system state
    - explain_computer(scan_paths=None) - High-level overview of your entire computer. Say "explain my computer" to trigger.
    - generate_file_graph(folder_path, max_files=50) - Creates semantic graph of file relationships. Say "graph folder X" to trigger.
    - file_timeline(days=1, date=None) - Shows chronological timeline of file activity. Say "what did I work on today?" or "show timeline"

    USAGE SCENARIOS & EXAMPLES:
    - User: "organize my helloword folder" -> Invoke `organize_folder(folder_path="helloword")`
    - User: "List the files in Resume Stuff" -> Invoke `list_files_by_date(folder_path="Resume Stuff")`
    - User: "I like the pdfs from start folder monitor to go in desktop" -> Invoke `set_user_preference(category="pdf_destination", preference="Desktop")`
    - User: "What have I been doing for the last 3 days?" -> Invoke `work_history_summary(days=3)`
    - User: "what did I work on today?" -> Invoke `file_timeline(days=1)`
    - User: "what did I just summarize?" -> Look at the conversation history below and answer directly (no tool needed)
    - User: "monitor downloads and move PDFs to my lab4 721 folder" -> Invoke `start_folder_monitor(folder_path="Downloads", move_to="lab4 721")`

    {convo_section}

    You can chain actions by referencing previous results with "RESULT_0", "RESULT_1", etc. in args.
    When semantic_search or time_travel_search is chained, RESULT_0 will be the FIRST (most relevant) file path.

    User request:
    {user_input}

    Respond ONLY in JSON format:
    {{
        "plan": "...",
        "actions": [
            {{"tool": "...", "args": {{...}}}}
        ]
    }}
    """

    response = genResponse(context)

    if "error" in response:
        return response["error"]

    plan = response.get("plan", "")
    actions = response.get("actions", [])

    if not request_permission(response):
        return "Execution cancelled by user."

    results = []
    raw_results = []  # Store unformatted tool output for RESULT_ chaining

    for action in actions:
        args = action["args"].copy()
        for key, value in args.items():
            if isinstance(value, str) and value.startswith("RESULT_"):
                idx = int(value[7:])
                prev_raw = raw_results[idx]  # Use the raw tool output, not formatted string

                # Extract a usable path/string from the previous result
                if isinstance(prev_raw, list) and prev_raw:
                    # Search returned a list of paths — take the best match (first item)
                    best = str(prev_raw[0]).strip()
                    if key == "folder_path":
                        import os as _os
                        args[key] = _os.path.dirname(best) if not _os.path.isdir(best) else best
                    else:
                        args[key] = best
                elif isinstance(prev_raw, dict):
                    # Tool returned a dict — try to extract a useful value
                    args[key] = prev_raw.get("file_path") or prev_raw.get("path") or str(prev_raw)
                elif isinstance(prev_raw, str):
                    args[key] = prev_raw.strip()
                else:
                    args[key] = str(prev_raw).strip()

        raw, formatted = execute_tool(action["tool"], args)
        raw_results.append(raw)
        results.append(formatted)

    final_output = "\n\n".join(str(r) for r in results)

    # Save the agent's response to conversation memory
    conversation_memory.add_turn("agent", final_output[:500])  # trim for brevity

    return final_output


def execute_tool(tool_name: str, arguments: dict):
    """
    Executes a specific system tool.
    Returns (raw_result, formatted_string) so RESULT_ chaining uses raw data.
    """
    tool = TOOL_REGISTRY.get(tool_name)

    if not tool:
        msg = f"⚠️ Unknown tool: {tool_name}"
        return (None, msg)

    try:
        result = tool(**arguments)

        if isinstance(result, dict) and "moves" in result:
            UNDO_STACK.append({"tool": tool_name, "args": arguments, "moves": result["moves"]})

        # --- Auto-log file accesses to file_memory for history/timeline ---
        FILE_TOUCH_TOOLS = {"summarize_file", "edit_file_nl", "semantic_search",
                            "organize_folder", "move_file", "time_travel_search", "start_folder_monitor"}
        if tool_name in FILE_TOUCH_TOOLS:
            try:
                path_arg = arguments.get("file_path") or arguments.get("folder_path") or ""
                if path_arg:
                    file_memory.record_access(
                        file_path=str(path_arg),
                        user_task=f"{tool_name} — {path_arg}",
                        context=str(arguments)
                    )
            except Exception:
                pass  # Never let memory logging crash a tool

        formatted = format_result(tool_name, result)
        return (result, formatted)
    except Exception as e:
        msg = f"❌ Something went wrong while running '{tool_name}': {str(e)}"
        return (None, msg)


def format_result(tool_name: str, result) -> str:
    """
    Converts raw tool output (dicts, lists) into friendly human-readable English.
    Uses rich tables for structured data.
    """
    from io import StringIO
    from rich.console import Console as _Console
    from rich.table import Table

    def render_table(table: Table) -> str:
        """Render a rich Table to a plain string."""
        buf = StringIO()
        tmp = _Console(file=buf, highlight=False)
        tmp.print(table)
        return buf.getvalue()

    if isinstance(result, str):
        return result

    if not isinstance(result, dict):
        return str(result)

    status = result.get("status", "")
    message = result.get("message", "")

    if tool_name == "file_timeline":
        return result.get("output", message)

    # --- Error ---
    if status == "error":
        return f"\n\u274c  {message}\n"

    # --- Tools that already return a message string ---
    if message:
        return f"\n{message}\n"

    # --- summarize_file ---
    if "summary" in result and "pdf_path" in result:
        summary = result["summary"]
        pdf_path = result.get("pdf_path", "")
        lines = ["\n📄 **File Summary**\n", str(summary)]
        if pdf_path:
            lines.append(f"\n\n💾 PDF saved to: `{pdf_path}`")
        return "\n".join(lines) + "\n"

    # --- list_files_by_date ---
    if "files" in result and isinstance(result["files"], list) and result["files"] and isinstance(result["files"][0], dict) and "path" in result["files"][0]:
        files = result["files"]
        lines = [f"\n📂 **{len(files)} file(s) found:**\n"]
        for i, f in enumerate(files, 1):
            name = os.path.basename(f.get("path", ""))
            size_kb = round(f.get("size_bytes", 0) / 1024, 1)
            modified = f.get("modified", "")[:10]
            lines.append(f"  **{i}.** {name}")
            lines.append(f"      Size: {size_kb} KB  |  Last modified: {modified}")
            lines.append("")
        return "\n".join(lines)

    # --- time_travel_search ---
    if "files" in result and isinstance(result["files"], list) and result["files"] and isinstance(result["files"][0], dict) and "file_name" in result["files"][0]:
        files = result["files"]
        if not files:
            return "\n🔍 No matching files found in your history.\n"
        table = Table(title=f"🕰️ File History Search Results", show_lines=True, header_style="bold blue")
        table.add_column("File", style="bold white")
        table.add_column("Accessed", style="yellow")
        table.add_column("Context", style="cyan")
        for f in files:
            table.add_row(f.get("file_name", ""), f.get("accessed", ""), f.get("context", ""))
        return "\n" + render_table(table)

    # --- work_history_summary ---
    if "summary" in result and isinstance(result["summary"], dict):
        s = result["summary"]
        lines = [
            f"\n📅 **Work History — {s.get('period', '')}**",
            "",
            f"  📊 **Files accessed:** {s.get('total_file_accesses', 0)}",
            f"  📄 **Unique files touched:** {s.get('unique_files', 0)}",
            f"  ⏱️  **Estimated time:** ~{s.get('estimated_hours', 0)} hours",
        ]
        tasks = s.get("main_tasks", {})
        if tasks:
            lines.append("")
            lines.append("  🔧 **Activities:**")
            for task, count in tasks.items():
                lines.append(f"      • {task.replace('_', ' ').title()}: {count} time(s)")
        recent = s.get("recent_files", [])
        if recent:
            lines.append("")
            lines.append("  🗂️  **Recent Files:**")
            table = Table(show_header=True, header_style="bold yellow", show_lines=False, box=None)
            table.add_column("File", style="white")
            table.add_column("Accessed At", style="dim")
            for rf in recent[-7:]:
                table.add_row(rf.get("file", ""), rf.get("accessed", "")[:16])
            lines.append(render_table(table))
        return "\n".join(lines) + "\n"

    # --- explain_folder ---
    if "summary" in result and "organization_suggestions" in result:
        s = result["summary"]
        folder = os.path.basename(result.get("folder", ""))
        lines = [
            f"\n🗂️  **Folder Analysis: '{folder}'**",
            "",
            f"  📊 Total files: {s.get('total_files', 0)}",
        ]
        categories = s.get("categories", {})
        if categories:
            lines.append("")
            lines.append("  📌 **File types found:**")
            for cat, count in categories.items():
                lines.append(f"      • {cat}: {count} file(s)")
        exts = s.get("top_extensions", {})
        if exts:
            lines.append("")
            lines.append("  📎 **Top extensions:**")
            for ext, count in list(exts.items())[:5]:
                lines.append(f"      • {ext}: {count} file(s)")
        suggestions = result.get("organization_suggestions", [])
        if suggestions:
            lines.append("")
            lines.append("  💡 **Organization Suggestions:**")
            for sug in suggestions:
                lines.append(f"      → Create a '{sug['suggested_folder']}' folder for {sug['file_count']} file(s)")
        return "\n".join(lines) + "\n"

    # --- explain_computer ---
    if "knowledge_map" in result:
        km = result["knowledge_map"]
        lines = [
            "\n🖥️  **Your Computer at a Glance**",
            "",
            f"  📂 Total files scanned: {km.get('total_files', 0)}",
        ]
        topics = km.get("main_topics", {})
        if topics:
            lines.append("")
            lines.append("  📌 **Main topic areas:**")
            for topic, count in list(topics.items())[:8]:
                lines.append(f"      • {topic}: {count} file(s)")
        projects = km.get("top_projects", [])
        if projects:
            lines.append("")
            lines.append("  🚀 **Top project folders:**")
            for p in projects[:5]:
                lines.append(f"      📁 {p.get('name')} — {p.get('code_files')} code file(s)")
        return "\n".join(lines) + "\n"

    # --- generate_file_graph ---
    if "graph" in result:
        graph = result["graph"]
        total = result.get("total_files", 0)
        root = graph.get("name", "")
        lines = [
            f"\n🌐 **Semantic File Map: '{root}'** ({total} files)",
            "",
            "  This shows how files in this folder are grouped by topic or type:",
            "",
        ]
        for child in graph.get("children", []):
            cat_name = child.get("name", "")
            cat_files = child.get("children", [])
            lines.append(f"  📂 **{cat_name}** ({len(cat_files)} file(s))")
            for cf in cat_files[:4]:
                lines.append(f"       • {cf.get('name', '')}")
            if len(cat_files) > 4:
                lines.append(f"       ... and {len(cat_files) - 4} more")
            lines.append("")
        return "\n".join(lines)

    # --- proactive_suggestions ---
    if "suggestions" in result:
        suggestions = result["suggestions"]
        if not suggestions:
            return "\n✨ Everything looks great! No suggestions right now.\n"
        lines = ["\n💡 **Proactive Suggestions for You:**", ""]
        for sug in suggestions:
            priority = sug.get("priority", "")
            emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "•")
            lines.append(f"  {emoji} {sug.get('message', '')}")
        return "\n".join(lines) + "\n"

    # --- Fallback ---
    return "\n" + str(result) + "\n"


def request_permission(action_plan: dict) -> bool:
    """
    Displays planned actions and asks user for confirmation
    before executing system-level changes.
    """
    plan = action_plan.get("plan", "")
    actions = action_plan.get("actions", [])

    console.print(Panel(plan, title="Plan", border_style="yellow"))

    table = Table(title="Planned Actions", show_header=True, header_style="bold magenta")
    table.add_column("Step", style="dim")
    table.add_column("Tool", style="blue")
    table.add_column("Arguments", justify="left")

    for i, action in enumerate(actions, 1):
        table.add_row(str(i), action['tool'], str(action['args']))

    console.print(table)

    confirm = console.input("\n[bold yellow]Allow execution? (y/n): [/bold yellow]").strip().lower()

    return confirm == "y"


def log_action(action: str, status: str) -> None:
    """
    Records all agent decisions and system changes
    for transparency and debugging.
    """

    timestamp = datetime.datetime.now().isoformat()

    log_entry = f"{timestamp} | ACTION: {action} | STATUS: {status}\n"

    with open("agent.log", "a") as log_file:
        log_file.write(log_entry)





#Memory System (Vector Store) 
# def store_memory(text: str) -> None:
#     """
#     Saves important information into a vector database
#     for future semantic retrieval.
#     """

# def retrieve_memory(query: str) -> list:
#     """
#     Retrieves relevant past memories based on semantic  similarity.
#     """
# def dry_run_action(action_plan: dict) -> str:
#     """
#     Simulates actions without making actual system changes.
#     Used for safety during demos.
#     """

# def undo()
