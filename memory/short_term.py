from typing import List, Dict, Any, Optional

class ShortTermMemory:
    """
    Manages in-session conversation history, intermediate tool results,
    and active agent execution traces.
    """
    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self.messages: List[Dict[str, str]] = []
        self.current_intent: Optional[str] = None
        self.execution_trace: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str):
        """Appends a turn to dialogue history."""
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]

    def get_context_history(self) -> List[Dict[str, str]]:
        """Returns message list suitable for chat prompt."""
        return list(self.messages)

    def log_agent_action(self, agent_name: str, action: str, output: Any):
        """Records an intermediate step taken by a specialized agent."""
        self.execution_trace.append({
            "agent": agent_name,
            "action": action,
            "output": output
        })

    def get_latest_trace(self) -> List[Dict[str, Any]]:
        return list(self.execution_trace)

    def clear(self):
        self.messages.clear()
        self.execution_trace.clear()
        self.current_intent = None
