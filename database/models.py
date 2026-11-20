import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime, Text, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    roll_no = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    department = Column(String(100), nullable=False)
    semester = Column(Integer, nullable=False, default=5)
    cgpa = Column(Float, nullable=False, default=8.5)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    tasks = relationship("Task", back_populates="student", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="student", cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", back_populates="student", cascade="all, delete-orphan")
    timetable_entries = relationship("TimetableEntry", back_populates="student", cascade="all, delete-orphan")
    examinations = relationship("Examination", back_populates="student", cascade="all, delete-orphan")
    meetings = relationship("MeetingRequest", back_populates="student", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="student", cascade="all, delete-orphan")
    memories = relationship("MemoryItem", back_populates="student", cascade="all, delete-orphan")
    study_plans = relationship("StudyPlan", back_populates="student", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "roll_no": self.roll_no,
            "name": self.name,
            "email": self.email,
            "department": self.department,
            "semester": self.semester,
            "cgpa": self.cgpa,
        }


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    designation = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    office_hours = Column(String(100), nullable=True)
    room_no = Column(String(50), nullable=True)

    subjects = relationship("Subject", back_populates="teacher")
    meetings = relationship("MeetingRequest", back_populates="teacher")
    timetable_entries = relationship("TimetableEntry", back_populates="teacher")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "department": self.department,
            "designation": self.designation,
            "email": self.email,
            "office_hours": self.office_hours,
            "room_no": self.room_no,
        }


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    semester = Column(Integer, nullable=False, default=5)
    credits = Column(Integer, nullable=False, default=4)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)

    teacher = relationship("Teacher", back_populates="subjects")
    attendance_records = relationship("AttendanceRecord", back_populates="subject")
    timetable_entries = relationship("TimetableEntry", back_populates="subject")
    tasks = relationship("Task", back_populates="subject")
    assignments = relationship("Assignment", back_populates="subject")
    examinations = relationship("Examination", back_populates="subject")

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "department": self.department,
            "semester": self.semester,
            "credits": self.credits,
            "teacher_name": self.teacher.name if self.teacher else "Unassigned",
        }


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="Present")  # 'Present', 'Absent', 'Excused'
    remarks = Column(String(200), nullable=True)

    student = relationship("Student", back_populates="attendance_records")
    subject = relationship("Subject", back_populates="attendance_records")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "subject_id": self.subject_id,
            "subject_code": self.subject.code if self.subject else "",
            "subject_name": self.subject.name if self.subject else "",
            "date": str(self.date),
            "status": self.status,
            "remarks": self.remarks,
        }


class TimetableEntry(Base):
    __tablename__ = "timetable"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    day_of_week = Column(String(20), nullable=False)  # Monday, Tuesday, ...
    start_time = Column(String(10), nullable=False)  # HH:MM e.g. 09:00
    end_time = Column(String(10), nullable=False)    # HH:MM e.g. 10:00
    classroom = Column(String(50), nullable=False, default="Room 101")

    student = relationship("Student", back_populates="timetable_entries")
    subject = relationship("Subject", back_populates="timetable_entries")
    teacher = relationship("Teacher", back_populates="timetable_entries")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "subject_id": self.subject_id,
            "subject_code": self.subject.code if self.subject else "",
            "subject_name": self.subject.name if self.subject else "",
            "teacher_name": self.teacher.name if self.teacher else (self.subject.teacher.name if self.subject and self.subject.teacher else "Faculty"),
            "day_of_week": self.day_of_week,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "classroom": self.classroom,
        }


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    priority = Column(String(20), nullable=False, default="Medium")  # High, Medium, Low
    due_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="Pending")  # Pending, Completed, Overdue
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    student = relationship("Student", back_populates="tasks")
    subject = relationship("Subject", back_populates="tasks")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "title": self.title,
            "description": self.description or "",
            "subject_id": self.subject_id,
            "subject_name": self.subject.name if self.subject else "General",
            "priority": self.priority,
            "due_date": str(self.due_date),
            "status": self.status,
            "created_at": str(self.created_at),
        }


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=False)
    max_marks = Column(Integer, nullable=False, default=100)
    status = Column(String(20), nullable=False, default="Pending")  # Pending, Submitted, Graded, Overdue
    priority = Column(String(20), nullable=False, default="Medium")  # High, Medium, Low
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("Student", back_populates="assignments")
    subject = relationship("Subject", back_populates="assignments")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "subject_id": self.subject_id,
            "subject_code": self.subject.code if self.subject else "",
            "subject_name": self.subject.name if self.subject else "",
            "title": self.title,
            "description": self.description or "",
            "due_date": str(self.due_date),
            "max_marks": self.max_marks,
            "status": self.status,
            "priority": self.priority,
        }


class Examination(Base):
    __tablename__ = "examinations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    exam_type = Column(String(50), nullable=False, default="Midterm")  # Midterm, Final, Quiz, Practical
    exam_date = Column(Date, nullable=False)
    start_time = Column(String(10), nullable=False, default="10:00")
    end_time = Column(String(10), nullable=False, default="13:00")
    venue = Column(String(100), nullable=False, default="Hall A")
    syllabus = Column(Text, nullable=True)
    preparation_status = Column(String(30), nullable=False, default="Not Started")  # Not Started, In Progress, Prepared
    max_marks = Column(Integer, nullable=False, default=100)

    student = relationship("Student", back_populates="examinations")
    subject = relationship("Subject", back_populates="examinations")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "subject_id": self.subject_id,
            "subject_code": self.subject.code if self.subject else "",
            "subject_name": self.subject.name if self.subject else "",
            "exam_type": self.exam_type,
            "exam_date": str(self.exam_date),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "venue": self.venue,
            "syllabus": self.syllabus or "",
            "preparation_status": self.preparation_status,
            "max_marks": self.max_marks,
        }


class MeetingRequest(Base):
    __tablename__ = "meeting_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    purpose = Column(Text, nullable=False)
    requested_date = Column(Date, nullable=False)
    requested_time = Column(String(10), nullable=False)  # HH:MM
    status = Column(String(20), nullable=False, default="Pending")  # Pending, Approved, Rejected, Completed
    teacher_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("Student", back_populates="meetings")
    teacher = relationship("Teacher", back_populates="meetings")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher.name if self.teacher else "",
            "department": self.teacher.department if self.teacher else "",
            "purpose": self.purpose,
            "requested_date": str(self.requested_date),
            "requested_time": self.requested_time,
            "status": self.status,
            "teacher_notes": self.teacher_notes or "",
            "created_at": str(self.created_at),
        }


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="System")  # Exam, Assignment, Attendance, Meeting, Task, System
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("Student", back_populates="notifications")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "title": self.title,
            "message": self.message,
            "category": self.category,
            "is_read": self.is_read,
            "created_at": str(self.created_at),
        }


class MemoryItem(Base):
    __tablename__ = "memory_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    memory_type = Column(String(30), nullable=False, default="long_term")  # short_term, long_term, episodic
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    student = relationship("Student", back_populates="memories")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "memory_type": self.memory_type,
            "key": self.key,
            "value": self.value,
            "metadata_json": self.metadata_json,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
        }


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    target_exam_or_goal = Column(String(200), nullable=False)
    plan_json = Column(Text, nullable=False)  # JSON structure containing breakdown & slots
    status = Column(String(30), nullable=False, default="Proposed")  # Draft, Proposed, Approved, Completed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("Student", back_populates="study_plans")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "title": self.title,
            "target_exam_or_goal": self.target_exam_or_goal,
            "plan_json": self.plan_json,
            "status": self.status,
            "created_at": str(self.created_at),
        }
