from typing import Optional, List, Dict, Any
from datetime import datetime
from database.db import get_db
from database.models import TimetableEntry, MeetingRequest

def _time_to_minutes(time_str: str) -> int:
    """Helper to convert HH:MM to minutes since midnight."""
    parts = time_str.strip().split(":")
    return int(parts[0]) * 60 + int(parts[1])

def _minutes_to_time(minutes: int) -> str:
    """Helper to convert minutes since midnight to HH:MM."""
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

def get_timetable(student_id: int, day_of_week: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves timetable for a specific day or entire week."""
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    with get_db() as db:
        query = db.query(TimetableEntry).filter(TimetableEntry.student_id == student_id)
        if day_of_week:
            query = query.filter(TimetableEntry.day_of_week.ilike(day_of_week.strip()))
        
        entries = query.all()
        # Sort by day and start time
        entries_dict = [e.to_dict() for e in entries]
        entries_dict.sort(key=lambda x: (
            days_order.index(x["day_of_week"]) if x["day_of_week"] in days_order else 99,
            _time_to_minutes(x["start_time"])
        ))

        return {
            "success": True,
            "student_id": student_id,
            "filter_day": day_of_week,
            "count": len(entries_dict),
            "entries": entries_dict
        }

def check_schedule_conflicts(
    student_id: int,
    target_day: str,
    start_time: str,
    end_time: str
) -> Dict[str, Any]:
    """
    Checks if a proposed time slot conflicts with scheduled classes or approved meetings.
    Two intervals [A_start, A_end] and [B_start, B_end] overlap if:
        max(A_start, B_start) < min(A_end, B_end)
    """
    try:
        req_start = _time_to_minutes(start_time)
        req_end = _time_to_minutes(end_time)
        if req_start >= req_end:
            return {"has_conflict": True, "error": "End time must be after start time."}
    except Exception as e:
        return {"has_conflict": True, "error": f"Invalid time format (use HH:MM): {str(e)}"}

    with get_db() as db:
        # 1. Check classes on that day
        classes = db.query(TimetableEntry).filter(
            TimetableEntry.student_id == student_id,
            TimetableEntry.day_of_week.ilike(target_day.strip())
        ).all()

        conflicts = []
        for c in classes:
            c_start = _time_to_minutes(c.start_time)
            c_end = _time_to_minutes(c.end_time)
            if max(req_start, c_start) < min(req_end, c_end):
                conflicts.append({
                    "type": "Class Conflict",
                    "subject": c.subject.name if c.subject else "Class",
                    "time": f"{c.start_time} - {c.end_time}",
                    "classroom": c.classroom
                })

        return {
            "has_conflict": len(conflicts) > 0,
            "conflict_count": len(conflicts),
            "conflicts": conflicts
        }

def get_available_slots(
    student_id: int,
    day_of_week: str,
    start_window: str = "08:00",
    end_window: str = "20:00"
) -> Dict[str, Any]:
    """
    Finds open time slots where no classes or meetings are scheduled.
    Useful for autonomous study plan scheduling.
    """
    tt_result = get_timetable(student_id, day_of_week)
    entries = tt_result.get("entries", [])

    busy_intervals = []
    for e in entries:
        busy_intervals.append((_time_to_minutes(e["start_time"]), _time_to_minutes(e["end_time"])))

    busy_intervals.sort(key=lambda x: x[0])

    # Merge overlapping or touching busy intervals
    merged_busy = []
    for interval in busy_intervals:
        if not merged_busy:
            merged_busy.append(interval)
        else:
            prev_start, prev_end = merged_busy[-1]
            if interval[0] <= prev_end:
                merged_busy[-1] = (prev_start, max(prev_end, interval[1]))
            else:
                merged_busy.append(interval)

    window_start = _time_to_minutes(start_window)
    window_end = _time_to_minutes(end_window)

    free_slots = []
    curr = window_start

    for b_start, b_end in merged_busy:
        if b_start > curr:
            slot_duration = b_start - curr
            if slot_duration >= 30:  # Minimum 30 min slot
                free_slots.append({
                    "start_time": _minutes_to_time(curr),
                    "end_time": _minutes_to_time(b_start),
                    "duration_minutes": slot_duration
                })
        curr = max(curr, b_end)

    if curr < window_end:
        slot_duration = window_end - curr
        if slot_duration >= 30:
            free_slots.append({
                "start_time": _minutes_to_time(curr),
                "end_time": _minutes_to_time(window_end),
                "duration_minutes": slot_duration
            })

    return {
        "success": True,
        "day": day_of_week,
        "window": f"{start_window} to {end_window}",
        "available_slots": free_slots
    }
