import sys
import datetime
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.db import get_db, init_db
from database.models import (
    Student, Teacher, Subject, AttendanceRecord, TimetableEntry,
    Task, Assignment, Examination, MeetingRequest, Notification,
    MemoryItem, StudyPlan
)

def seed_database():
    """Seeds database with realistic initial data."""
    init_db()

    with get_db() as db:
        # Check if already seeded
        if db.query(Student).count() > 0:
            print("Database already contains data. Skipping seeding.")
            return

        print("Seeding database with realistic student, teacher, and academic records...")

        # 1. Teachers
        t1 = Teacher(
            name="Dr. Rajesh Sharma",
            department="Computer Science & Engineering",
            designation="Professor & HOD",
            email="rajesh.sharma@college.edu",
            office_hours="Tue & Thu 3:00 PM - 5:00 PM",
            room_no="Faculty Block C, Room 302"
        )
        t2 = Teacher(
            name="Prof. Ananya Roy",
            department="Computer Science & Engineering",
            designation="Associate Professor",
            email="ananya.roy@college.edu",
            office_hours="Mon & Wed 2:00 PM - 4:00 PM",
            room_no="Faculty Block C, Room 305"
        )
        t3 = Teacher(
            name="Dr. Vikram Malhotra",
            department="Computer Science & Engineering",
            designation="Associate Professor",
            email="vikram.malhotra@college.edu",
            office_hours="Mon & Fri 10:00 AM - 12:00 PM",
            room_no="Faculty Block B, Room 208"
        )
        t4 = Teacher(
            name="Dr. Sneha Kulkarni",
            department="Computer Science & Engineering",
            designation="Assistant Professor",
            email="sneha.kulkarni@college.edu",
            office_hours="Wed & Fri 3:00 PM - 5:00 PM",
            room_no="Faculty Block D, Room 401"
        )
        t5 = Teacher(
            name="Prof. David Miller",
            department="Computer Science & Engineering",
            designation="Assistant Professor",
            email="david.miller@college.edu",
            office_hours="Tue & Thu 11:00 AM - 1:00 PM",
            room_no="Faculty Block B, Room 210"
        )
        db.add_all([t1, t2, t3, t4, t5])
        db.flush()

        # 2. Students
        s1 = Student(
            roll_no="CS21B101",
            name="Aarav Sharma",
            email="aarav.cs21@college.edu",
            department="Computer Science & Engineering",
            semester=5,
            cgpa=8.65
        )
        s2 = Student(
            roll_no="CS21B102",
            name="Priya Patel",
            email="priya.cs21@college.edu",
            department="Computer Science & Engineering",
            semester=5,
            cgpa=9.12
        )
        s3 = Student(
            roll_no="CS21B103",
            name="Rohan Verma",
            email="rohan.cs21@college.edu",
            department="Computer Science & Engineering",
            semester=5,
            cgpa=7.45
        )
        db.add_all([s1, s2, s3])
        db.flush()

        # 3. Subjects
        sub1 = Subject(code="CS501", name="Operating Systems", department="CSE", semester=5, credits=4, teacher_id=t1.id)
        sub2 = Subject(code="CS502", name="Database Management Systems", department="CSE", semester=5, credits=4, teacher_id=t2.id)
        sub3 = Subject(code="CS503", name="Computer Networks", department="CSE", semester=5, credits=4, teacher_id=t3.id)
        sub4 = Subject(code="CS504", name="Artificial Intelligence & ML", department="CSE", semester=5, credits=3, teacher_id=t4.id)
        sub5 = Subject(code="CS505", name="Software Engineering", department="CSE", semester=5, credits=3, teacher_id=t5.id)
        db.add_all([sub1, sub2, sub3, sub4, sub5])
        db.flush()

        today = datetime.date.today()

        # 4. Timetable Entries for Aarav Sharma (s1)
        # Monday to Friday schedule
        timetable_data = [
            # Monday
            (s1.id, sub1.id, t1.id, "Monday", "09:00", "10:00", "Lecture Hall 101"),
            (s1.id, sub2.id, t2.id, "Monday", "10:15", "11:15", "Lecture Hall 101"),
            (s1.id, sub3.id, t3.id, "Monday", "11:30", "12:30", "Network Lab 2"),
            (s1.id, sub4.id, t4.id, "Monday", "14:00", "15:00", "AI Lab 1"),
            # Tuesday
            (s1.id, sub5.id, t5.id, "Tuesday", "09:00", "10:00", "Lecture Hall 102"),
            (s1.id, sub1.id, t1.id, "Tuesday", "10:15", "11:15", "OS Lab"),
            (s1.id, sub3.id, t3.id, "Tuesday", "13:30", "14:30", "Lecture Hall 101"),
            # Wednesday
            (s1.id, sub2.id, t2.id, "Wednesday", "09:00", "10:00", "DBMS Lab"),
            (s1.id, sub4.id, t4.id, "Wednesday", "10:15", "11:15", "Lecture Hall 101"),
            (s1.id, sub5.id, t5.id, "Wednesday", "11:30", "12:30", "Lecture Hall 102"),
            (s1.id, sub1.id, t1.id, "Wednesday", "15:00", "16:00", "Lecture Hall 101"),
            # Thursday
            (s1.id, sub3.id, t3.id, "Thursday", "09:00", "10:00", "Lecture Hall 101"),
            (s1.id, sub2.id, t2.id, "Thursday", "10:15", "11:15", "Lecture Hall 101"),
            (s1.id, sub5.id, t5.id, "Thursday", "14:00", "15:00", "Lecture Hall 102"),
            # Friday
            (s1.id, sub4.id, t4.id, "Friday", "09:00", "10:00", "Lecture Hall 101"),
            (s1.id, sub1.id, t1.id, "Friday", "10:15", "11:15", "Lecture Hall 101"),
            (s1.id, sub3.id, t3.id, "Friday", "11:30", "12:30", "Network Lab 2"),
        ]
        for entry in timetable_data:
            db.add(TimetableEntry(
                student_id=entry[0],
                subject_id=entry[1],
                teacher_id=entry[2],
                day_of_week=entry[3],
                start_time=entry[4],
                end_time=entry[5],
                classroom=entry[6]
            ))

        # 5. Attendance Records
        # Generate 30 sessions per subject with realistic statuses
        # CS501: 26/30 (86.7%)
        # CS502: 25/30 (83.3%)
        # CS503: 20/30 (66.7%) -> WARNING TRIGGER
        # CS504: 28/30 (93.3%)
        # CS505: 24/30 (80.0%)
        attendance_config = [
            (sub1.id, 26, 4),
            (sub2.id, 25, 5),
            (sub3.id, 20, 10),  # Under 75%!
            (sub4.id, 28, 2),
            (sub5.id, 24, 6)
        ]
        base_date = today - datetime.timedelta(days=45)
        for subject_id, present_count, absent_count in attendance_config:
            # Add presents
            for i in range(present_count):
                rec_date = base_date + datetime.timedelta(days=i)
                db.add(AttendanceRecord(
                    student_id=s1.id,
                    subject_id=subject_id,
                    date=rec_date,
                    status="Present",
                    remarks="Attended class"
                ))
            # Add absents
            for i in range(absent_count):
                rec_date = base_date + datetime.timedelta(days=present_count + i)
                db.add(AttendanceRecord(
                    student_id=s1.id,
                    subject_id=subject_id,
                    date=rec_date,
                    status="Absent",
                    remarks="Absence recorded"
                ))

        # 6. Tasks for Aarav
        tasks_data = [
            (s1.id, "Review Page Replacement Algorithms", "Practice FIFO, LRU, and Optimal page replacement numericals", sub1.id, "High", today + datetime.timedelta(days=2), "Pending"),
            (s1.id, "Solve BCNF & 3NF Normalization Questions", "Complete Exercise 4 from DBMS textbook", sub2.id, "Medium", today + datetime.timedelta(days=4), "Pending"),
            (s1.id, "Read TCP Congestion Control Tahoe vs Reno", "Prepare notes on additive increase multiplicative decrease", sub3.id, "High", today + datetime.timedelta(days=1), "Pending"),
            (s1.id, "Train Decision Tree Classifier on Iris Dataset", "Implement Scikit-Learn pipeline and plot tree diagram", sub4.id, "Low", today + datetime.timedelta(days=5), "Pending"),
            (s1.id, "Submit SRS Document Draft", "Draft Software Requirements Specification for Team Project", sub5.id, "Medium", today - datetime.timedelta(days=2), "Completed"),
            (s1.id, "Review Banker's Algorithm Code", "Write multi-threaded resource allocation simulator in C", sub1.id, "Medium", today - datetime.timedelta(days=5), "Completed"),
        ]
        for t in tasks_data:
            db.add(Task(
                student_id=t[0],
                title=t[1],
                description=t[2],
                subject_id=t[3],
                priority=t[4],
                due_date=t[5],
                status=t[6]
            ))

        # 7. Assignments for Aarav
        assignments_data = [
            (s1.id, sub1.id, "Kernel Synchronization Lab", "Implement Producer-Consumer and Dining Philosophers using POSIX semaphores", today + datetime.timedelta(days=3), 100, "Pending", "High"),
            (s1.id, sub2.id, "SQL Complex Queries & Indexing", "Write queries with window functions, common table expressions, and analyze EXPLAIN PLAN", today + datetime.timedelta(days=7), 100, "Pending", "Medium"),
            (s1.id, sub3.id, "Wireshark Packet Analysis", "Capture and inspect TCP 3-way handshake, DNS lookup, and HTTP requests", today + datetime.timedelta(days=5), 50, "Pending", "High"),
            (s1.id, sub4.id, "Machine Learning Classification Mini-Project", "Train and evaluate Logistic Regression, Random Forest, and SVM models", today + datetime.timedelta(days=12), 100, "Pending", "Medium"),
            (s1.id, sub5.id, "Agile Sprint Planning Report", "Create user stories, story points, and sprint burndown chart", today - datetime.timedelta(days=3), 50, "Submitted", "Low"),
        ]
        for a in assignments_data:
            db.add(Assignment(
                student_id=a[0],
                subject_id=a[1],
                title=a[2],
                description=a[3],
                due_date=a[4],
                max_marks=a[5],
                status=a[6],
                priority=a[7]
            ))

        # 8. Examinations
        exams_data = [
            (s1.id, sub1.id, "Final", today + datetime.timedelta(days=14), "10:00", "13:00", "Auditorium Hall B", "Units 1 to 5: Processes, Memory, Storage, File Systems", "In Progress", 100),
            (s1.id, sub2.id, "Final", today + datetime.timedelta(days=17), "10:00", "13:00", "Auditorium Hall B", "Units 1 to 5: ER modeling, SQL, Normalization, ACID transactions", "In Progress", 100),
            (s1.id, sub3.id, "Final", today + datetime.timedelta(days=21), "10:00", "13:00", "Auditorium Hall B", "Units 1 to 5: OSI/TCP, Subnetting, Routing, Transport, Application", "Not Started", 100),
            (s1.id, sub4.id, "Final", today + datetime.timedelta(days=25), "14:00", "17:00", "Main Exam Center Room 204", "Units 1 to 5: Search, Logic, Supervised & Unsupervised Learning", "Not Started", 100),
            (s1.id, sub1.id, "Practical Lab Exam", today + datetime.timedelta(days=10), "09:00", "12:00", "OS Computing Lab", "Kernel programming and synchronization primitives", "Prepared", 50),
        ]
        for e in exams_data:
            db.add(Examination(
                student_id=e[0],
                subject_id=e[1],
                exam_type=e[2],
                exam_date=e[3],
                start_time=e[4],
                end_time=e[5],
                venue=e[6],
                syllabus=e[7],
                preparation_status=e[8],
                max_marks=e[9]
            ))

        # 9. Meeting Requests
        meetings_data = [
            (s1.id, t3.id, "Discuss attendance condonation and remedial assignments for Computer Networks", today + datetime.timedelta(days=2), "11:00", "Approved", "Please bring your previous lab submission records."),
            (s1.id, t1.id, "Clarification on final project topic in OS process scheduling", today + datetime.timedelta(days=4), "15:30", "Pending", None),
        ]
        for m in meetings_data:
            db.add(MeetingRequest(
                student_id=m[0],
                teacher_id=m[1],
                purpose=m[2],
                requested_date=m[3],
                requested_time=m[4],
                status=m[5],
                teacher_notes=m[6]
            ))

        # 10. Notifications
        notifications_data = [
            (s1.id, "Critical Attendance Alert: CS503", "Your attendance in Computer Networks is currently 66.7%, which is below the mandatory 75% threshold. You need 10 consecutive classes to reach 75%.", "Attendance", False),
            (s1.id, "Upcoming Assignment: Kernel Synchronization", "Assignment 'Kernel Synchronization Lab' for Operating Systems is due in 3 days.", "Assignment", False),
            (s1.id, "Exam Schedule Released", "Final examination for CS501 Operating Systems is scheduled in 14 days at Auditorium Hall B.", "Exam", False),
            (s1.id, "Meeting Request Approved", "Dr. Vikram Malhotra approved your meeting request for " + str(today + datetime.timedelta(days=2)) + " at 11:00 AM.", "Meeting", True),
        ]
        for n in notifications_data:
            db.add(Notification(
                student_id=n[0],
                title=n[1],
                message=n[2],
                category=n[3],
                is_read=n[4]
            ))

        # 11. Initial Long-term & Episodic Memories
        memories_data = [
            (s1.id, "long_term", "preferred_study_time", "Prefers studying in late evening after 6:00 PM", '{"category": "study_preference", "confidence": 0.95}'),
            (s1.id, "long_term", "focus_subject", "Computer Networks (CS503) requires top priority due to low attendance and upcoming finals", '{"priority": "high"}'),
            (s1.id, "long_term", "session_duration", "Prefers 45-minute focused study sessions with 10-minute breaks", '{"category": "productivity"}'),
            (s1.id, "episodic", "last_approved_plan", "Approved 5-day midterm revision sprint on October 8 with focus on Operating Systems", '{"date": "2026-10-08", "status": "completed"}'),
        ]
        for mem in memories_data:
            db.add(MemoryItem(
                student_id=mem[0],
                memory_type=mem[1],
                key=mem[2],
                value=mem[3],
                metadata_json=mem[4]
            ))

        db.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    seed_database()
