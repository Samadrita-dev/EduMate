import sys
from pathlib import Path
import streamlit as st

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.db import get_db, init_db
from database.models import Student
from database.seed import seed_database
from utils.ui_components import apply_custom_css, render_brand_sidebar
from config import APP_NAME, APP_TAGLINE, DEFAULT_STUDENT_ID

# Page configuration
st.set_page_config(
    page_title=f"{APP_NAME} - {APP_TAGLINE}",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply premium academic CSS
apply_custom_css()

# Ensure database is seeded
init_db()
seed_database()

# Session state initialization
if "active_student_id" not in st.session_state:
    st.session_state["active_student_id"] = DEFAULT_STUDENT_ID

student_id = st.session_state["active_student_id"]

# Fetch current student details & all students for profile switcher
with get_db() as db:
    all_students = db.query(Student).order_by(Student.id.asc()).all()
    students_map = {f"{s.name} ({s.roll_no})": s.id for s in all_students}

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        student = all_students[0] if all_students else None
        if student:
            student_id = student.id
            st.session_state["active_student_id"] = student_id

    if student:
        student_name = student.name
        student_department = student.department
        student_semester = student.semester
    else:
        student_name = "Guest Student"
        student_department = "General"
        student_semester = 1

# Render Sidebar Brand
render_brand_sidebar(
    current_student_name=student_name,
    department=student_department,
    semester=student_semester
)

# Quick Profile Switcher in Sidebar
if students_map:
    current_key = next((k for k, v in students_map.items() if v == student_id), list(students_map.keys())[0])
    curr_idx = list(students_map.keys()).index(current_key)
    chosen_student_label = st.sidebar.selectbox("👤 Active Student User", list(students_map.keys()), index=curr_idx)
    if students_map[chosen_student_label] != student_id:
        st.session_state["active_student_id"] = students_map[chosen_student_label]
        st.rerun()

st.sidebar.markdown("---")

# Sidebar Navigation
NAV_OPTIONS = [
    "📊 Dashboard",
    "📋 My Tasks",
    "📈 Attendance",
    "🗓️ Timetable",
    "📚 Assignments",
    "📝 Examinations",
    "👨‍🏫 Teacher Directory",
    "🤝 Meeting Scheduler",
    "🧠 Study Planner",
    "🔔 Notifications",
    "⚙️ Profile and Settings",
    "🛠️ Admin & Student Management",
]

selected_nav = st.sidebar.radio("Navigation", NAV_OPTIONS, index=0)

# Sidebar Footer
st.sidebar.markdown("---")
st.sidebar.caption("🚀 **EduMate v1.0.0**\nAcademic Management System")

# Page Routing
if selected_nav == "📊 Dashboard":
    from views.dashboard import render_dashboard
    render_dashboard(student_id)

elif selected_nav == "📋 My Tasks":
    from views.tasks import render_tasks
    render_tasks(student_id)

elif selected_nav == "📈 Attendance":
    from views.attendance import render_attendance
    render_attendance(student_id)

elif selected_nav == "🗓️ Timetable":
    from views.timetable import render_timetable
    render_timetable(student_id)

elif selected_nav == "📚 Assignments":
    from views.assignments import render_assignments
    render_assignments(student_id)

elif selected_nav == "📝 Examinations":
    from views.exams import render_exams
    render_exams(student_id)

elif selected_nav == "👨‍🏫 Teacher Directory":
    from views.teachers import render_teachers
    render_teachers(student_id)

elif selected_nav == "🤝 Meeting Scheduler":
    from views.meetings import render_meetings
    render_meetings(student_id)

elif selected_nav == "🧠 Study Planner":
    from views.study_planner import render_study_planner
    render_study_planner(student_id)

elif selected_nav == "🔔 Notifications":
    from views.notifications import render_notifications
    render_notifications(student_id)

elif selected_nav == "⚙️ Profile and Settings":
    from views.profile_settings import render_profile_settings
    render_profile_settings(student_id)

elif selected_nav == "🛠️ Admin & Student Management":
    from views.admin import render_admin
    render_admin(student_id)
