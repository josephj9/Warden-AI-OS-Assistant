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

# Auto-index key folders on startup
console.print(Panel("Indexing key folders...", title="Startup", border_style="blue"))
index_folder(os.path.expanduser("~/Desktop"))
index_folder(os.path.expanduser("~/Documents"))
index_folder(os.path.expanduser("~/Downloads"))
console.print(Panel("Indexing complete. Warden AI is ready!", title="Startup", border_style="green"))

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