import os
import sys

from agent.agent import run_agent
from rich.console import Console
from rich.markdown import Markdown
from rich.rule import Rule


console = Console()


def main() -> None:
    """
    Global CLI entrypoint for Warden.

    Examples:
      warden "organize my desktop"
      warden --yes "organize the folder with the machine learning power points"
      warden --dry-run "explain my ML slides folder"
    """
    args = sys.argv[1:]
    if not args:
        console.print("Usage: warden [--yes] [--dry-run] <command text>")
        console.print('Example: warden --yes "organize my desktop"')
        return

    auto_yes = "--yes" in args or "-y" in args
    dry_run = "--dry-run" in args
    # Strip flags
    args = [a for a in args if a not in ("--yes", "-y", "--dry-run")]
    if not args:
        console.print("No command provided after flags.")
        return

    query = " ".join(args)

    # Configure behavior for the agent
    os.environ["WARDEN_AUTO_YES"] = "1" if auto_yes else "0"
    os.environ["WARDEN_DRY_RUN"] = "1" if dry_run else "0"

    result = run_agent(query, dry_run=dry_run)

    console.print(Rule("[bold green]Result[/bold green]", style="green"))
    console.print(Markdown(str(result)))
    console.print(Rule(style="green"))


if __name__ == "__main__":
    main()

