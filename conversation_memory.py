"""
Conversational Memory for Warden AI
Stores multi-turn dialogue history so the agent remembers context across messages.

Example:
    User: "summarize discrete math 1"
    -- later --
    User: "what did I just summarize?"
    Agent knows: you just summarized Discrete Math 1.pdf
"""

import os
import json
from datetime import datetime
from typing import List, Dict

CONVERSATION_FILE = "conversation_history.json"
MAX_TURNS_IN_CONTEXT = 14   # How many past turns to inject into the prompt
MAX_HISTORY_STORED = 200    # How many turns to keep on disk
BRIEF_SUMMARY_MAX_CHARS = 120  # Max chars per turn in brief summary


class ConversationMemory:
    """
    Persists the conversation as a list of turns:
        [{"role": "user"|"agent", "text": "...", "timestamp": "..."}]
    """

    def __init__(self, history_file: str = CONVERSATION_FILE):
        self.history_file = history_file
        self.history: List[Dict] = self._load()

    def _load(self) -> List[Dict]:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save(self):
        try:
            # Keep only the most recent N turns
            trimmed = self.history[-MAX_HISTORY_STORED:]
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(trimmed, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def add_turn(self, role: str, text: str):
        """Add a single dialogue turn (role: 'user' or 'agent')."""
        self.history.append({
            "role": role,
            "text": str(text).strip(),
            "timestamp": datetime.now().isoformat()
        })
        self._save()

    def get_recent_turns(self, n: int = MAX_TURNS_IN_CONTEXT) -> List[Dict]:
        """Return the last N turns."""
        return self.history[-n:]

    def get_brief_summary(self, n_turns: int = 6) -> str:
        """
        One-line summary of the last few turns for quick context.
        E.g. "User: organize my folder. Agent: Organized 5 files. User: summarize readme."
        """
        turns = self.get_recent_turns(n_turns)
        if not turns:
            return ""
        parts = []
        for t in turns:
            role = "User" if t["role"] == "user" else "Agent"
            text = (t.get("text") or "").strip().replace("\n", " ")[:BRIEF_SUMMARY_MAX_CHARS]
            if len((t.get("text") or "")) > BRIEF_SUMMARY_MAX_CHARS:
                text += "..."
            parts.append(f"{role}: {text}")
        return " | ".join(parts)

    def get_context_block(self, n: int = MAX_TURNS_IN_CONTEXT, include_brief: bool = True) -> str:
        """
        Format recent turns as a readable block to inject into the agent prompt.
        If include_brief is True, prefixes a one-line summary for conversational continuity.
        Returns empty string if no history.
        """
        turns = self.get_recent_turns(n)
        if not turns:
            return ""

        lines = ["--- Conversation History (most recent last) ---"]
        if include_brief:
            brief = self.get_brief_summary(n_turns=min(6, len(turns)))
            if brief:
                lines.append(f"Brief: {brief}")
                lines.append("")
        for turn in turns:
            ts = turn.get("timestamp", "")[:16].replace("T", " ")
            role_label = "User" if turn["role"] == "user" else "Agent"
            lines.append(f"[{ts}] {role_label}: {turn['text']}")
        lines.append("--- End of History ---")
        return "\n".join(lines)

    def clear(self):
        """Wipe conversation history."""
        self.history = []
        self._save()

    def get_full_history(self) -> List[Dict]:
        return list(self.history)


# Singleton instance -- import this everywhere
conversation_memory = ConversationMemory()
