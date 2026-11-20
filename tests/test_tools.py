import sys
import datetime
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.task_tools import add_task, get_tasks, update_task, delete_task
from tools.attendance_tools import calculate_attendance, calculate_classes_needed, get_attendance, get_attendance_alerts
from tools.timetable_tools import check_schedule_conflicts, get_available_slots
from tools.meeting_tools import request_meeting, get_teachers
from tools.notification_tools import create_notification, get_notifications

def test_task_tools_crud():
    student_id = 1
    # 1. Add Task
    add_res = add_task(
        student_id=student_id,
        title="Unit Test Task",
        due_date=str(datetime.date.today() + datetime.timedelta(days=2)),
        description="Testing task tools",
        priority="High"
    )
    assert add_res["success"] is True, f"Add task failed: {add_res}"
    task_id = add_res["task"]["id"]

    # 2. Get Tasks
    get_res = get_tasks(student_id=student_id)
    assert get_res["success"] is True
    found = any(t["id"] == task_id for t in get_res["tasks"])
    assert found is True, "Created task should appear in get_tasks"

    # 3. Update Task
    up_res = update_task(task_id=task_id, student_id=student_id, status="Completed")
    assert up_res["success"] is True
    assert up_res["task"]["status"] == "Completed"

    # 4. Delete Task
    del_res = delete_task(task_id=task_id, student_id=student_id)
    assert del_res["success"] is True
    print("✅ test_task_tools_crud passed!")

def test_attendance_math_and_alerts():
    # Formula test
    assert calculate_attendance(24, 30) == 80.0
    assert calculate_attendance(20, 30) == 66.67
    assert calculate_attendance(0, 0) == 0.0

    # Needed classes formula test
    # If 20 attended out of 30, target 75%:
    # (20 + x) / (30 + x) >= 0.75 => x >= (0.75*30 - 20) / (0.25) = (22.5 - 20) / 0.25 = 2.5 / 0.25 = 10 classes
    needed_res = calculate_classes_needed(20, 30, 75.0)
    assert needed_res["possible"] is True
    assert needed_res["needed"] == 10, f"Expected 10 classes needed, got {needed_res['needed']}"

    # Alerts test on student 1
    alerts_res = get_attendance_alerts(student_id=1)
    assert alerts_res["success"] is True
    assert alerts_res["has_alerts"] is True, "Student 1 should have attendance alert for CS503"
    print("✅ test_attendance_math_and_alerts passed!")

def test_timetable_and_meeting_conflicts():
    student_id = 1
    # Check conflict detection
    # On Monday, Aarav has CS501 from 09:00 to 10:00
    conflict = check_schedule_conflicts(student_id, "Monday", "09:30", "10:30")
    assert conflict["has_conflict"] is True, "Overlap with 09:00-10:00 class must be detected"

    # Check non-conflict
    free_slot = check_schedule_conflicts(student_id, "Monday", "18:00", "19:00")
    assert free_slot["has_conflict"] is False, "18:00 slot should be completely free"

    # Available slot finder
    slots = get_available_slots(student_id, "Monday", "08:00", "18:00")
    assert slots["success"] is True
    assert len(slots["available_slots"]) > 0

    print("✅ test_timetable_and_meeting_conflicts passed!")

if __name__ == "__main__":
    test_task_tools_crud()
    test_attendance_math_and_alerts()
    test_timetable_and_meeting_conflicts()
