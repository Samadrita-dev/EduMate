from typing import List, Dict, Any, Optional
from tools.memory_tools import save_memory, retrieve_memory, delete_memory, clear_student_memory

class LongTermMemory:
    """
    Manages persistent student preferences (study times, focus areas, notifications)
    stored securely in SQLite with student isolation.
    """
    def __init__(self, student_id: int):
        self.student_id = student_id

    def set_preference(self, key: str, value: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Saves or updates a preference."""
        return save_memory(
            student_id=self.student_id,
            memory_type="long_term",
            key=key,
            value=value,
            metadata=metadata
        )

    def get_preferences(self) -> List[Dict[str, Any]]:
        """Retrieves all long-term preferences for the student."""
        res = retrieve_memory(self.student_id, memory_type="long_term")
        return res.get("memories", [])

    def get_preference_by_key(self, key: str) -> Optional[str]:
        """Finds value for a specific key."""
        res = retrieve_memory(self.student_id, memory_type="long_term", key=key)
        memories = res.get("memories", [])
        if memories:
            return memories[0]["value"]
        return None

    def get_formatted_context(self) -> str:
        """Generates a condensed bulleted string for LLM prompting."""
        prefs = self.get_preferences()
        if not prefs:
            return "No custom preferences saved."
        lines = []
        for p in prefs:
            lines.append(f"- {p['key'].replace('_', ' ').capitalize()}: {p['value']}")
        return "\n".join(lines)

    def delete_preference(self, memory_id: int) -> Dict[str, Any]:
        return delete_memory(memory_id, self.student_id)

    def clear_all(self) -> Dict[str, Any]:
        return clear_student_memory(self.student_id, memory_type="long_term")
