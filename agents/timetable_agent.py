from typing import Dict, Any, Optional
from tools.timetable_tools import get_timetable, check_schedule_conflicts, get_available_slots

class TimetableAgent:
    """Specialized agent responsible for class schedules, free slot discovery, and conflict checks."""

    def __init__(self, student_id: int):
        self.student_id = student_id
        self.agent_name = "TIMETABLE_AGENT"

    def execute(self, action: str = "get", params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params or {}
        act = action.lower()

        if act in ["check_conflict", "conflict"]:
            day = params.get("day", "Monday")
            start = params.get("start_time", "10:00")
            end = params.get("end_time", "11:00")
            res = check_schedule_conflicts(self.student_id, target_day=day, start_time=start, end_time=end)
            return {"agent": self.agent_name, "action": act, "result": res}

        elif act in ["available_slots", "free_time"]:
            day = params.get("day", "Monday")
            window_start = params.get("window_start", "08:00")
            window_end = params.get("window_end", "20:00")
            res = get_available_slots(self.student_id, day_of_week=day, start_window=window_start, end_window=window_end)
            return {"agent": self.agent_name, "action": act, "result": res}

        else:
            day = params.get("day")
            res = get_timetable(self.student_id, day_of_week=day)
            return {"agent": self.agent_name, "action": "get_timetable", "result": res}
