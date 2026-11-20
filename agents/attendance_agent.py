from typing import Dict, Any, Optional
from tools.attendance_tools import get_attendance, calculate_attendance, get_attendance_alerts

class AttendanceAgent:
    """Specialized agent responsible for calculating and auditing student attendance."""

    def __init__(self, student_id: int):
        self.student_id = student_id
        self.agent_name = "ATTENDANCE_AGENT"

    def execute(self, action: str = "summary", params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params or {}
        act = action.lower()

        if act in ["alerts", "warnings", "check_shortage"]:
            res = get_attendance_alerts(self.student_id)
            return {"agent": self.agent_name, "action": act, "result": res}

        elif act in ["calculate", "formula"]:
            attended = params.get("attended", 0)
            total = params.get("total", 0)
            pct = calculate_attendance(attended, total)
            return {
                "agent": self.agent_name,
                "action": act,
                "result": {"attended": attended, "total": total, "percentage": pct}
            }

        else:
            # Default: comprehensive attendance summary
            subject_id = params.get("subject_id")
            res = get_attendance(self.student_id, subject_id=subject_id)
            return {"agent": self.agent_name, "action": "summary", "result": res}
