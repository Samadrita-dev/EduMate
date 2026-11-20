from typing import List, Dict, Any, Optional
from tools.memory_tools import save_memory, retrieve_memory, delete_memory
from database.db import get_db
from database.models import StudyPlan

class EpisodicMemory:
    """
    Manages episodic recollections: past approved study plans,
    notable academic interactions, and historical commitments.
    """
    def __init__(self, student_id: int):
        self.student_id = student_id

    def record_episode(self, key: str, summary: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Stores a historical event or decision."""
        return save_memory(
            student_id=self.student_id,
            memory_type="episodic",
            key=key,
            value=summary,
            metadata=metadata
        )

    def get_episodes(self) -> List[Dict[str, Any]]:
        """Retrieves past episodes recorded in database."""
        res = retrieve_memory(self.student_id, memory_type="episodic")
        return res.get("memories", [])

    def get_past_approved_plans(self) -> List[Dict[str, Any]]:
        """Retrieves past study plans that received human approval."""
        with get_db() as db:
            plans = db.query(StudyPlan).filter(
                StudyPlan.student_id == self.student_id,
                StudyPlan.status.in_(["Approved", "Completed"])
            ).order_by(StudyPlan.created_at.desc()).limit(5).all()
            return [p.to_dict() for p in plans]

    def get_formatted_context(self) -> str:
        """Condensed episodic context string for planners."""
        episodes = self.get_episodes()
        approved_plans = self.get_past_approved_plans()

        context_parts = []
        if episodes:
            context_parts.append("Past Notable Interactions:")
            for e in episodes[:3]:
                context_parts.append(f"- {e['key']}: {e['value']}")

        if approved_plans:
            context_parts.append("Previously Approved Plans:")
            for p in approved_plans[:2]:
                context_parts.append(f"- {p['title']} ({p['target_exam_or_goal']}) [Status: {p['status']}]")

        if not context_parts:
            return "No historical study plans or episodes recorded."

        return "\n".join(context_parts)
