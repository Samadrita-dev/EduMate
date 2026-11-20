import datetime
import json
from typing import Dict, Any

from database.db import get_db
from database.models import Examination, StudyPlan
from sqlalchemy.orm import joinedload


def get_exams(student_id: int, upcoming_only: bool = True) -> Dict[str, Any]:
    """Retrieves examinations for a student with countdown calculation."""

    today = datetime.date.today()

    with get_db() as db :
        query = (
            db.query(Examination)
            .options(joinedload(Examination.subject))
            .filter(Examination.student_id == student_id)
        )

        if upcoming_only:
            query = query.filter(Examination.exam_date >= today)

        exams = query.order_by(Examination.exam_date.asc()).all()

        results = []

        for exam in exams:
            data = exam.to_dict()
            days_left = (exam.exam_date - today).days

            data["days_remaining"] = days_left

            if days_left < 0:
                data["urgency"] = "COMPLETED / PAST"
            elif days_left == 0:
                data["urgency"] = "TODAY"
            elif days_left <= 3:
                data["urgency"] = "CRITICAL (Under 3 Days)"
            elif days_left <= 7:
                data["urgency"] = "HIGH (This Week)"
            elif days_left <= 14:
                data["urgency"] = "MODERATE (2 Weeks)"
            else:
                data["urgency"] = "UPCOMING"

            results.append(data)

        return {
            "success": True,
            "count": len(results),
            "examinations": results
        }


def get_exam_details(exam_id: int, student_id: int) -> Dict[str, Any]:
    """Retrieves syllabus, timing, and preparation status for an exam."""

    with get_db() as db:
        exam = (
            db.query(Examination)
            .options(joinedload(Examination.subject))
            .filter(
                Examination.id == exam_id,
                Examination.student_id == student_id
            )
            .first()
        )

        if not exam:
            return {
                "success": False,
                "error": f"Exam #{exam_id} not found."
            }

        data = exam.to_dict()
        today = datetime.date.today()

        data["days_remaining"] = (exam.exam_date - today).days

        return {
            "success": True,
            "exam": data
        }


def update_exam_prep_status(
    exam_id: int,
    student_id: int,
    new_status: str
) -> Dict[str, Any]:
    """Updates preparation status for an examination."""

    valid_statuses = ["Not Started", "In Progress", "Prepared"]

    if not isinstance(new_status, str):
        return {
            "success": False,
            "error": "Status must be a valid string."
        }

    matched = next(
        (
            status for status in valid_statuses
            if status.lower() == new_status.strip().lower()
        ),
        None
    )

    if not matched:
        return {
            "success": False,
            "error": f"Invalid status. Choose from: {valid_statuses}"
        }

    with get_db() as db:
        exam = db.query(Examination).filter(
            Examination.id == exam_id,
            Examination.student_id == student_id
        ).first()

        if not exam:
            return {
                "success": False,
                "error": f"Exam #{exam_id} not found."
            }

        exam.preparation_status = matched

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        return {
            "success": True,
            "message": f"Preparation status updated to '{matched}'.",
            "exam_id": exam_id
        }


def save_study_plan_record(
    student_id: int,
    title: str,
    goal: str,
    plan_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Saves a structured study plan with Proposed status."""

    if not isinstance(plan_data, dict):
        return {
            "success": False,
            "error": "Study plan data must be a dictionary."
        }

    with get_db() as db:
        plan = StudyPlan(
            student_id=student_id,
            title=title,
            target_exam_or_goal=goal,
            plan_json=json.dumps(plan_data, indent=2),
            status="Proposed"
        )

        db.add(plan)

        try:
            db.commit()
            db.refresh(plan)

        except Exception:
            db.rollback()
            raise

        return {
            "success": True,
            "plan_id": plan.id,
            "status": "Proposed",
            "message": "Study plan proposed for review."
        }
