import math
from typing import Optional, List, Dict, Any
from database.db import get_db
from database.models import AttendanceRecord, Subject, Student
from config import DEFAULT_ATTENDANCE_REQUIREMENT

def calculate_attendance(classes_attended: int, total_classes: int) -> float:
    """Calculates attendance percentage strictly using standard academic formula."""
    if total_classes <= 0:
        return 0.0
    return round((classes_attended / total_classes) * 100.0, 2)

def calculate_classes_needed(
    classes_attended: int,
    total_classes: int,
    target_percentage: float = DEFAULT_ATTENDANCE_REQUIREMENT
) -> Dict[str, Any]:
    """
    Calculates number of additional consecutive classes required to reach target percentage.
    Formula:
        (attended + x) / (total + x) >= target / 100
        x * (100 - target) >= (target * total) - (100 * attended)
        x = ceil( (target * total - 100 * attended) / (100 - target) )
    """
    if target_percentage >= 100.0:
        return {
            "needed": None,
            "possible": False,
            "message": "Target 100% attendance is mathematically impossible if any class was missed."
        }

    current_pct = calculate_attendance(classes_attended, total_classes)
    if current_pct >= target_percentage:
        # Can calculate how many classes can safely be skipped while maintaining threshold!
        # (attended) / (total + y) >= target / 100 => y <= (100 * attended - target * total) / target
        safe_skips = math.floor((100 * classes_attended - target_percentage * total_classes) / target_percentage)
        return {
            "needed": 0,
            "possible": True,
            "current_percentage": current_pct,
            "target_percentage": target_percentage,
            "safe_skips_allowed": max(0, safe_skips),
            "status": "Target already met or exceeded."
        }

    numerator = (target_percentage * total_classes) - (100.0 * classes_attended)
    denominator = 100.0 - target_percentage

    if denominator <= 0:
        return {"needed": None, "possible": False, "message": "Invalid target percentage."}

    classes_needed = math.ceil(numerator / denominator)
    return {
        "needed": max(0, classes_needed),
        "possible": True,
        "current_percentage": current_pct,
        "target_percentage": target_percentage,
        "new_total_classes": total_classes + classes_needed,
        "new_attended_classes": classes_attended + classes_needed,
        "projected_percentage": calculate_attendance(classes_attended + classes_needed, total_classes + classes_needed),
        "message": f"Must attend next {classes_needed} consecutive classes without absence to achieve {target_percentage}%."
    }

def get_attendance(student_id: int, subject_id: Optional[int] = None) -> Dict[str, Any]:
    """Retrieves subject-wise official attendance metrics and student summary."""
    with get_db() as db:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {"success": False, "error": f"Student with ID {student_id} not found."}

        subjects_query = db.query(Subject)
        if subject_id:
            subjects_query = subjects_query.filter(Subject.id == subject_id)
        subjects = subjects_query.all()

        results = []
        overall_attended = 0
        overall_total = 0

        for sub in subjects:
            records = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.subject_id == sub.id
            ).all()

            total_sessions = len(records)
            attended_sessions = sum(1 for r in records if r.status in ["Present", "Excused"])
            pct = calculate_attendance(attended_sessions, total_sessions)
            needed_calc = calculate_classes_needed(attended_sessions, total_sessions, DEFAULT_ATTENDANCE_REQUIREMENT)

            overall_attended += attended_sessions
            overall_total += total_sessions

            status_flag = "Critical" if pct < 65.0 else ("Warning" if pct < DEFAULT_ATTENDANCE_REQUIREMENT else "Good")

            results.append({
                "subject_id": sub.id,
                "subject_code": sub.code,
                "subject_name": sub.name,
                "faculty_name": sub.teacher.name if sub.teacher else "Faculty",
                "total_classes": total_sessions,
                "classes_attended": attended_sessions,
                "classes_absent": total_sessions - attended_sessions,
                "attendance_percentage": pct,
                "status_flag": status_flag,
                "target_requirement": DEFAULT_ATTENDANCE_REQUIREMENT,
                "classes_needed_for_target": needed_calc.get("needed", 0),
                "safe_skips_allowed": needed_calc.get("safe_skips_allowed", 0),
                "analysis_note": needed_calc.get("message", "")
            })

        overall_pct = calculate_attendance(overall_attended, overall_total)

        return {
            "success": True,
            "student_id": student_id,
            "student_name": student.name,
            "overall_attendance_percentage": overall_pct,
            "overall_classes_attended": overall_attended,
            "overall_total_classes": overall_total,
            "subjects": results
        }

def get_attendance_alerts(student_id: int, threshold: float = DEFAULT_ATTENDANCE_REQUIREMENT) -> Dict[str, Any]:
    """Identifies subjects falling below the required attendance threshold."""
    att_data = get_attendance(student_id)
    if not att_data.get("success"):
        return att_data

    alerts = []
    for sub in att_data.get("subjects", []):
        if sub["attendance_percentage"] < threshold:
            alerts.append({
                "subject_code": sub["subject_code"],
                "subject_name": sub["subject_name"],
                "current_percentage": sub["attendance_percentage"],
                "threshold": threshold,
                "shortage": round(threshold - sub["attendance_percentage"], 2),
                "classes_needed": sub["classes_needed_for_target"],
                "severity": "CRITICAL (Debarment Risk)" if sub["attendance_percentage"] < 65.0 else "WARNING (Shortage)"
            })

    return {
        "success": True,
        "has_alerts": len(alerts) > 0,
        "alert_count": len(alerts),
        "alerts": alerts
    }
