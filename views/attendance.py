import streamlit as st
import plotly.graph_objects as go
from tools.attendance_tools import get_attendance, calculate_classes_needed
from utils.ui_components import render_metric_card, render_alert_box

def render_attendance(student_id: int):
    """Renders the official attendance tracking and shortage calculator module."""
    st.markdown("## 📊 Official Attendance Management")
    st.caption("Monitor course-by-course attendance records, identify debarment risks, and calculate required recovery classes.")

    att_res = get_attendance(student_id)
    if not att_res.get("success"):
        st.error(att_res.get("error", "Failed to retrieve attendance."))
        return

    overall_pct = att_res.get("overall_attendance_percentage", 0.0)
    attended_total = att_res.get("overall_classes_attended", 0)
    conducted_total = att_res.get("overall_total_classes", 0)
    subjects = att_res.get("subjects", [])

    # Official Policy Banner
    st.info("🔒 **Official Academic Policy ACAD-POL-04:** Minimum 75% attendance is required to appear in final examinations. Official logs are recorded directly by faculty.")

    # Top KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Aggregate Attendance", f"{overall_pct}%", "Across all registered courses")
    with col2:
        render_metric_card("Classes Attended", f"{attended_total}", f"Out of {conducted_total} sessions")
    with col3:
        absent_total = conducted_total - attended_total
        render_metric_card("Total Absences", f"{absent_total}", "Recorded unexcused absences")
    with col4:
        shortage_count = sum(1 for s in subjects if s["attendance_percentage"] < 75.0)
        status_sub = f"{shortage_count} subjects at risk" if shortage_count > 0 else "All subjects compliant"
        render_metric_card("Shortage Alerts", f"{shortage_count}", status_sub)

    # Check for Critical Warnings (< 65% debarment, or 65-75% condonation)
    for s in subjects:
        if s["attendance_percentage"] < 65.0:
            render_alert_box(
                f"🚨 DEBARMENT ALERT: {s['subject_name']} ({s['subject_code']})",
                f"Your attendance is currently **{s['attendance_percentage']}%** (below 65% hard floor). Under Senate rules, condonation is prohibited. You will receive an 'FA' grade unless immediate remediation is filed.",
                level="critical"
            )
        elif s["attendance_percentage"] < 75.0:
            needed = s["classes_needed_for_target"]
            render_alert_box(
                f"⚠️ ATTENDANCE SHORTAGE: {s['subject_name']} ({s['subject_code']})",
                f"Your attendance is **{s['attendance_percentage']}%** (Target: 75%). You must attend the next **{needed} consecutive classes** without absence to restore eligibility.",
                level="warning"
            )

    st.markdown("---")

    # Detailed Table
    st.subheader("📚 Subject-Wise Breakdown")
    table_data = []
    for s in subjects:
        table_data.append({
            "Subject Code": s["subject_code"],
            "Course Name": s["subject_name"],
            "Faculty": s["faculty_name"],
            "Conducted": s["total_classes"],
            "Attended": s["classes_attended"],
            "Absent": s["classes_absent"],
            "Attendance %": f"{s['attendance_percentage']}%",
            "Status": s["status_flag"],
            "Consecutive Needed": f"{s['classes_needed_for_target']} classes" if s["classes_needed_for_target"] > 0 else "0 (Safe)",
            "Safe Skips": f"{s['safe_skips_allowed']} classes"
        })
    st.dataframe(table_data, use_container_width=True)

    st.markdown("---")

    # Interactive Attendance Target Simulator / Calculator
    st.subheader("🧮 Interactive Target Attendance Calculator")
    st.caption("Simulate future class attendance and compute mathematically required sessions.")

    calc_col1, calc_col2 = st.columns(2)
    with calc_col1:
        subject_names = [s["subject_code"] + " - " + s["subject_name"] for s in subjects]
        chosen_sub_str = st.selectbox("Select Subject to Simulate", subject_names)
        chosen_code = chosen_sub_str.split(" - ")[0]
        selected_sub_obj = next(s for s in subjects if s["subject_code"] == chosen_code)

        target_pct = st.slider("Target Attendance Requirement (%)", min_value=60.0, max_value=95.0, value=75.0, step=1.0)

    with calc_col2:
        calc_res = calculate_classes_needed(
            classes_attended=selected_sub_obj["classes_attended"],
            total_classes=selected_sub_obj["total_classes"],
            target_percentage=target_pct
        )

        st.markdown(f"""
        <div style="background-color: #121513; border: 1.5px solid #00FF66; border-radius: 8px; padding: 1.25rem; box-shadow: 0 0 15px rgba(0, 255, 102, 0.15);">
            <div style="font-weight: 700; color: #00FF66; font-size: 1.15rem; text-shadow: 0 0 8px rgba(0,255,102,0.3);">Simulation Results for {chosen_code}</div>
            <div style="font-size: 0.9rem; color: #CCCCCC; margin-top: 0.5rem;">
                • Current Record: <b style="color:#FFFFFF;">{selected_sub_obj['classes_attended']} / {selected_sub_obj['total_classes']}</b> ({selected_sub_obj['attendance_percentage']}%)<br>
                • Desired Target: <b style="color:#00FF66;">{target_pct}%</b>
            </div>
            <div style="font-size: 1.3rem; font-weight: 800; color: #00FF66; margin-top: 0.75rem;">
                {'Need ' + str(calc_res.get('needed')) + ' consecutive classes' if calc_res.get('needed', 0) > 0 else 'Target achieved! Can safely miss ' + str(calc_res.get('safe_skips_allowed', 0)) + ' class(es)'}
            </div>
            <div style="font-size: 0.85rem; color: #8C9990; margin-top: 0.4rem;">
                {calc_res.get('message', '')}
            </div>
        </div>
        """, unsafe_allow_html=True)
