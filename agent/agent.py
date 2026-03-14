import os
import shutil
from pathlib import Path
import datetime
from tools.llm import genResponse
from tools.tools import organize_folder, summarize_file, start_folder_monitor
from vector.search import hybrid_search

UNDO_STACK = []

def undo_last() -> str:
    if not UNDO_STACK:
        return "No actions to undo."
    
    last = UNDO_STACK.pop()
    tool_name = last["tool"]
    
    if tool_name == "organize_folder":
        moves = last["moves"]
        for old, new in reversed(moves):
            if os.path.exists(new):
                shutil.move(new, old)
        return f"Undid organize: moved {len(moves)} files back."
    else:
        return f"Undo not implemented for {tool_name}"

TOOL_REGISTRY = {
    "organize_folder": organize_folder,
    "summarize_file": summarize_file,
    "semantic_search": hybrid_search,
    "undo_last": undo_last,
    "start_folder_monitor": start_folder_monitor,
}

def run_agent(user_input: str) -> str:
    print("AI Agent Ready.")

    context = f"""
    You are a system AI agent.

    Available tools:
    - organize_folder(folder_path)
    - summarize_file(file_path)
    - semantic_search(query)
    - undo_last()
    - start_folder_monitor(folder_path)

    You can chain actions by referencing previous results with "RESULT_0", "RESULT_1", etc. in args.

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

    for action in actions:
        args = action["args"].copy()
        for key, value in args.items():
            if isinstance(value, str) and value.startswith("RESULT_"):
                idx = int(value[6:])
                prev_result = results[idx]
                if isinstance(prev_result, list):
                    args[key] = prev_result[0] if prev_result else ""
                else:
                    args[key] = str(prev_result)
        result = execute_tool(action["tool"], args)
        results.append(result)

    return "\n".join(str(r) for r in results)


def execute_tool(tool_name: str, arguments: dict) -> str:
    """
    Executes a specific system tool with provided arguments.
    Acts as the bridge between LLM reasoning and OS actions.
    """
    tool = TOOL_REGISTRY.get(tool_name)

    if not tool:
        return f"Unknown tool: {tool_name}"

    try:
        result = tool(**arguments)
        
        if isinstance(result, dict) and "moves" in result:
            UNDO_STACK.append({"tool": tool_name, "args": arguments, "moves": result["moves"]})
            return result["message"]
        else:
            return result
    except Exception as e:
        return f"Tool execution failed ({tool_name}): {str(e)}"


def request_permission(action_plan: dict) -> bool:
    """
    Displays planned actions and asks user for confirmation
    before executing system-level changes.
    """

    print("\n=== Planned Actions ===")
    print("Plan:", action_plan.get("plan", ""))

    actions = action_plan.get("actions", [])

    for i, action in enumerate(actions, 1):
        print(f"{i}. {action['tool']} -> {action['args']}")

    confirm = input("\nAllow execution? (y/n): ").strip().lower()

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





#DO LATER

# def watch_folder(folder_path: str) -> None:
#     """
#     Continuously monitors a folder and reacts when
#     new files are added or modified.
#     """



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
