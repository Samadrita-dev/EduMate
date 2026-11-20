import sys
import datetime
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from llm.client import OllamaClient
from tools.task_tools import add_task, update_task
from tools.meeting_tools import request_meeting
from tools.attendance_tools import get_attendance
from rag.retriever import DocumentRetriever

def test_ollama_unavailable_fallback():
    # Simulate unavailable port
    client = OllamaClient(base_url="http://localhost:9999")
    status = client.check_connection()
    assert status["available"] is False
    assert "not running" in status["message"] or "error" in status

    # Verify fallback intent parsing still works without error
    intent_res = client.parse_intent("Show my timetable for tomorrow")
    assert intent_res["intent"] == "timetable"
    assert "TIMETABLE_AGENT" in intent_res["target_agents"]
    print("✅ test_ollama_unavailable_fallback passed!")

def test_invalid_student_id():
    res = get_attendance(student_id=999999)
    assert res["success"] is False
    assert "not found" in res["error"].lower()
    print("✅ test_invalid_student_id passed!")

def test_invalid_task_inputs():
    # Empty title
    res1 = add_task(student_id=1, title="", due_date="2026-12-01")
    assert res1["success"] is False

    # Invalid date
    res2 = add_task(student_id=1, title="Test Task", due_date="not-a-date")
    assert res2["success"] is False

    # Non-existent task update
    res3 = update_task(task_id=999999, student_id=1, status="Completed")
    assert res3["success"] is False
    print("✅ test_invalid_task_inputs passed!")

def test_conflicting_and_invalid_meeting_requests():
    # Past date
    res1 = request_meeting(
        student_id=1,
        teacher_id=1,
        purpose="Test meeting",
        requested_date="2020-01-01",
        requested_time="10:00"
    )
    assert res1["success"] is False
    assert "past" in res1["error"].lower()

    # Invalid time format
    res2 = request_meeting(
        student_id=1,
        teacher_id=1,
        purpose="Test meeting",
        requested_date=str(datetime.date.today() + datetime.timedelta(days=2)),
        requested_time="invalid_time"
    )
    assert res2["success"] is False

    print("✅ test_conflicting_and_invalid_meeting_requests passed!")

def test_missing_document_handling():
    retriever = DocumentRetriever()
    res = retriever.retrieve_document_content("non_existent_document_xyz.txt")
    assert res["success"] is False
    assert "does not exist" in res["error"]
    print("✅ test_missing_document_handling passed!")

if __name__ == "__main__":
    test_ollama_unavailable_fallback()
    test_invalid_student_id()
    test_invalid_task_inputs()
    test_conflicting_and_invalid_meeting_requests()
    test_missing_document_handling()
