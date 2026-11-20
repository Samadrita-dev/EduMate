from typing import Dict, Any, Optional
from tools.exam_tools import get_exams, get_exam_details, update_exam_prep_status

class ExamAgent:
    """Specialized agent responsible for tracking examination dates, syllabus coverage, and countdowns."""

    def __init__(self, student_id: int):
        self.student_id = student_id
        self.agent_name = "EXAM_AGENT"

    def execute(self, action: str = "get", params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params or {}
        act = action.lower()

        if act in ["details", "syllabus"]:
            exam_id = params.get("exam_id")
            if not exam_id:
                return {"agent": self.agent_name, "success": False, "error": "exam_id required for details."}
            res = get_exam_details(exam_id=exam_id, student_id=self.student_id)
            return {"agent": self.agent_name, "action": act, "result": res}

        elif act in ["update_status", "prep_status"]:
            exam_id = params.get("exam_id")
            new_status = params.get("status", "In Progress")
            if not exam_id:
                return {"agent": self.agent_name, "success": False, "error": "exam_id required for status update."}
            res = update_exam_prep_status(exam_id=exam_id, student_id=self.student_id, new_status=new_status)
            return {"agent": self.agent_name, "action": act, "result": res}

        else:
            upcoming = params.get("upcoming_only", True)
            res = get_exams(self.student_id, upcoming_only=upcoming)
            return {"agent": self.agent_name, "action": "list_exams", "result": res}
