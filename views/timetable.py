import streamlit as st
import datetime
from tools.timetable_tools import get_timetable, get_available_slots, check_schedule_conflicts

def render_timetable(student_id: int):
    """Renders the daily and weekly timetable schedule in black and neon green."""
    st.markdown("## 🗓️ Academic Timetable & Schedule")
    st.caption("Review weekly lecture timings, locate open study periods, and test for scheduling conflicts.")

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    today_name = datetime.date.today().strftime("%A")
    default_index = days.index(today_name) if today_name in days else 0

    view_mode = st.radio("View Mode", ["Day View", "Full Week Overview"], horizontal=True)

    if view_mode == "Day View":
        selected_day = st.selectbox("Select Day of Week", days, index=default_index)
        tt_res = get_timetable(student_id, day_of_week=selected_day)
        entries = tt_res.get("entries", [])

        st.subheader(f"📅 Lecture Schedule for {selected_day}")
        if entries:
            for e in entries:
                st.markdown(f"""
                <div style="background-color: #121513; border: 1px solid #1E2922; border-left: 5px solid #00FF66; border-radius: 8px; padding: 1.1rem 1.25rem; margin-bottom: 0.75rem; box-shadow: 0 0 10px rgba(0,255,102,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700; font-size: 1.15rem; color: #FFFFFF;">{e['subject_name']} <span style="color:#00FF66;">({e['subject_code']})</span></span>
                        <span style="background-color: #00FF6625; color: #00FF66; border: 1px solid #00FF6660; font-weight: 700; padding: 0.2rem 0.65rem; border-radius: 9999px; font-size: 0.85rem;">
                            🕒 {e['start_time']} - {e['end_time']}
                        </span>
                    </div>
                    <div style="font-size: 0.88rem; color: #CCCCCC; margin-top: 0.4rem;">
                        📍 <b>Venue:</b> <span style="color:#00FF66;">{e['classroom']}</span> &nbsp;•&nbsp; 👨‍🏫 <b>Instructor:</b> {e['teacher_name']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No classes scheduled on {selected_day}.")

        st.markdown("---")

        # Open Study Slots Section
        st.subheader(f"⏳ Free Study Slots on {selected_day}")
        st.caption("Unoccupied windows between scheduled lectures suitable for focused revision or project work.")
        slots_res = get_available_slots(student_id, day_of_week=selected_day, start_window="08:30", end_window="18:00")
        free_slots = slots_res.get("available_slots", [])

        if free_slots:
            slot_cols = st.columns(min(3, len(free_slots)))
            for i, slot in enumerate(free_slots):
                with slot_cols[i % len(slot_cols)]:
                    st.markdown(f"""
                    <div style="background-color: #0F1A13; border: 1px solid #00FF6650; border-radius: 8px; padding: 0.85rem 1.1rem; margin-bottom: 0.5rem; box-shadow: 0 0 10px rgba(0,255,102,0.15);">
                        <div style="font-weight: 700; color: #00FF66;">🟢 Open Study Window</div>
                        <div style="font-size: 1.05rem; font-weight: 700; color: #FFFFFF; margin-top: 0.25rem;">
                            {slot['start_time']} - {slot['end_time']}
                        </div>
                        <div style="font-size: 0.82rem; color: #8C9990;">
                            Duration: {slot['duration_minutes']} minutes
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.write("No open windows found in the 08:30 - 18:00 schedule.")

    else:
        # Full Week Overview
        st.subheader("📆 Full Weekly Timetable Grid")
        all_res = get_timetable(student_id)
        entries = all_res.get("entries", [])

        week_cols = st.columns(5)
        for i, d in enumerate(days):
            with week_cols[i]:
                st.markdown(f"#### {d}")
                day_entries = [e for e in entries if e["day_of_week"] == d]
                if day_entries:
                    for e in day_entries:
                        st.markdown(f"""
                        <div style="background-color: #121513; border: 1px solid #1E2922; border-left: 3px solid #00FF66; border-radius: 6px; padding: 0.6rem 0.7rem; margin-bottom: 0.5rem; font-size: 0.8rem; box-shadow: 0 0 8px rgba(0,255,102,0.08);">
                            <b style="color:#00FF66;">{e['start_time']}-{e['end_time']}</b><br>
                            <span style="font-weight: 700; color: #FFFFFF;">{e['subject_code']}</span><br>
                            <span style="color: #A3A3A3;">{e['classroom']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("No classes")

    st.markdown("---")

    # Conflict Checker Tool
    with st.expander("🔍 Test Schedule Conflict Checker", expanded=False):
        c_day = st.selectbox("Conflict Check Day", days)
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            c_start = st.text_input("Proposed Start Time (HH:MM)", value="10:30")
        with c_col2:
            c_end = st.text_input("Proposed End Time (HH:MM)", value="11:30")

        if st.button("Check Conflict", type="primary"):
            res = check_schedule_conflicts(student_id, target_day=c_day, start_time=c_start, end_time=c_end)
            if res.get("has_conflict"):
                st.error("❌ Schedule Conflict Detected!")
                for c in res.get("conflicts", []):
                    st.write(f"- Overlaps with **{c['subject']}** ({c['time']}) in {c['classroom']}")
            else:
                st.success("✅ Slot is completely free! No timetable conflicts found.")
