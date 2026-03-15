import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from vector.moorcheh import add_chunk, query_chunks
import uuid


class FileMemory:
    """
    Time-Travel File Memory System
    Tracks when and why files were accessed with context and embeddings.
    """
    
    def __init__(self, memory_file: str = "file_memory.json"):
        self.memory_file = memory_file
        self.memory = self._load_memory()
    
    def _load_memory(self) -> Dict:
        """Load memory from JSON file"""
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
                if "preferences" not in data:
                    data["preferences"] = {}
                return data
        return {"accesses": [], "preferences": {}}
    
    def _save_memory(self):
        """Save memory to JSON file"""
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2)

    def set_preference(self, key: str, value: str):
        """Save a user preference."""
        self.memory.setdefault("preferences", {})[key] = value
        self._save_memory()
        
    def get_preference(self, key: str) -> Optional[str]:
        """Retrieve a user preference."""
        return self.memory.get("preferences", {}).get(key)
    
    def record_access(self, file_path: str, user_task: str = "", context: str = "", summary: str = ""):
        """
        Record a file access with context and timestamp.
        Stores both locally and in vector database for semantic search.
        """
        timestamp = datetime.now().isoformat()
        
        access_record = {
            "file_path": str(Path(file_path).absolute()),
            "timestamp": timestamp,
            "user_task": user_task,
            "context": context,
            "summary": summary,
            "file_name": os.path.basename(file_path)
        }
        
        # Add to local memory
        self.memory["accesses"].append(access_record)
        self._save_memory()
        
        # Add to vector database for semantic search
        chunk_id = str(uuid.uuid4())
        searchable_text = f"{user_task} {context} {summary} {os.path.basename(file_path)}"
        metadata = {
            "file_path": access_record["file_path"],
            "timestamp": timestamp,
            "user_task": user_task,
            "file_name": access_record["file_name"]
        }
        
        try:
            add_chunk(chunk_id, searchable_text, metadata)
        except Exception as e:
            print(f"Warning: Could not add to vector DB: {e}")
    
    def search_by_context(self, query: str, n: int = 5) -> List[Dict]:
        """
        Search file history by semantic similarity.
        Example: "What PDF did I read before my ML midterm?"
        """
        try:
            # Try vector search first
            results = query_chunks(query, n)
            
            # Format results
            formatted = []
            for result in results:
                if hasattr(result, 'metadata'):
                    formatted.append({
                        "file_path": result.metadata.get("file_path", ""),
                        "file_name": result.metadata.get("file_name", ""),
                        "timestamp": result.metadata.get("timestamp", ""),
                        "user_task": result.metadata.get("user_task", ""),
                        "relevance_score": getattr(result, 'score', 0)
                    })
            
            return formatted
        except Exception as e:
            print(f"Vector search failed: {e}, falling back to local search")
            return self._local_search(query, n)
    
    def _local_search(self, query: str, n: int = 5) -> List[Dict]:
        """Fallback local search using keyword matching"""
        query_lower = query.lower()
        scored = []
        
        for access in self.memory["accesses"]:
            score = 0
            searchable = f"{access.get('user_task', '')} {access.get('context', '')} {access.get('summary', '')} {access.get('file_name', '')}".lower()
            
            # Simple keyword matching
            for word in query_lower.split():
                if word in searchable:
                    score += 1
            
            if score > 0:
                scored.append((score, access))
        
        # Sort by score descending
        scored.sort(reverse=True, key=lambda x: x[0])
        return [access for score, access in scored[:n]]
    
    def get_recent_accesses(self, limit: int = 10) -> List[Dict]:
        """Get most recent file accesses"""
        accesses = sorted(
            self.memory["accesses"],
            key=lambda x: x["timestamp"],
            reverse=True
        )
        return accesses[:limit]
    
    def get_accesses_in_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get file accesses within a date range"""
        accesses = []
        for access in self.memory["accesses"]:
            if start_date <= access["timestamp"] <= end_date:
                accesses.append(access)
        return accesses


# Global instance
file_memory = FileMemory()
