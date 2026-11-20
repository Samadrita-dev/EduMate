import streamlit as st
import datetime
from database.db import get_db
from database.models import Assignment, Subject


def render_assignments(student_id: int):
    """Renders the comprehensive Coursework and Assignment Manager."""
    st.markdown("## 📚 Coursework & Assignments")
    st.caption("Manage assignment submissions, monitor approaching deadlines, and track grading progress.")

    # Load data inside session, convert to plain dicts immediately
    with get_db() as db:
        raw_assignments = (
            db.query(Assignment)
            .filter(Assignment.student_id == student_id)
            .order_by(Assignment.due_date.asc())
            .all()
        )
        subjects = db.query(Subject).all()
        subj_map = {f"{s.code} - {s.name}": s.id for s in subjects}
        assignments = []
        for a in raw_assignments:
            assignments.append({
                "id": a.id,
                "title": a.title,
                "description": a.description or "",
                "subject_name": a.subject.name if a.subject else "Unknown",
                "subject_code": a.subject.code if a.subject else "N/A",
                "subject_id": a.subject_id,
                "due_date": a.due_date,
                "max_marks": a.max_marks,
                "priority": a.priority,
                "status": a.status,
            })

    # Add Assignment Form
    with st.expander("➕ Submit / Register New Assignment", expanded=False):
        with st.form("add_assignment_form", clear_on_submit=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                title = st.text_input("Assignment Title *", placeholder="e.g. Distributed Database Sharding Lab")
                desc = st.text_area("Description / Problem Statement", placeholder="e.g. Implement range partitioning and benchmark query latency")
            with col2:
                selected_sub = st.selectbox("Course Subject *", list(subj_map.keys()))
                due_date = st.date_input("Deadline", min_value=datetime.date.today(), value=datetime.date.today() + datetime.timedelta(days=5))
                priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
                max_marks = st.number_input("Maximum Marks", min_value=10, max_value=200, value=100)

            submitted = st.form_submit_button("Register Assignment", type="primary")
            if submitted:
                if not title.strip():
                    st.error("Title is required.")
                else:
                    with get_db() as db:
                        new_a = Assignment(
                            student_id=student_id,
                            subject_id=subj_map[selected_sub],
                            title=title.strip(),
                            description=desc.strip(),
                            due_date=due_date,
                            max_marks=max_marks,
                            priority=priority,
                            status="Pending"
                        )
                        db.add(new_a)
                        db.commit()
                    st.success("Assignment registered successfully!")
                    st.rerun()

    st.markdown("---")

    today = datetime.date.today()
    if not assignments:
        st.info("No assignments currently logged.")
        return

    # Filter tabs
    status_tabs = st.tabs(["Pending / Due Soon", "Submitted / Graded", "All Assignments"])

    with status_tabs[0]:
        pending_list = [a for a in assignments if a["status"] in ["Pending", "Overdue"]]
        if not pending_list:
            st.success("🎉 All assignments are submitted! No pending deadlines.")
        for a in pending_list:
            days_left = (a["due_date"] - today).days
            urgency_color = "#FF3366" if days_left <= 3 else "#00FF66"
            st.markdown(f"""
            <div style="background-color: #121513; border: 1px solid #1E2922; border-left: 5px solid {urgency_color}; border-radius: 8px; padding: 1.1rem 1.25rem; margin-bottom: 0.75rem; box-shadow: 0 0 10px {urgency_color}15;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; font-size: 1.15rem; color: #FFFFFF;">{a['title']}</span>
                    <span style="background-color: {urgency_color}25; color: {urgency_color}; border: 1px solid {urgency_color}60; padding: 0.25rem 0.65rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700;">
                        ⏳ {days_left} day(s) left
                    </span>
                </div>
                <div style="font-size: 0.88rem; color: #CCCCCC; margin-top: 0.4rem;">{a['description']}</div>
                <div style="font-size: 0.82rem; color: #8C9990; margin-top: 0.5rem; display: flex; gap: 1.5rem;">
                    <span>📚 <b>Course:</b> <span style="color:#00FF66;">{a['subject_name']} ({a['subject_code']})</span></span>
                    <span>📅 <b>Deadline:</b> {a['due_date']}</span>
                    <span>🎯 <b>Max Marks:</b> {a['max_marks']}</span>
                    <span>Priority: <b style="color:#FFFFFF;">{a['priority']}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            btn_col1, _ = st.columns([2, 5])
            with btn_col1:
                if st.button("Mark as Submitted", key=f"sub_{a['id']}"):
                    with get_db() as db:
                        rec = db.query(Assignment).filter(Assignment.id == a["id"]).first()
                        if rec:
                            rec.status = "Submitted"
                            db.commit()
                    st.success(f"'{a['title']}' marked as Submitted!")
                    st.rerun()

    with status_tabs[1]:
        completed_list = [a for a in assignments if a["status"] in ["Submitted", "Graded"]]
        if not completed_list:
            st.write("No submitted or graded assignments yet.")
        for a in completed_list:
            st.markdown(f"""
            <div style="background-color: #121513; border: 1px solid #1E2922; border-left: 5px solid #00FF66; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 0.75rem; box-shadow: 0 0 10px rgba(0,255,102,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; font-size: 1.1rem; color: #FFFFFF;">{a['title']}</span>
                    <span style="background-color: #00FF6625; color: #00FF66; border: 1px solid #00FF6660; padding: 0.25rem 0.65rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700;">
                        ✅ {a['status']}
                    </span>
                </div>
                <div style="font-size: 0.85rem; color: #8C9990; margin-top: 0.4rem;">
                    Course: <b style="color:#00FF66;">{a['subject_name']}</b> &nbsp;•&nbsp; Submitted on or before {a['due_date']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with status_tabs[2]:
        all_table = []
        for a in assignments:
            all_table.append({
                "Title": a["title"],
                "Course": a["subject_code"],
                "Deadline": str(a["due_date"]),
                "Priority": a["priority"],
                "Status": a["status"],
                "Max Marks": a["max_marks"]
            })
        st.dataframe(all_table, use_container_width=True)
