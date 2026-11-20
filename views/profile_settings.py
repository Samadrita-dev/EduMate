import streamlit as st
from database.db import get_db
from database.models import Student
from memory.long_term import LongTermMemory
from memory.episodic import EpisodicMemory
from llm.client import OllamaClient
from config import OLLAMA_BASE_URL, OLLAMA_MODEL

def render_profile_settings(current_student_id: int):
    """Renders student profile controls, memory privacy management, and system settings."""
    st.markdown("## ⚙️ Profile & System Settings")
    st.caption("Manage active student identity, configure agent memory preferences, and inspect local LLM status.")

    ltm = LongTermMemory(current_student_id)
    epm = EpisodicMemory(current_student_id)

    # Student Profile Switching (Multi-student demonstration)
    st.subheader("👤 Student Account & Session Identity")
    with get_db() as db:
        all_students = db.query(Student).all()
        student_opts = {f"{s.name} ({s.roll_no} - {s.department})": s.id for s in all_students}

    current_label = next((k for k, v in student_opts.items() if v == current_student_id), list(student_opts.keys())[0])
    selected_student = st.selectbox("Active Student Session", list(student_opts.keys()), index=list(student_opts.keys()).index(current_label))

    new_id = student_opts[selected_student]
    if new_id != current_student_id:
        st.session_state["active_student_id"] = new_id
        st.success(f"Switched session to {selected_student}!")
        st.rerun()

    st.markdown("---")

    # Long-Term Memory & User Privacy Controls
    st.subheader("🧠 Long-Term Memory (Student-Approved Preferences)")
    st.caption("The agent remembers these preferences across conversations. Under privacy requirements, you can review or delete any saved memory.")

    prefs = ltm.get_preferences()
    if prefs:
        for p in prefs:
            p_col1, p_col2 = st.columns([5, 1])
            with p_col1:
                st.markdown(f"• **{p['key'].replace('_', ' ').title()}:** {p['value']}")
            with p_col2:
                if st.button("Delete", key=f"del_mem_{p['id']}"):
                    ltm.delete_preference(p["id"])
                    st.success("Memory deleted!")
                    st.rerun()
    else:
        st.info("No long-term preferences saved.")

    # Add New Preference Form
    with st.expander("➕ Save New Personal Preference to Agent Memory", expanded=False):
        with st.form("new_memory_form", clear_on_submit=True):
            mem_key = st.text_input("Preference Key (e.g. preferred_study_time, focus_subject)")
            mem_val = st.text_input("Preference Value (e.g. Prefers studying early morning before 8 AM)")
            save_btn = st.form_submit_button("Save Preference")
            if save_btn:
                if not mem_key.strip() or not mem_val.strip():
                    st.error("Both key and value are required.")
                else:
                    res = ltm.set_preference(key=mem_key.strip(), value=mem_val.strip())
                    if res.get("success"):
                        st.success("Preference saved to long-term memory!")
                        st.rerun()
                    else:
                        st.error(res.get("error"))

    st.markdown("---")

    # Episodic Recollections
    st.subheader("📜 Episodic Memory")
    st.caption("Historical recollections of approved plans and significant student interactions.")
    episodes = epm.get_episodes()
    if episodes:
        for ep in episodes:
            st.markdown(f"- **{ep['key']}:** {ep['value']} &nbsp;*(Saved: {ep.get('created_at', '')[:10]})*")
    else:
        st.write("No episodic memories logged.")

    st.markdown("---")

    # Local LLM (Ollama) Settings
    st.subheader("🤖 Local LLM (Ollama) Diagnostics")
    llm = OllamaClient()
    conn = llm.check_connection()

    st.text_input("Ollama Base URL", value=OLLAMA_BASE_URL, disabled=True)
    st.text_input("Ollama Active Model", value=OLLAMA_MODEL, disabled=True)

    if conn["available"]:
        st.success(f"Connected to local Ollama. Available local models: {', '.join(conn.get('available_models', []))}")
    else:
        st.warning(conn["message"])
