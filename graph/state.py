from typing import TypedDict, List, Dict, Any, Optional

class EduMateState(TypedDict, total=False):
    """
    Central shared state passed between all specialized agents in the LangGraph workflow.
    """
    student_id: int
    user_query: str
    intent: str
    target_agents: List[str]
    plan_steps: List[str]
    agent_outputs: Dict[str, Any]
    retrieved_evidence: List[Dict[str, Any]]
    student_preferences: str
    episodic_context: str
    pending_approval: Optional[Dict[str, Any]]
    approval_status: Optional[str]  # 'approved', 'rejected', 'edited', None
    final_response: str
    execution_trace: List[Dict[str, Any]]
    requires_human_approval: bool
    completed: bool
