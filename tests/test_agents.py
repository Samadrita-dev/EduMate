import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from agents.coordinator import CoordinatorAgent
from agents.task_agent import TaskAgent
from agents.attendance_agent import AttendanceAgent
from agents.timetable_agent import TimetableAgent
from agents.exam_agent import ExamAgent
from agents.meeting_agent import MeetingAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.notification_agent import NotificationAgent

def test_specialized_agents():
    student_id = 1

    # Task Agent
    ta = TaskAgent(student_id)
    t_res = ta.execute("get", {})
    assert t_res["agent"] == "TASK_AGENT"
    assert t_res["result"]["success"] is True

    # Attendance Agent
    aa = AttendanceAgent(student_id)
    a_res = aa.execute("summary")
    assert a_res["agent"] == "ATTENDANCE_AGENT"
    assert a_res["result"]["success"] is True

    # Timetable Agent
    tta = TimetableAgent(student_id)
    tt_res = tta.execute("get", {"day": "Monday"})
    assert tt_res["agent"] == "TIMETABLE_AGENT"
    assert tt_res["result"]["success"] is True

    # Exam Agent
    ea = ExamAgent(student_id)
    e_res = ea.execute("get")
    assert e_res["agent"] == "EXAM_AGENT"
    assert e_res["result"]["success"] is True

    # Meeting Agent
    ma = MeetingAgent(student_id)
    m_res = ma.execute("teachers")
    assert m_res["agent"] == "MEETING_AGENT"
    assert m_res["result"]["success"] is True

    # Knowledge Agent
    ka = KnowledgeAgent()
    k_res = ka.execute("search", {"query": "attendance", "top_k": 2})
    assert k_res["agent"] == "KNOWLEDGE_AGENT"
    assert "result" in k_res

    # Notification Agent
    na = NotificationAgent(student_id)
    n_res = na.execute("get")
    assert n_res["agent"] == "NOTIFICATION_AGENT"
    assert n_res["result"]["success"] is True

    print("✅ test_specialized_agents passed!")

def test_multi_agent_coordination_and_approval():
    coord = CoordinatorAgent(student_id=1)
    
    # 1. Attendance query
    res1 = coord.run("What is my current attendance?")
    assert res1["success"] is True
    assert res1["intent"] == "attendance"
    assert "ATTENDANCE_AGENT" in res1["target_agents"]

    # 2. Multi-agent study plan query requiring Human-in-the-loop approval
    res2 = coord.run("Help me plan my study schedule for upcoming exams.")
    assert res2["success"] is True
    assert res2["intent"] == "study_plan"
    assert res2["requires_human_approval"] is True
    assert res2["pending_approval"] is not None
    assert res2["pending_approval"]["action_type"] == "STUDY_PLAN"

    # 3. Simulate Human Approval
    res3 = coord.run(
        query="Confirm",
        approval_status="approved",
        pending_approval=res2["pending_approval"]
    )
    assert res3["success"] is True

    print("✅ test_multi_agent_coordination_and_approval passed!")

if __name__ == "__main__":
    test_specialized_agents()
    test_multi_agent_coordination_and_approval()
