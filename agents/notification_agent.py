from typing import Dict, Any, Optional
from tools.notification_tools import (
    create_notification, get_notifications, mark_notification_read, run_proactive_checks
)

class NotificationAgent:
    """Specialized agent responsible for in-app alert management and proactive warnings."""

    def __init__(self, student_id: int):
        self.student_id = student_id
        self.agent_name = "NOTIFICATION_AGENT"

    def execute(self, action: str = "get", params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params or {}
        act = action.lower()

        if act in ["create", "send"]:
            title = params.get("title", "Notice")
            msg = params.get("message", "")
            cat = params.get("category", "System")
            res = create_notification(self.student_id, title=title, message=msg, category=cat)
            return {"agent": self.agent_name, "action": act, "result": res}

        elif act in ["mark_read", "read"]:
            nid = params.get("notification_id")
            if not nid:
                return {"agent": self.agent_name, "success": False, "error": "notification_id is required."}
            res = mark_notification_read(notification_id=nid, student_id=self.student_id)
            return {"agent": self.agent_name, "action": act, "result": res}

        elif act in ["proactive_audit", "run_checks"]:
            res = run_proactive_checks(self.student_id)
            return {"agent": self.agent_name, "action": act, "result": res}

        else:
            unread_only = params.get("unread_only", False)
            res = get_notifications(self.student_id, unread_only=unread_only)
            return {"agent": self.agent_name, "action": "list_notifications", "result": res}
