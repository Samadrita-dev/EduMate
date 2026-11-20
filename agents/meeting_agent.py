from typing import Dict, Any, Optional
from tools.meeting_tools import get_teachers, request_meeting, get_meeting_status

class MeetingAgent:
    """Specialized agent responsible for teacher directory inquiries and meeting requests."""

    def __init__(self, student_id: int):
        self.student_id = student_id
        self.agent_name = "MEETING_AGENT"

    def execute(self, action: str = "status", params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params or {}
        act = action.lower()

        if act in ["teachers", "directory", "faculty"]:
            dept = params.get("department")
            search = params.get("search_query")
            res = get_teachers(department=dept, search_query=search)
            return {"agent": self.agent_name, "action": act, "result": res}

        elif act in ["request", "book", "schedule"]:
            teacher_id = params.get("teacher_id")
            purpose = params.get("purpose", "Academic Consultation")
            date_str = params.get("date")
            time_str = params.get("time")

            if not teacher_id or not date_str or not time_str:
                return {
                    "agent": self.agent_name,
                    "success": False,
                    "error": "teacher_id, date (YYYY-MM-DD), and time (HH:MM) are required to request a meeting."
                }

            res = request_meeting(
                student_id=self.student_id,
                teacher_id=teacher_id,
                purpose=purpose,
                requested_date=date_str,
                requested_time=time_str
            )
            return {"agent": self.agent_name, "action": act, "result": res}

        else:
            status = params.get("status")
            res = get_meeting_status(self.student_id, status=status)
            return {"agent": self.agent_name, "action": "get_status", "result": res}
