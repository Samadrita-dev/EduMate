import streamlit as st
import datetime
from database.db import get_db
from database.models import Subject
from tools.task_tools import add_task, get_tasks, update_task, delete_task

def render_tasks(student_id: int):
    """Renders the interactive To-Do and Task Management interface."""
    st.markdown("## 📋 My Tasks & To-Do List")
    st.caption("Organize your daily study goals, track assignments, and prioritize pending academic work.")

    # Top Control Row: Add Task Expander
    with st.expander("➕ Add New Academic Task", expanded=False):
        with st.form("new_task_form", clear_on_submit=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                title = st.text_input("Task Title *", placeholder="e.g. Practice BCNF Normalization Numericals")
                description = st.text_area("Description", placeholder="e.g. Complete textbook problems 1 to 5")
            with col2:
                with get_db() as db:
                    subjects = db.query(Subject).all()
                    subj_map = {f"{s.code} - {s.name}": s.id for s in subjects}

                selected_sub_label = st.selectbox("Related Subject", ["General (No Subject)"] + list(subj_map.keys()))
                subject_id = subj_map.get(selected_sub_label) if selected_sub_label != "General (No Subject)" else None

                priority = st.selectbox("Priority Level", ["High", "Medium", "Low"], index=1)
                due_date = st.date_input("Due Date", min_value=datetime.date.today(), value=datetime.date.today() + datetime.timedelta(days=2))

            submitted = st.form_submit_button("Create Task", type="primary")
            if submitted:
                if not title.strip():
                    st.error("Task title is required.")
                else:
                    res = add_task(
                        student_id=student_id,
                        title=title.strip(),
                        due_date=str(due_date),
                        description=description.strip(),
                        subject_id=subject_id,
                        priority=priority
                    )
                    if res.get("success"):
                        st.success("Task created successfully!")
                        st.rerun()
                    else:
                        st.error(res.get("error"))

    st.markdown("---")

    # Filters and Sorting
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1:
        status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Completed"])
    with f_col2:
        sort_by = st.selectbox("Sort By", ["Due Date", "Priority"])
    with f_col3:
        with get_db() as db:
            subs = db.query(Subject).all()
            filter_subj_options = ["All Subjects"] + [s.code for s in subs]
        sub_filter = st.selectbox("Filter by Subject", filter_subj_options)

    # Fetch tasks
    sort_key = "priority" if sort_by == "Priority" else "due_date"
    status_arg = None if status_filter == "All" else status_filter
    task_res = get_tasks(student_id=student_id, status=status_arg, sort_by=sort_key)
    tasks = task_res.get("tasks", [])

    if sub_filter != "All Subjects":
        tasks = [t for t in tasks if sub_filter in t.get("subject_name", "") or sub_filter == t.get("subject_code", "")]

    st.write(f"Showing **{len(tasks)}** task(s)")

    if not tasks:
        st.info("No tasks found matching your filter criteria.")
        return

    # Task List View
    today = datetime.date.today()
    for t in tasks:
        is_completed = t["status"] == "Completed"
        is_overdue = t.get("is_overdue", False)

        p_color = "#FF3366" if t["priority"] == "High" else ("#FFB800" if t["priority"] == "Medium" else "#00FF66")
        border_color = "#00FF66" if is_completed else ("#FF3366" if is_overdue else "#1E2922")

        with st.container():
            st.markdown(f"""
            <div style="background-color: #121513; border: 1px solid #1E2922; border-left: 5px solid {border_color}; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 0.75rem; box-shadow: 0 0 10px {border_color}15;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.1rem; font-weight: 700; text-decoration: {'line-through' if is_completed else 'none'}; color: {'#666666' if is_completed else '#FFFFFF'};">
                        {t['title']}
                    </span>
                    <span>
                        <span style="background-color: {p_color}25; color: {p_color}; border: 1px solid {p_color}60; border-radius: 9999px; padding: 0.2rem 0.6rem; font-size: 0.75rem; font-weight: 700;">
                            {t['priority']}
                        </span>
                    </span>
                </div>
                <div style="font-size: 0.88rem; color: #CCCCCC; margin-top: 0.35rem;">
                    {t['description']}
                </div>
                <div style="font-size: 0.82rem; color: #8C9990; margin-top: 0.5rem; display: flex; gap: 1.5rem;">
                    <span>📚 <b>Subject:</b> <span style="color:#00FF66;">{t.get('subject_name', 'General')}</span></span>
                    <span>📅 <b>Due:</b> {t['due_date']} {'<span style="color:#FF3366; font-weight:bold;">(OVERDUE)</span>' if is_overdue else ''}</span>
                    <span>Status: <b style="color:{'#00FF66' if is_completed else '#FFB800'};">{t['status']}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            btn_col1, btn_col2, btn_col3, _ = st.columns([1, 1, 1, 3])
            with btn_col1:
                toggle_label = "Undo" if is_completed else "Mark Done"
                if st.button(toggle_label, key=f"done_{t['id']}"):
                    new_st = "Pending" if is_completed else "Completed"
                    update_task(task_id=t["id"], student_id=student_id, status=new_st)
                    st.rerun()

            with btn_col2:
                if st.button("Delete", key=f"del_{t['id']}"):
                    delete_task(task_id=t["id"], student_id=student_id)
                    st.rerun()
