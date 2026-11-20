import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.db import get_db, init_db
from database.models import Student, Subject, Teacher, Task, AttendanceRecord, Examination, MeetingRequest
from database.seed import seed_database

def test_database_models_and_persistence():
    init_db()
    seed_database()

    with get_db() as db:
        # Check student records exist
        students = db.query(Student).all()
        assert len(students) >= 1, "Students table should contain seeded records"
        s1 = students[0]
        assert s1.name == "Aarav Sharma"
        assert s1.roll_no == "CS21B101"

        # Check teachers
        teachers = db.query(Teacher).all()
        assert len(teachers) >= 5, "Teachers table should contain at least 5 faculty members"

        # Check subjects
        subjects = db.query(Subject).all()
        assert len(subjects) >= 5, "Subjects table should contain at least 5 courses"

        # Check attendance records
        att_recs = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == s1.id).all()
        assert len(att_recs) >= 30, "Attendance records should be populated"

        # Check examinations
        exams = db.query(Examination).filter(Examination.student_id == s1.id).all()
        assert len(exams) >= 1, "Exams should be logged for student"

        # Check student isolation
        s2 = db.query(Student).filter(Student.id == 2).first()
        if s2:
            s1_tasks = db.query(Task).filter(Task.student_id == s1.id).all()
            for t in s1_tasks:
                assert t.student_id == s1.id, "Tasks must be strictly isolated to student"

    print("✅ test_database_models_and_persistence passed!")

if __name__ == "__main__":
    test_database_models_and_persistence()
