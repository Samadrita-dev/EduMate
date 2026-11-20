import datetime
from typing import Optional, List, Dict, Any
from database.db import get_db
from database.models import Task, Subject, Student

def add_task(
    student_id: int,
    title: str,
    due_date: str,
    description: str = "",
    subject_id: Optional[int] = None,
    priority: str = "Medium"
) -> Dict[str, Any]:
    """Adds a new task for a student after validating inputs."""
    if not title or not title.strip():
        return {"success": False, "error": "Task title cannot be empty."}
    
    priority = priority.capitalize()
    if priority not in ["High", "Medium", "Low"]:
        priority = "Medium"

    try:
        if isinstance(due_date, str):
            parsed_date = datetime.date.fromisoformat(due_date.strip())
        elif isinstance(due_date, datetime.date):
            parsed_date = due_date
        else:
            return {"success": False, "error": "Invalid date format. Expected YYYY-MM-DD."}
    except Exception as e:
        return {"success": False, "error": f"Invalid due date: {str(e)}"}

    with get_db() as db:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {"success": False, "error": f"Student with ID {student_id} not found."}

        if subject_id:
            subj = db.query(Subject).filter(Subject.id == subject_id).first()
            if not subj:
                return {"success": False, "error": f"Subject with ID {subject_id} not found."}

        task = Task(
            student_id=student_id,
            title=title.strip(),
            description=description.strip() if description else "",
            subject_id=subject_id,
            priority=priority,
            due_date=parsed_date,
            status="Pending"
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return {"success": True, "message": "Task created successfully.", "task": task.to_dict()}

def get_tasks(
    student_id: int,
    status: Optional[str] = None,
    subject_id: Optional[int] = None,
    sort_by: str = "due_date"
) -> Dict[str, Any]:
    """Retrieves tasks for a student with filtering and sorting."""
    with get_db() as db:
        query = db.query(Task).filter(Task.student_id == student_id)
        if status:
            query = query.filter(Task.status.ilike(status))
        if subject_id:
            query = query.filter(Task.subject_id == subject_id)

        if sort_by == "priority":
            # Sort High -> Medium -> Low
            tasks = query.all()
            priority_order = {"High": 1, "Medium": 2, "Low": 3}
            tasks.sort(key=lambda t: (priority_order.get(t.priority, 4), t.due_date))
        else:
            tasks = query.order_by(Task.due_date.asc()).all()

        today = datetime.date.today()
        task_list = []
        for t in tasks:
            d = t.to_dict()
            # Dynamic check for overdue
            if t.status == "Pending" and t.due_date < today:
                d["is_overdue"] = True
            else:
                d["is_overdue"] = False
            task_list.append(d)

        return {"success": True, "count": len(task_list), "tasks": task_list}

def update_task(
    task_id: int,
    student_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    status: Optional[str] = None,
    subject_id: Optional[int] = None
) -> Dict[str, Any]:
    """Updates an existing task with ownership verification."""
    with get_db() as db:
        task = db.query(Task).filter(Task.id == task_id, Task.student_id == student_id).first()
        if not task:
            return {"success": False, "error": f"Task #{task_id} not found or does not belong to student #{student_id}."}

        if title is not None:
            task.title = title.strip()
        if description is not None:
            task.description = description.strip()
        if priority is not None:
            p = priority.capitalize()
            if p in ["High", "Medium", "Low"]:
                task.priority = p
        if due_date is not None:
            try:
                task.due_date = datetime.date.fromisoformat(due_date.strip())
            except Exception:
                return {"success": False, "error": "Invalid date format. Expected YYYY-MM-DD."}
        if status is not None:
            s = status.capitalize()
            if s in ["Pending", "Completed", "Overdue"]:
                task.status = s
        if subject_id is not None:
            task.subject_id = subject_id

        task.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(task)
        return {"success": True, "message": "Task updated successfully.", "task": task.to_dict()}

def delete_task(task_id: int, student_id: int) -> Dict[str, Any]:
    """Deletes a task with ownership verification."""
    with get_db() as db:
        task = db.query(Task).filter(Task.id == task_id, Task.student_id == student_id).first()
        if not task:
            return {"success": False, "error": f"Task #{task_id} not found or does not belong to student #{student_id}."}
        db.delete(task)
        db.commit()
        return {"success": True, "message": f"Task #{task_id} deleted successfully."}
