import datetime
from typing import Dict, Any, Optional
from tools.task_tools import add_task, get_tasks, update_task, delete_task

class TaskAgent:
    """Specialized agent responsible for academic task and assignment lifecycle."""

    def __init__(self, student_id: int):
        self.student_id = student_id
        self.agent_name = "TASK_AGENT"

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches requested task action to appropriate tool."""
        act = action.lower()
        if act in ["add", "create"]:
            title = params.get("title", "Untitled Task")
            due_date = params.get("due_date", str(datetime.date.today() + datetime.timedelta(days=3)))
            desc = params.get("description", "")
            subject_id = params.get("subject_id")
            priority = params.get("priority", "Medium")
            res = add_task(self.student_id, title=title, due_date=due_date, description=desc, subject_id=subject_id, priority=priority)
            return {"agent": self.agent_name, "action": act, "result": res}

        elif act in ["get", "list", "retrieve"]:
            status = params.get("status")
            subject_id = params.get("subject_id")
            sort_by = params.get("sort_by", "due_date")
            res = get_tasks(self.student_id, status=status, subject_id=subject_id, sort_by=sort_by)
            return {"agent": self.agent_name, "action": act, "result": res}

        elif act in ["update", "edit", "complete"]:
            task_id = params.get("task_id")
            if not task_id:
                return {"agent": self.agent_name, "success": False, "error": "task_id is required for update."}
            res = update_task(
                task_id=task_id,
                student_id=self.student_id,
                title=params.get("title"),
                description=params.get("description"),
                priority=params.get("priority"),
                due_date=params.get("due_date"),
                status=params.get("status")
            )
            return {"agent": self.agent_name, "action": act, "result": res}

        elif act in ["delete", "remove"]:
            task_id = params.get("task_id")
            if not task_id:
                return {"agent": self.agent_name, "success": False, "error": "task_id is required for deletion."}
            res = delete_task(task_id=task_id, student_id=self.student_id)
            return {"agent": self.agent_name, "action": act, "result": res}

        else:
            # Default: list pending tasks
            res = get_tasks(self.student_id, status="Pending")
            return {"agent": self.agent_name, "action": "list_default", "result": res}
