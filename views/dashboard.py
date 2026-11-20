import streamlit as st
import datetime
import plotly.express as px
import plotly.graph_objects as go
from database.db import get_db
from database.models import (
    Student, Subject, Task, Assignment, Examination, MeetingRequest, Notification, TimetableEntry
)
from tools.attendance_tools import get_attendance
from utils.ui_components import render_metric_card, render_alert_box

def render_dashboard(student_id: int):
    """Renders the comprehensive personalized student dashboard in black and neon green."""
    today = datetime.date.today()

    with get_db() as db:
        student_obj = db.query(Student).filter(Student.id == student_id).first()
        if not student_obj:
            st.error("Student profile not found.")
            return
        student = student_obj.to_dict()

        # Real metrics counts
        pending_tasks = db.query(Task).filter(Task.student_id == student_id, Task.status == "Pending").count()
        completed_tasks = db.query(Task).filter(Task.student_id == student_id, Task.status == "Completed").count()
        total_tasks = pending_tasks + completed_tasks
        
        pending_assignments = db.query(Assignment).filter(Assignment.student_id == student_id, Assignment.status == "Pending").count()
        completed_assignments = db.query(Assignment).filter(Assignment.student_id == student_id, Assignment.status.in_(["Submitted", "Graded"])).count()

        upcoming_exams = [e.to_dict() for e in db.query(Examination).filter(Examination.student_id == student_id, Examination.exam_date >= today).order_by(Examination.exam_date.asc()).all()]
        next_exam = upcoming_exams[0] if upcoming_exams else None

        upcoming_meetings = [m.to_dict() for m in db.query(MeetingRequest).filter(MeetingRequest.student_id == student_id, MeetingRequest.requested_date >= today).all()]

        notifications = [n.to_dict() for n in db.query(Notification).filter(Notification.student_id == student_id).order_by(Notification.created_at.desc()).limit(4).all()]

        current_day = today.strftime("%A")
        todays_classes = [c.to_dict() for c in db.query(TimetableEntry).filter(
            TimetableEntry.student_id == student_id,
            TimetableEntry.day_of_week == current_day
        ).order_by(TimetableEntry.start_time.asc()).all()]

    # Attendance query via verified tool
    att_data = get_attendance(student_id)
    overall_attendance = att_data.get("overall_attendance_percentage", 0.0)

    # Header section
    st.markdown(f"## 🎓 Academic Command Center — {student['name']}")
    st.caption(f"📅 **Today:** {today.strftime('%A, %B %d, %Y')} | 🏛️ **Dept:** {student['department']} | 📘 **Semester {student['semester']}** | 🎯 **Current CGPA:** `{student['cgpa']}`")
    st.markdown("---")

    # Critical Alerts banner if attendance < 75%
    shortage_subs = [s for s in att_data.get("subjects", []) if s["attendance_percentage"] < 75.0]
    if shortage_subs:
        warning_msg = ", ".join([f"**{s['subject_code']}** ({s['attendance_percentage']}%) - Needs {s['classes_needed_for_target']} consecutive classes" for s in shortage_subs])
        render_alert_box(
            "⚠️ ATTENDANCE WARNING TRIGGERED",
            f"You are falling short of the mandatory 75% threshold in: {warning_msg}. Debarment risk applies under College Policy ACAD-POL-04.",
            level="critical"
        )

    # Top KPI Metrics Row
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        att_subtext = "🟢 In Good Standing" if overall_attendance >= 75.0 else "🔴 Shortage Alert"
        render_metric_card("Overall Attendance", f"{overall_attendance}%", att_subtext)

    with m_col2:
        render_metric_card("Pending Tasks", f"{pending_tasks}", f"{completed_tasks} completed so far")

    with m_col3:
        render_metric_card("Active Assignments", f"{pending_assignments}", f"{completed_assignments} submitted")

    with m_col4:
        if next_exam:
            exam_date_obj = datetime.date.fromisoformat(next_exam["exam_date"])
            days_left = (exam_date_obj - today).days
            exam_subtext = f"In {days_left} days ({next_exam['subject_code']})"
            render_metric_card("Next Final Exam", next_exam["subject_code"], exam_subtext)
        else:
            render_metric_card("Next Exam", "None", "All exams completed")

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Row
    chart_col1, chart_col2 = st.columns([3, 2])

    with chart_col1:
        st.subheader("📊 Subject Attendance Overview")
        subjects_list = att_data.get("subjects", [])
        if subjects_list:
            sub_codes = [s["subject_code"] for s in subjects_list]
            sub_pcts = [s["attendance_percentage"] for s in subjects_list]
            # Neon Green for safe, Red for risk
            colors = ["#FF3366" if p < 75.0 else "#00FF66" for p in sub_pcts]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=sub_codes,
                y=sub_pcts,
                marker=dict(color=colors, line=dict(color="#00FF66", width=1)),
                text=[f"{p}%" for p in sub_pcts],
                textposition="auto",
                textfont=dict(color="#000000", family="sans-serif", size=12),
                name="Attendance %"
            ))
            # 75% threshold line
            fig.add_hline(
                y=75,
                line_dash="dot",
                line_color="#FFB800",
                annotation_text="75% Mandatory Cutoff",
                annotation_position="top right",
                annotation_font=dict(color="#FFB800")
            )
            fig.update_layout(
                yaxis=dict(
                    range=[0, 100],
                    title="Percentage (%)",
                    gridcolor="#1F2922",
                    color="#A3A3A3"
                ),
                xaxis=dict(
                    title="Course Code",
                    gridcolor="#1F2922",
                    color="#A3A3A3"
                ),
                margin=dict(l=20, r=20, t=30, b=20),
                height=300,
                plot_bgcolor="#0E1110",
                paper_bgcolor="#0E1110",
                font=dict(color="#EAEAEA")
            )
            st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        st.subheader("📋 Academic Task Status")
        if total_tasks > 0:
            fig_tasks = px.pie(
                names=["Pending Tasks", "Completed Tasks"],
                values=[pending_tasks, completed_tasks],
                color_discrete_sequence=["#FFB800", "#00FF66"],
                hole=0.55
            )
            fig_tasks.update_layout(
                margin=dict(l=10, r=10, t=20, b=20),
                height=300,
                showlegend=True,
                paper_bgcolor="#0E1110",
                plot_bgcolor="#0E1110",
                font=dict(color="#EAEAEA"),
                legend=dict(font=dict(color="#EAEAEA"))
            )
            st.plotly_chart(fig_tasks, use_container_width=True)
        else:
            st.info("No tasks recorded yet.")

    st.markdown("---")

    # Detailed Schedule & Upcoming Deadlines Grid
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("🗓️ Today's Lecture Schedule")
        if todays_classes:
            for c in todays_classes:
                st.markdown(f"""
                <div style="background:#121513; border:1px solid #1E2922; border-left: 4px solid #00FF66; border-radius:6px; padding:0.75rem 1rem; margin-bottom:0.6rem; box-shadow: 0 0 10px rgba(0,255,102,0.06);">
                    <strong style="color:#00FF66; font-size:1rem;">{c['start_time']} - {c['end_time']}</strong> &nbsp;|&nbsp; <b style="color:#FFFFFF;">{c['subject_name']}</b> ({c['subject_code']})<br>
                    <span style="font-size:0.85rem; color:#A3A3A3;">📍 {c['classroom']} &nbsp;•&nbsp; 👨‍🏫 {c['teacher_name']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No classes scheduled for today ({current_day}). Great day for independent revision!")

    with row2_col2:
        st.subheader("📝 Approaching Examinations")
        if upcoming_exams:
            for ex in upcoming_exams[:3]:
                ex_date = datetime.date.fromisoformat(ex["exam_date"])
                days_rem = (ex_date - today).days
                badge_color = "#FF3366" if days_rem <= 7 else "#00FF66"
                st.markdown(f"""
                <div style="background:#121513; border:1px solid #1E2922; border-left: 4px solid {badge_color}; border-radius:6px; padding:0.75rem 1rem; margin-bottom:0.6rem; box-shadow: 0 0 10px rgba(0,255,102,0.06);">
                    <strong style="color:#FFFFFF; font-size:1rem;">{ex['subject_name']} ({ex['exam_type']})</strong><br>
                    <span style="font-size:0.85rem; color:#A3A3A3;">📅 {ex['exam_date']} at {ex['start_time']} | 📍 {ex['venue']}</span><br>
                    <span style="color:{badge_color}; font-weight:700; font-size:0.85rem;">⏳ {days_rem} days remaining • Prep: {ex['preparation_status']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No upcoming exams in the immediate schedule.")

    st.markdown("---")

    # Bottom Notifications & Quick Meetings
    row3_col1, row3_col2 = st.columns(2)

    with row3_col1:
        st.subheader("🔔 Recent In-App Notifications")
        if notifications:
            for n in notifications:
                read_dot = "⚪" if n.get("is_read") else "🟢"
                st.markdown(f"**{read_dot} [{n.get('category')}] {n.get('title')}**")
                st.caption(f"{n.get('message')} &nbsp;•&nbsp; *{n.get('created_at', '')[:16]}*")
        else:
            st.write("No unread notifications.")

    with row3_col2:
        st.subheader("👨‍🏫 Upcoming Faculty Consultations")
        if upcoming_meetings:
            for m in upcoming_meetings:
                status_color = "#00FF66" if m["status"] == "Approved" else "#FFB800"
                st.markdown(f"""
                <div style="background:#121513; border:1px solid #1E2922; border-radius:6px; padding:0.75rem 1rem; margin-bottom:0.6rem;">
                    <strong style="color:#FFFFFF;">{m['teacher_name']}</strong> — <span style="color:{status_color}; font-weight:bold;">{m['status']}</span><br>
                    <span style="font-size:0.85rem; color:#A3A3A3;">📅 {m['requested_date']} at {m['requested_time']}</span><br>
                    <span style="font-size:0.82rem; color:#8C9990;">Purpose: {m['purpose']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write("No upcoming teacher appointments scheduled.")
