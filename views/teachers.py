import streamlit as st
from database.db import get_db
from database.models import Teacher, Subject
from sqlalchemy.orm import joinedload


def render_teachers(student_id: int):
    """Renders the Faculty and Teacher Directory in black and neon green."""
    st.markdown("## 👨‍🏫 Faculty & Teacher Directory")
    st.caption("Access official faculty profiles, designated office consultation hours, and academic cabins.")

    # Search & Filter
    s_col1, s_col2 = st.columns([2, 1])
    with s_col1:
        search_query = st.text_input("🔍 Search Faculty by Name or Designation", placeholder="e.g. Rajesh, Sharma, Associate Professor")
    with s_col2:
        with get_db() as db:
            teachers_all = db.query(Teacher).all()
            depts = list(set(t.department for t in teachers_all))
        dept_filter = st.selectbox("Department", ["All Departments"] + sorted(depts))

    # Build teacher list as plain dicts inside session
    with get_db() as db:
        query = db.query(Teacher).options(joinedload(Teacher.subjects))
        if dept_filter != "All Departments":
            query = query.filter(Teacher.department == dept_filter)
        if search_query.strip():
            term = f"%{search_query.strip()}%"
            query = query.filter(
                (Teacher.name.ilike(term)) | (Teacher.designation.ilike(term))
            )
        raw_teachers = query.order_by(Teacher.name.asc()).all()
        teachers = [{
            "id": t.id,
            "name": t.name,
            "designation": t.designation,
            "department": t.department,
            "room_no": t.room_no or "Faculty Hall",
            "email": t.email,
            "office_hours": t.office_hours or "By appointment",
            "subjects_taught": ", ".join([f"{s.code} ({s.name})" for s in t.subjects]) if t.subjects else "Department Faculty",
        } for t in raw_teachers]

    st.write(f"Showing **{len(teachers)}** faculty member(s)")

    if not teachers:
        st.info("No teachers matched your search criteria.")
        return

    # Teacher Cards Grid
    cols = st.columns(2)
    for idx, t in enumerate(teachers):
        with cols[idx % 2]:
            st.markdown(f"""
            <div style="background-color: #121513; border: 1px solid #1E2922; border-left: 4px solid #00FF66; border-radius: 10px; padding: 1.25rem; margin-bottom: 1rem; box-shadow: 0 0 12px rgba(0,255,102,0.08);">
                <div style="font-size: 1.2rem; font-weight: 800; color: #FFFFFF;">{t['name']}</div>
                <div style="font-size: 0.88rem; font-weight: 700; color: #00FF66; margin-top: 0.2rem;">{t['designation']}</div>
                <div style="font-size: 0.82rem; color: #8C9990; margin-top: 0.2rem;">🏛️ {t['department']}</div>
                <div style="margin-top: 0.75rem; font-size: 0.85rem; color: #CCCCCC; line-height: 1.6;">
                    📚 <b>Courses:</b> <span style="color:#00FF66;">{t['subjects_taught']}</span><br>
                    📍 <b>Cabin:</b> <span style="color:#FFFFFF;">{t['room_no']}</span><br>
                    📧 <b>Email:</b> <code style="color:#00FF66; background:#0A0D0B; border:1px solid #1E2922;">{t['email']}</code><br>
                    🕒 <b>Office Hours:</b> <b style="color:#00FF66;">{t['office_hours']}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
