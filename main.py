from agent.agent import run_agent
from vector.indexer import index_folder
import os

# Auto-index key folders on startup
print("Indexing key folders...")
index_folder(os.path.expanduser("~/Desktop"))
index_folder(os.path.expanduser("~/Documents"))
index_folder(os.path.expanduser("~/Downloads"))
print("Indexing complete.")

while True:
    user_input = input("\nAsk the agent: ")

    if user_input.lower() in ["exit", "quit"]:
        break

    result = run_agent(user_input)

    print("\nResult:")
    print(result)