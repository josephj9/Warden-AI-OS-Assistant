# Suppress noisy warnings from HuggingFace/transformers/sentence-transformers before any imports
import os
import warnings
import logging
import sys

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

from agent.agent import run_agent, format_result
from vector.indexer import index_folder
import threading
import time
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.rule import Rule
from tools.advanced_tools import proactive_suggestions

console = Console()

# --- Terminal one-shot: run from CLI e.g. python main.py "organize the folder with ML powerpoints" ---
def run_terminal_one_shot():
    """If user passed a query as args, run once and exit. Use --yes to skip confirmation."""
    if __name__ != "__main__":
        return False
    args = sys.argv[1:]
    if not args:
        return False
    auto_yes = "--yes" in args or "-y" in args
    args = [a for a in args if a not in ("--yes", "-y")]
    if not args:
        return False
    query = " ".join(args)
    os.environ["WARDEN_AUTO_YES"] = "1" if auto_yes else "0"
    result = run_agent(query)
    console.print(Rule("[bold green]Result[/bold green]", style="green"))
    console.print(Markdown(str(result)))
    console.print(Rule(style="green"))
    return True

if run_terminal_one_shot():
    sys.exit(0)

# Auto-index key folders on first startup only
INDEX_STATE_FILE = "index_state.json"
indexed_ok = False
try:
    if os.path.exists(INDEX_STATE_FILE):
        indexed_ok = True
    else:
        console.print(Panel("Indexing key folders...", title="Startup", border_style="blue"))
        index_folder(os.path.expanduser("~/Desktop"))
        index_folder(os.path.expanduser("~/Documents"))
        index_folder(os.path.expanduser("~/Downloads"))
        with open(INDEX_STATE_FILE, "w", encoding="utf-8") as f:
            f.write('{"indexed": true}')
        indexed_ok = True
        console.print(Panel("Indexing complete. Warden AI is ready!", title="Startup", border_style="green"))
except Exception:
    # If indexing fails, continue; semantic tools will still work on whatever is already indexed.
    indexed_ok = False

# --- Idle Proactive Suggestion System ---
IDLE_TIMEOUT = 60  # seconds of inactivity before suggesting (fires once per session)
_last_activity = time.time()
_suggestion_lock = threading.Lock()
_suggestion_fired = False  # Only trigger once per session

def _idle_watcher():
    """Background thread: fires proactive suggestions ONCE after idle timeout."""
    global _last_activity, _suggestion_fired
    while True:
        time.sleep(5)
        if _suggestion_fired:
            break  # Already fired once, stop watching
        idle_for = time.time() - _last_activity
        if idle_for >= IDLE_TIMEOUT:
            _suggestion_fired = True
            with _suggestion_lock:
                result = proactive_suggestions()
                formatted = format_result("proactive_suggestions", result)
                if formatted.strip() and "No suggestions" not in formatted:
                    console.print()
                    console.print(Rule("[bold yellow]💡 Warden Suggestion[/bold yellow]", style="yellow"))
                    console.print(Markdown(formatted))
                    console.print(Rule(style="yellow"))

watcher = threading.Thread(target=_idle_watcher, daemon=True)
watcher.start()

while True:
    user_input = console.input("\n[bold cyan]Ask the agent:[/bold cyan] ")

    if user_input.lower() in ["exit", "quit"]:
        console.print("[bold yellow]Goodbye! Warden AI shutting down.[/bold yellow]")
        break

    result = run_agent(user_input)

    console.print(Rule("[bold green]Result[/bold green]", style="green"))
    console.print(Markdown(str(result)))
    console.print(Rule(style="green"))