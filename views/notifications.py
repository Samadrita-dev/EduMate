import streamlit as st
from tools.notification_tools import (
    get_notifications, mark_notification_read, run_proactive_checks
)

def render_notifications(student_id: int):
    """Renders the in-app notification center in black and neon green."""
    st.markdown("## 🔔 Notification Center")
    st.caption("Stay informed about upcoming deadlines, attendance shortage warnings, and examination dates.")

    # Proactive Audit Trigger
    top_col1, top_col2 = st.columns([2, 1])
    with top_col1:
        st.write("EduMate monitors your academic status in the background and surfaces proactive alerts.")
    with top_col2:
        if st.button("⚡ Run Proactive Academic Audit", type="primary", use_container_width=True):
            with st.spinner("Auditing deadlines, exams, and attendance records..."):
                audit_res = run_proactive_checks(student_id)
                new_alerts = audit_res.get("new_alerts_count", 0)
                if new_alerts > 0:
                    st.success(f"Audit completed! Generated {new_alerts} new proactive notification(s).")
                else:
                    st.info("Audit completed: All notifications are up-to-date.")
                st.rerun()

    st.markdown("---")

    n_res = get_notifications(student_id)
    notifs = n_res.get("notifications", [])
    unread_count = n_res.get("unread_count", 0)

    st.write(f"You have **{unread_count} unread** notification(s) out of {len(notifs)} total.")

    if not notifs:
        st.info("No notifications at this time.")
        return

    # Notification category neon colors
    category_colors = {
        "Exam": "#FF3366",
        "Attendance": "#FFB800",
        "Assignment": "#00FF66",
        "Meeting": "#00E5FF",
        "Task": "#A855F7",
        "System": "#00FF66"
    }

    for n in notifs:
        cat = n.get("category", "System")
        color = category_colors.get(cat, "#00FF66")
        is_read = n.get("is_read", False)

        with st.container():
            st.markdown(f"""
            <div style="background-color: {'#101211' if is_read else '#0F1A13'}; border: 1px solid {'#1E2922' if is_read else '#00FF6640'}; border-left: 5px solid {color}; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 0.65rem; box-shadow: 0 0 10px {'transparent' if is_read else 'rgba(0,255,102,0.1)'};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; font-size: 1.1rem; color: #FFFFFF;">
                        {'⚪ ' if is_read else '🟢 '} <span style="color: {color};">[{cat}]</span> {n['title']}
                    </span>
                    <span style="font-size: 0.8rem; color: #8C9990;">
                        {n.get('created_at', '')[:16]}
                    </span>
                </div>
                <div style="font-size: 0.88rem; color: #CCCCCC; margin-top: 0.35rem;">
                    {n['message']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if not is_read:
                btn_c, _ = st.columns([1.5, 6])
                with btn_c:
                    if st.button("Mark Read", key=f"read_{n['id']}", use_container_width=True):
                        mark_notification_read(notification_id=n["id"], student_id=student_id)
                        st.rerun()
