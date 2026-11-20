from typing import Dict, Any, Optional
from graph.workflow import edumate_graph
from graph.state import EduMateState

class CoordinatorAgent:
    """
    Central Coordinator Interface managing state orchestration,
    intent execution, and human-in-the-loop approvals.
    """
    def __init__(self, student_id: int = 1):
        self.student_id = student_id

    def run(
        self,
        query: str,
        approval_status: Optional[str] = None,
        pending_approval: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Runs the LangGraph workflow with input state."""
        initial_state: EduMateState = {
            "student_id": self.student_id,
            "user_query": query,
            "intent": "general",
            "target_agents": [],
            "plan_steps": [],
            "agent_outputs": {},
            "retrieved_evidence": [],
            "student_preferences": "",
            "episodic_context": "",
            "pending_approval": pending_approval,
            "approval_status": approval_status,
            "final_response": "",
            "execution_trace": [],
            "requires_human_approval": False,
            "completed": False
        }

        try:
            final_state = edumate_graph.invoke(initial_state)
            return {
                "success": True,
                "response": final_state.get("final_response", ""),
                "intent": final_state.get("intent", ""),
                "target_agents": final_state.get("target_agents", []),
                "plan_steps": final_state.get("plan_steps", []),
                "agent_outputs": final_state.get("agent_outputs", {}),
                "pending_approval": final_state.get("pending_approval"),
                "requires_human_approval": final_state.get("requires_human_approval", False),
                "execution_trace": final_state.get("execution_trace", []),
                "retrieved_evidence": final_state.get("retrieved_evidence", [])
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"Encountered an issue processing your request: {str(e)}",
                "execution_trace": []
            }
