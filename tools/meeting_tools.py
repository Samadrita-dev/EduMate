import datetime
from typing import Optional, List, Dict, Any
from database.db import get_db
from database.models import MeetingRequest, Teacher, Student, TimetableEntry
from tools.timetable_tools import check_schedule_conflicts

def get_teachers(
    department: Optional[str] = None,
    search_query: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieves teacher directory with optional filtering and search."""
    with get_db() as db:
        query = db.query(Teacher)
        if department:
            query = query.filter(Teacher.department.ilike(f"%{department.strip()}%"))
        if search_query:
            term = f"%{search_query.strip()}%"
            query = query.filter((Teacher.name.ilike(term)) | (Teacher.designation.ilike(term)))

        teachers = query.order_by(Teacher.name.asc()).all()
        return {
            "success": True,
            "count": len(teachers),
            "teachers": [t.to_dict() for t in teachers]
        }

def request_meeting(
    student_id: int,
    teacher_id: int,
    purpose: str,
    requested_date: str,
    requested_time: str
) -> Dict[str, Any]:
    """
    Submits a meeting request after conflict validation.
    The meeting is marked strictly as 'Pending' until explicitly confirmed.
    """
    if not purpose or not purpose.strip():
        return {"success": False, "error": "Meeting purpose is required."}

    try:
        req_date = datetime.date.fromisoformat(requested_date.strip())
        if req_date < datetime.date.today():
            return {"success": False, "error": "Cannot schedule a meeting in the past."}
    except Exception as e:
        return {"success": False, "error": f"Invalid date format (use YYYY-MM-DD): {str(e)}"}

    try:
        parts = requested_time.strip().split(":")
        start_hour = int(parts[0])
        start_min = int(parts[1])
        # Meeting length assumed 30 minutes for conflict checking
        end_min_total = start_hour * 60 + start_min + 30
        end_time_str = f"{end_min_total // 60:02d}:{end_min_total % 60:02d}"
    except Exception:
        return {"success": False, "error": "Invalid time format (use HH:MM)."}

    with get_db() as db:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {"success": False, "error": f"Student #{student_id} not found."}

        teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
        if not teacher:
            return {"success": False, "error": f"Teacher #{teacher_id} not found."}

        # Check timetable conflict on the day of week corresponding to requested_date
        day_of_week = req_date.strftime("%A")
        conflict_res = check_schedule_conflicts(student_id, day_of_week, requested_time.strip(), end_time_str)
        if conflict_res.get("has_conflict"):
            conflicts = conflict_res.get("conflicts", [])
            desc = ", ".join([f"{c['subject']} ({c['time']})" for c in conflicts])
            return {
                "success": False,
                "error": f"Schedule conflict detected on {day_of_week}: Student has {desc}."
            }

        meeting = MeetingRequest(
            student_id=student_id,
            teacher_id=teacher_id,
            purpose=purpose.strip(),
            requested_date=req_date,
            requested_time=requested_time.strip(),
            status="Pending"  # Strict requirement: pending until authorized approval
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        return {
            "success": True,
            "message": f"Meeting request submitted successfully for {teacher.name}. Status: Pending Faculty Approval.",
            "meeting": meeting.to_dict()
        }

def get_meeting_status(student_id: int, status: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves all meeting requests for a student."""
    with get_db() as db:
        query = db.query(MeetingRequest).filter(MeetingRequest.student_id == student_id)
        if status:
            query = query.filter(MeetingRequest.status.ilike(status.strip()))

        meetings = query.order_by(MeetingRequest.requested_date.desc()).all()
        return {
            "success": True,
            "count": len(meetings),
            "meetings": [m.to_dict() for m in meetings]
        }

def update_meeting_status(
    meeting_id: int,
    status: str,
    teacher_notes: Optional[str] = None
) -> Dict[str, Any]:
    """Updates status of a meeting request (e.g. Approved, Rejected, Completed)."""
    valid = ["Pending", "Approved", "Rejected", "Completed"]
    matched = next((s for s in valid if s.lower() == status.strip().lower()), None)
    if not matched:
        return {"success": False, "error": f"Invalid status. Must be one of {valid}."}

    with get_db() as db:
        meeting = db.query(MeetingRequest).filter(MeetingRequest.id == meeting_id).first()
        if not meeting:
            return {"success": False, "error": f"Meeting request #{meeting_id} not found."}

        meeting.status = matched
        if teacher_notes is not None:
            meeting.teacher_notes = teacher_notes.strip()
        db.commit()
        return {"success": True, "message": f"Meeting #{meeting_id} status updated to {matched}."}
