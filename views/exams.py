import streamlit as st
import datetime
from database.db import get_db
from database.models import Examination, Subject
from tools.exam_tools import update_exam_prep_status
from sqlalchemy.orm import joinedload


def render_exams(student_id: int):
    """Renders the examination schedule, syllabus breakdown, and prep tracker."""
    st.markdown("## 📝 Examination Center")
    st.caption("Track official exam dates, venue halls, syllabus coverage, and your revision readiness.")

    today = datetime.date.today()

    # Load all exams inside session and convert to plain dicts
    with get_db() as db:
        raw_exams = (
            db.query(Examination)
            .options(joinedload(Examination.subject))
            .filter(Examination.student_id == student_id)
            .order_by(Examination.exam_date.asc())
            .all()
        )
        exams = []
        for e in raw_exams:
            exams.append({
                "id": e.id,
                "subject_name": e.subject.name if e.subject else "Unknown",
                "subject_code": e.subject.code if e.subject else "N/A",
                "exam_type": e.exam_type,
                "exam_date": e.exam_date,
                "start_time": str(e.start_time),
                "end_time": str(e.end_time),
                "venue": e.venue,
                "syllabus": e.syllabus or "Refer course outline",
                "max_marks": e.max_marks,
                "preparation_status": e.preparation_status or "Not Started",
            })

    if not exams:
        st.info("No examinations currently scheduled.")
        return

    # Countdown Metric Grid
    st.subheader("⏳ Examination Countdowns")
    grid_cols = st.columns(min(3, len(exams)))
    for idx, e in enumerate(exams[:3]):
        days_left = (e["exam_date"] - today).days
        count_color = "#FF3366" if days_left <= 7 else "#00FF66"
        with grid_cols[idx]:
            st.markdown(f"""
            <div style="background-color: #121513; border: 1px solid #1E2922; border-radius: 8px; padding: 1.1rem; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
                <div style="font-size: 0.82rem; font-weight: 700; color: #8C9990; text-transform: uppercase;">{e['exam_type']}</div>
                <div style="font-size: 1.35rem; font-weight: 800; color: #00FF66; margin-top: 0.2rem; text-shadow: 0 0 8px rgba(0,255,102,0.3);">{e['subject_code']}</div>
                <div style="font-size: 2.2rem; font-weight: 900; color: {count_color}; margin: 0.25rem 0; text-shadow: 0 0 10px {count_color}50;">
                    {days_left} <span style="font-size: 1rem; font-weight: 600;">days</span>
                </div>
                <div style="font-size: 0.82rem; color: #CCCCCC;">📅 {e['exam_date']} ({e['start_time']})</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Detailed Exam Cards
    st.subheader("📋 Exam Schedules & Syllabus Details")
    for e in exams:
        days_left = (e["exam_date"] - today).days
        prep_color = (
            "#00FF66" if e["preparation_status"] == "Prepared"
            else ("#FFB800" if e["preparation_status"] == "In Progress" else "#FF3366")
        )

        with st.container():
            st.markdown(f"""
            <div style="background-color: #121513; border: 1px solid #1E2922; border-left: 5px solid {prep_color}; border-radius: 8px; padding: 1.2rem; margin-bottom: 0.75rem; box-shadow: 0 0 12px {prep_color}18;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 800; font-size: 1.2rem; color: #FFFFFF;">
                        {e['subject_name']} <span style="color: #00FF66;">({e['subject_code']})</span> — {e['exam_type']}
                    </span>
                    <span style="background-color: {prep_color}25; color: {prep_color}; border: 1px solid {prep_color}60; font-weight: 700; padding: 0.25rem 0.65rem; border-radius: 9999px; font-size: 0.82rem;">
                        {e['preparation_status']}
                    </span>
                </div>
                <div style="font-size: 0.88rem; color: #CCCCCC; margin-top: 0.6rem; display: flex; gap: 1.5rem;">
                    <span>📅 <b>Date:</b> {e['exam_date']}</span>
                    <span>🕒 <b>Time:</b> {e['start_time']} - {e['end_time']}</span>
                    <span>📍 <b>Venue:</b> <span style="color:#00FF66;">{e['venue']}</span></span>
                    <span>🎯 <b>Max Marks:</b> {e['max_marks']}</span>
                </div>
                <div style="background-color: #0A0D0B; border: 1px dashed #1E2922; border-radius: 6px; padding: 0.75rem 0.9rem; margin-top: 0.75rem; font-size: 0.85rem; color: #D4D4D4;">
                    📖 <b>Covered Syllabus:</b> {e['syllabus']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Update Prep Status inline
            p_col1, _ = st.columns([2, 5])
            with p_col1:
                current_idx = ["Not Started", "In Progress", "Prepared"].index(e["preparation_status"])
                new_status = st.selectbox(
                    f"Update Readiness ({e['subject_code']})",
                    ["Not Started", "In Progress", "Prepared"],
                    index=current_idx,
                    key=f"status_sel_{e['id']}"
                )
                if new_status != e["preparation_status"]:
                    update_exam_prep_status(
                        exam_id=e["id"],
                        student_id=student_id,
                        new_status=new_status
                    )
                    st.success(f"Status updated to '{new_status}'!")
                    st.rerun()
