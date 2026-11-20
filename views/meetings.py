import streamlit as st
import datetime
from database.db import get_db
from database.models import Teacher, MeetingRequest
from tools.meeting_tools import request_meeting, get_meeting_status, update_meeting_status

def render_meetings(student_id: int):
    """Renders the Faculty Consultation and Meeting Scheduling system in black and neon green."""
    st.markdown("## 🤝 Faculty Meeting Scheduler")
    st.caption("Schedule one-on-one academic consultations, resolve doubts, and track meeting approval states.")

    # Request Meeting Expander
    with st.expander("📅 Schedule New Meeting with Faculty", expanded=False):
        with st.form("request_meeting_form", clear_on_submit=True):
            col1, col2 = st.columns([1, 1])
            with col1:
                with get_db() as db:
                    teachers = db.query(Teacher).all()
                    teacher_map = {f"{t.name} ({t.designation})": t.id for t in teachers}
                chosen_t_str = st.selectbox("Select Faculty Member *", list(teacher_map.keys()))
                purpose = st.text_area("Meeting Purpose / Agenda *", placeholder="e.g. Discuss project deliverables and research guidance")

            with col2:
                req_date = st.date_input("Requested Date *", min_value=datetime.date.today(), value=datetime.date.today() + datetime.timedelta(days=2))
                req_time = st.selectbox("Requested Time Slot *", [
                    "09:30", "10:30", "11:30", "14:00", "15:00", "15:30", "16:30"
                ])
                st.caption("⚠️ Requests are verified against your lecture timetable before dispatch.")

            submitted = st.form_submit_button("Submit Meeting Request", type="primary", use_container_width=True)
            if submitted:
                if not purpose.strip():
                    st.error("Please provide a meeting purpose.")
                else:
                    teacher_id = teacher_map[chosen_t_str]
                    res = request_meeting(
                        student_id=student_id,
                        teacher_id=teacher_id,
                        purpose=purpose.strip(),
                        requested_date=str(req_date),
                        requested_time=req_time
                    )
                    if res.get("success"):
                        st.success(res.get("message"))
                        st.rerun()
                    else:
                        st.error(f"❌ {res.get('error')}")

    st.markdown("---")

    # Meeting List Tabs
    status_tabs = st.tabs(["Pending Approval", "Approved Consultations", "Past / Completed"])

    m_res = get_meeting_status(student_id)
    all_meetings = m_res.get("meetings", [])

    with status_tabs[0]:
        pending_list = [m for m in all_meetings if m["status"] == "Pending"]
        if not pending_list:
            st.info("No pending meeting requests.")
        for m in pending_list:
            st.markdown(f"""
            <div style="background-color: #14130A; border: 1.5px solid #FFB800; border-radius: 8px; padding: 1.1rem 1.25rem; margin-bottom: 0.75rem; box-shadow: 0 0 10px rgba(255,184,0,0.15);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 800; font-size: 1.15rem; color: #FFFFFF;">👨‍🏫 {m['teacher_name']}</span>
                    <span style="background-color: #FFB80025; color: #FFB800; border: 1px solid #FFB80060; padding: 0.25rem 0.65rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700;">
                        ⏳ Pending Faculty Approval
                    </span>
                </div>
                <div style="font-size: 0.88rem; color: #CCCCCC; margin-top: 0.5rem; line-height: 1.5;">
                    📅 <b>Date:</b> {m['requested_date']} at {m['requested_time']}<br>
                    📝 <b>Agenda:</b> {m['purpose']}
                </div>
                <div style="font-size: 0.8rem; color: #FFB800; margin-top: 0.5rem; font-style: italic;">
                    Notice: This meeting is awaiting faculty confirmation and is not yet final.
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Simulated faculty approval button for demonstration testing
            with st.expander("🛠️ Faculty Action (Simulation)", expanded=False):
                col_a, col_r = st.columns(2)
                with col_a:
                    if st.button("Simulate Faculty Approval", key=f"sim_app_{m['id']}", use_container_width=True):
                        update_meeting_status(m["id"], "Approved", "Meeting confirmed. Please be on time.")
                        st.success("Meeting status updated to Approved!")
                        st.rerun()
                with col_r:
                    if st.button("Simulate Faculty Rejection", key=f"sim_rej_{m['id']}", use_container_width=True):
                        update_meeting_status(m["id"], "Rejected", "Conflict with faculty committee meeting.")
                        st.info("Meeting rejected.")
                        st.rerun()

    with status_tabs[1]:
        approved_list = [m for m in all_meetings if m["status"] == "Approved"]
        if not approved_list:
            st.info("No approved meetings currently scheduled.")
        for m in approved_list:
            st.markdown(f"""
            <div style="background-color: #0A140E; border: 1.5px solid #00FF66; border-radius: 8px; padding: 1.1rem 1.25rem; margin-bottom: 0.75rem; box-shadow: 0 0 12px rgba(0,255,102,0.2);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 800; font-size: 1.15rem; color: #FFFFFF;">👨‍🏫 {m['teacher_name']}</span>
                    <span style="background-color: #00FF6625; color: #00FF66; border: 1px solid #00FF6660; padding: 0.25rem 0.65rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700;">
                        ✅ Confirmed Appointment
                    </span>
                </div>
                <div style="font-size: 0.88rem; color: #CCCCCC; margin-top: 0.5rem; line-height: 1.5;">
                    📅 <b>Date:</b> {m['requested_date']} at {m['requested_time']}<br>
                    📝 <b>Purpose:</b> {m['purpose']}<br>
                    💬 <b>Faculty Remarks:</b> <i style="color:#00FF66;">{m.get('teacher_notes', 'None')}</i>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with status_tabs[2]:
        past_list = [m for m in all_meetings if m["status"] in ["Completed", "Rejected"]]
        if not past_list:
            st.write("No archived or past consultations.")
        for m in past_list:
            st.markdown(f"""
            <div style="background-color: #121513; border: 1px solid #1E2922; border-radius: 8px; padding: 0.85rem 1rem; margin-bottom: 0.5rem; font-size: 0.85rem; color: #8C9990;">
                <b style="color:#FFFFFF;">{m['teacher_name']}</b> — Status: <b style="color:#A3A3A3;">{m['status']}</b> on {m['requested_date']}<br>
                <i>{m['purpose']}</i>
            </div>
            """, unsafe_allow_html=True)
