import datetime
from typing import Optional, List, Dict, Any
from database.db import get_db
from database.models import Notification, Assignment, Examination, AttendanceRecord, Subject
from tools.attendance_tools import get_attendance_alerts

def create_notification(
    student_id: int,
    title: str,
    message: str,
    category: str = "System"
) -> Dict[str, Any]:
    """Creates a persistent in-app notification."""
    valid_categories = ["Exam", "Assignment", "Attendance", "Meeting", "Task", "System"]
    cat = category.capitalize()
    if cat not in valid_categories:
        cat = "System"

    with get_db() as db:
        notif = Notification(
            student_id=student_id,
            title=title.strip(),
            message=message.strip(),
            category=cat,
            is_read=False
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return {"success": True, "notification": notif.to_dict()}

def get_notifications(
    student_id: int,
    unread_only: bool = False
) -> Dict[str, Any]:
    """Retrieves notifications for a student."""
    with get_db() as db:
        query = db.query(Notification).filter(Notification.student_id == student_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)

        notifs = query.order_by(Notification.created_at.desc()).all()
        return {
            "success": True,
            "count": len(notifs),
            "unread_count": sum(1 for n in notifs if not n.is_read),
            "notifications": [n.to_dict() for n in notifs]
        }

def mark_notification_read(notification_id: int, student_id: int) -> Dict[str, Any]:
    """Marks a notification as read with ownership check."""
    with get_db() as db:
        notif = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.student_id == student_id
        ).first()

        if not notif:
            return {"success": False, "error": f"Notification #{notification_id} not found."}

        notif.is_read = True
        db.commit()
        return {"success": True, "message": "Notification marked as read."}

def run_proactive_checks(student_id: int) -> Dict[str, Any]:
    """
    Proactively audits student records and creates smart alerts:
    - Deadlines approaching within 3 days.
    - Examinations approaching within 14 days.
    - Attendance shortfalls below 75%.
    """
    alerts_generated = []
    today = datetime.date.today()

    with get_db() as db:
        # 1. Check Assignments
        assignments = db.query(Assignment).filter(
            Assignment.student_id == student_id,
            Assignment.status.in_(["Pending", "Overdue"])
        ).all()
        for a in assignments:
            days = (a.due_date - today).days
            if 0 <= days <= 3:
                # Check if already notified recently
                existing = db.query(Notification).filter(
                    Notification.student_id == student_id,
                    Notification.title.ilike(f"%{a.title}%")
                ).first()
                if not existing:
                    notif = Notification(
                        student_id=student_id,
                        title=f"Deadline Approaching: {a.title}",
                        message=f"Assignment for {a.subject.name} is due in {days} day(s) on {a.due_date}.",
                        category="Assignment"
                    )
                    db.add(notif)
                    alerts_generated.append(notif.title)

        # 2. Check Examinations
        exams = db.query(Examination).filter(
            Examination.student_id == student_id,
            Examination.exam_date >= today
        ).all()
        for e in exams:
            days = (e.exam_date - today).days
            if days <= 14:
                existing = db.query(Notification).filter(
                    Notification.student_id == student_id,
                    Notification.title.ilike(f"%Exam Alert: {e.subject.code}%")
                ).first()
                if not existing:
                    notif = Notification(
                        student_id=student_id,
                        title=f"Exam Alert: {e.subject.code} {e.exam_type}",
                        message=f"{e.exam_type} in {e.subject.name} scheduled on {e.exam_date} ({days} days remaining). Prep status: {e.preparation_status}.",
                        category="Exam"
                    )
                    db.add(notif)
                    alerts_generated.append(notif.title)

        # 3. Check Attendance alerts
        att_alerts = get_attendance_alerts(student_id)
        if att_alerts.get("has_alerts"):
            for al in att_alerts.get("alerts", []):
                existing = db.query(Notification).filter(
                    Notification.student_id == student_id,
                    Notification.title.ilike(f"%Attendance Warning: {al['subject_code']}%")
                ).first()
                if not existing:
                    notif = Notification(
                        student_id=student_id,
                        title=f"Attendance Warning: {al['subject_code']}",
                        message=f"Attendance in {al['subject_name']} is {al['current_percentage']}%. Must attend next {al['classes_needed']} consecutive classes to reach 75%.",
                        category="Attendance"
                    )
                    db.add(notif)
                    alerts_generated.append(notif.title)

        db.commit()

    return {
        "success": True,
        "new_alerts_count": len(alerts_generated),
        "alerts_generated": alerts_generated
    }
