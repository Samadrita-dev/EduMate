import streamlit as st
import datetime
import random
from database.db import get_db
from database.models import (
    Student, Subject, Teacher, AttendanceRecord,
    Examination, Assignment, Task, TimetableEntry
)
from sqlalchemy.orm import joinedload
from tools.attendance_tools import get_attendance, calculate_attendance, calculate_classes_needed


# ─────────────────────────────────────────────
#  HELPER FUNCTIONS
# ─────────────────────────────────────────────
def _load_all_students():
    with get_db() as db:
        return [s.to_dict() for s in db.query(Student).order_by(Student.id.asc()).all()]

def _load_subjects():
    with get_db() as db:
        rows = db.query(Subject).all()
        return {f"{s.code} - {s.name}": s.id for s in rows}

def _load_teachers():
    with get_db() as db:
        rows = db.query(Teacher).all()
        return {f"{t.name} ({t.department})": t.id for t in rows}

def _sync_student_attendance(student_id: int, subject_id: int, total_classes: int, attended_classes: int):
    """
    Reconciles AttendanceRecord rows in the database for a student and subject
    so that total records = total_classes, and Present records = attended_classes.
    """
    with get_db() as db:
        # Fetch existing records
        existing = (
            db.query(AttendanceRecord)
            .filter(AttendanceRecord.student_id == student_id, AttendanceRecord.subject_id == subject_id)
            .order_by(AttendanceRecord.date.asc())
            .all()
        )
        
        # Delete excess if existing is greater than total_classes
        if len(existing) > total_classes:
            to_remove = existing[total_classes:]
            for r in to_remove:
                db.delete(r)
            existing = existing[:total_classes]

        # Update status for existing records
        today = datetime.date.today()
        base_date = today - datetime.timedelta(days=total_classes + 5)
        
        # Determine statuses: first `attended_classes` are Present, rest Absent
        statuses = ["Present"] * attended_classes + ["Absent"] * (total_classes - attended_classes)
        # Randomize order slightly for natural distribution or keep sequential
        random.seed(student_id * 100 + subject_id)
        random.shuffle(statuses)

        for i, record in enumerate(existing):
            record.status = statuses[i]
            record.remarks = "Admin updated"

        # Add remaining records if total_classes > existing
        current_count = len(existing)
        for i in range(current_count, total_classes):
            sim_date = base_date + datetime.timedelta(days=i + 1)
            # Skip Sundays
            if sim_date.weekday() == 6:
                sim_date += datetime.timedelta(days=1)
            
            stat = statuses[i]
            db.add(AttendanceRecord(
                student_id=student_id,
                subject_id=subject_id,
                date=sim_date,
                status=stat,
                remarks="Admin provisioned"
            ))

        db.commit()


# ─────────────────────────────────────────────
#  MAIN RENDER
# ─────────────────────────────────────────────
def render_admin(current_student_id: int):
    st.markdown("## 🛠️ Student & Academic Management Center")
    st.caption("Administrative portal to register new students, configure attendance records, manage exams, assignments, and timetables.")

    tab_students, tab_attendance, tab_exams, tab_assignments, tab_tasks, tab_timetable = st.tabs([
        "👤 Student Profiles",
        "📈 Attendance Management",
        "📝 Examination Schedules",
        "📚 Course Assignments",
        "📋 Student Tasks",
        "🗓️ Class Timetable",
    ])

    # ══════════════════════════════════════════════════
    #  TAB 1 – STUDENT PROFILES
    # ══════════════════════════════════════════════════
    with tab_students:
        st.subheader("🎓 Registered Student Directory")
        students = _load_all_students()

        if students:
            # Display formatted summary table
            display_data = []
            for s in students:
                is_active = (s["id"] == st.session_state.get("active_student_id"))
                display_data.append({
                    "Active Profile": "⭐ ACTIVE" if is_active else "",
                    "Roll No": s["roll_no"],
                    "Full Name": s["name"],
                    "Email": s["email"],
                    "Department": s["department"],
                    "Semester": s["semester"],
                    "CGPA": f"{s['cgpa']:.2f}",
                })
            st.dataframe(display_data, use_container_width=True)
        else:
            st.info("No student profiles found.")

        st.markdown("---")

        col_add, col_edit = st.columns([1, 1])

        # ── Add New Student ───────────────────────────
        with col_add:
            with st.container(border=True):
                st.markdown("#### ➕ Register New Student")
                with st.form("add_student_form", clear_on_submit=True):
                    s_name = st.text_input("Full Name *", placeholder="e.g. Ananya Sen")
                    s_roll = st.text_input("Roll Number *", placeholder="e.g. CS2024045")
                    s_email = st.text_input("Email Address *", placeholder="e.g. ananya.sen@college.edu")
                    
                    c_d, c_s, c_c = st.columns(3)
                    with c_d:
                        s_dept = st.text_input("Department", value="Computer Science")
                    with c_s:
                        s_sem = st.number_input("Semester", min_value=1, max_value=8, value=5)
                    with c_c:
                        s_cgpa = st.number_input("Initial CGPA", min_value=0.0, max_value=10.0, value=8.5, step=0.1)

                    auto_seed = st.checkbox(
                        "Auto-enroll in semester subjects & initialize standard timetable & attendance",
                        value=True,
                        help="Automatically creates default timetable entries and baseline attendance records for all department subjects."
                    )

                    btn_add = st.form_submit_button("Register Student", type="primary", use_container_width=True)

                    if btn_add:
                        if not s_name.strip() or not s_roll.strip() or not s_email.strip():
                            st.error("Please fill in Name, Roll Number, and Email.")
                        else:
                            try:
                                with get_db() as db:
                                    # Check duplicate roll or email
                                    existing = db.query(Student).filter(
                                        (Student.roll_no == s_roll.strip()) | (Student.email == s_email.strip())
                                    ).first()
                                    if existing:
                                        st.error("A student with this Roll Number or Email already exists.")
                                    else:
                                        new_student = Student(
                                            name=s_name.strip(),
                                            roll_no=s_roll.strip(),
                                            email=s_email.strip(),
                                            department=s_dept.strip(),
                                            semester=int(s_sem),
                                            cgpa=float(s_cgpa),
                                        )
                                        db.add(new_student)
                                        db.commit()
                                        db.refresh(new_student)
                                        new_id = new_student.id

                                        # Auto seed if requested
                                        if auto_seed:
                                            subjects = db.query(Subject).all()
                                            # Add default timetable
                                            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                                            for idx, sub in enumerate(subjects):
                                                day = days[idx % len(days)]
                                                db.add(TimetableEntry(
                                                    student_id=new_id,
                                                    subject_id=sub.id,
                                                    teacher_id=sub.teacher_id,
                                                    day_of_week=day,
                                                    start_time="10:00",
                                                    end_time="11:30",
                                                    classroom="Room 302"
                                                ))
                                                # Seed default attendance (25 conducted, 20 attended ~ 80%)
                                                for d in range(25):
                                                    att_date = datetime.date.today() - datetime.timedelta(days=(25 - d) * 2)
                                                    status = "Present" if d % 5 != 0 else "Absent"
                                                    db.add(AttendanceRecord(
                                                        student_id=new_id,
                                                        subject_id=sub.id,
                                                        date=att_date,
                                                        status=status,
                                                        remarks="Initial enrollment baseline"
                                                    ))
                                            db.commit()

                                        st.session_state["active_student_id"] = new_id
                                        st.success(f"🎉 Student '{s_name.strip()}' registered successfully and set as Active!")
                                        st.rerun()
                            except Exception as e:
                                st.error(f"Error registering student: {e}")

        # ── Edit / Switch / Delete Student ────────────
        with col_edit:
            with st.container(border=True):
                st.markdown("#### ✏️ Manage Student Profile")
                students = _load_all_students()
                if not students:
                    st.info("No students available to edit.")
                else:
                    stu_map = {f"{s['name']} ({s['roll_no']})": s["id"] for s in students}
                    current_idx = 0
                    for idx, (label, sid) in enumerate(stu_map.items()):
                        if sid == st.session_state.get("active_student_id"):
                            current_idx = idx
                            break

                    chosen_label = st.selectbox("Select Student Profile", list(stu_map.keys()), index=current_idx)
                    sel_id = stu_map[chosen_label]
                    sel_student = next(s for s in students if s["id"] == sel_id)

                    # Quick switch active student button
                    if sel_id != st.session_state.get("active_student_id"):
                        if st.button(f"👉 Set '{sel_student['name']}' as Active App User", use_container_width=True):
                            st.session_state["active_student_id"] = sel_id
                            st.success(f"Switched active student to {sel_student['name']}!")
                            st.rerun()

                    with st.form("edit_student_form"):
                        e_name = st.text_input("Full Name", value=sel_student["name"])
                        e_roll = st.text_input("Roll No", value=sel_student["roll_no"])
                        e_email = st.text_input("Email", value=sel_student["email"])
                        e_dept = st.text_input("Department", value=sel_student["department"])
                        e_sem = st.number_input("Semester", min_value=1, max_value=8, value=sel_student["semester"])
                        e_cgpa = st.number_input("CGPA", min_value=0.0, max_value=10.0, value=float(sel_student["cgpa"]), step=0.1)

                        b_save, b_del = st.columns(2)
                        with b_save:
                            btn_save = st.form_submit_button("💾 Save Profile", type="primary", use_container_width=True)
                        with b_del:
                            btn_del = st.form_submit_button("🗑️ Delete Student", use_container_width=True)

                    if btn_save:
                        with get_db() as db:
                            rec = db.query(Student).filter(Student.id == sel_id).first()
                            if rec:
                                rec.name = e_name.strip()
                                rec.roll_no = e_roll.strip()
                                rec.email = e_email.strip()
                                rec.department = e_dept.strip()
                                rec.semester = int(e_sem)
                                rec.cgpa = float(e_cgpa)
                                db.commit()
                        st.success("✅ Student profile updated!")
                        st.rerun()

                    if btn_del:
                        with get_db() as db:
                            rec = db.query(Student).filter(Student.id == sel_id).first()
                            if rec:
                                db.delete(rec)
                                db.commit()
                        # Switch active student to first available
                        with get_db() as db:
                            first_s = db.query(Student).first()
                            if first_s:
                                st.session_state["active_student_id"] = first_s.id
                        st.warning("Student profile deleted.")
                        st.rerun()

    # ══════════════════════════════════════════════════
    #  TAB 2 – ATTENDANCE MANAGEMENT
    # ══════════════════════════════════════════════════
    with tab_attendance:
        st.subheader("📈 Attendance Management & Quick Updater")
        st.caption("Update subject-wise attendance percentages, batch mark session attendance, or edit historical logs.")

        students = _load_all_students()
        subj_map = _load_subjects()

        if not students or not subj_map:
            st.warning("Please ensure at least one student and one subject exist.")
        else:
            stu_map = {f"{s['name']} ({s['roll_no']})": s["id"] for s in students}
            
            # ── 1. FAST ATTENDANCE SUMMARY SETTER ─────────
            with st.container(border=True):
                st.markdown("#### ⚡ Quick Subject Attendance Setter")
                st.caption("Directly adjust or set the official total classes conducted and attended for any course.")

                q_col1, q_col2, q_col3 = st.columns([1.2, 1.2, 1.6])
                with q_col1:
                    fast_stu = st.selectbox("Select Student", list(stu_map.keys()), key="fast_att_stu")
                    fast_sid = stu_map[fast_stu]
                with q_col2:
                    fast_subj = st.selectbox("Select Course / Subject", list(subj_map.keys()), key="fast_att_subj")
                    fast_subid = subj_map[fast_subj]

                # Get current stats for selected student & subject
                with get_db() as db:
                    records = db.query(AttendanceRecord).filter(
                        AttendanceRecord.student_id == fast_sid,
                        AttendanceRecord.subject_id == fast_subid
                    ).all()
                    curr_total = len(records)
                    curr_attended = sum(1 for r in records if r.status in ["Present", "Excused"])
                    curr_pct = calculate_attendance(curr_attended, curr_total)

                with q_col3:
                    st.markdown(f"""
                    <div style="background-color: #121513; border: 1px solid #1E2922; border-left: 4px solid #00FF66; border-radius: 8px; padding: 0.85rem 1rem; box-shadow: 0 0 10px rgba(0,255,102,0.1);">
                        <span style="font-size: 0.85rem; color: #8C9990;">Current Official Record:</span><br>
                        <b style="font-size: 1.15rem; color: #FFFFFF;">{curr_attended} / {curr_total} sessions</b>
                        <span style="font-size: 1.15rem; font-weight: 800; color: {'#00FF66' if curr_pct >= 75 else '#FF3366'}; margin-left: 0.5rem; text-shadow: 0 0 8px {'rgba(0,255,102,0.3)' if curr_pct >= 75 else 'rgba(255,51,102,0.3)'};">
                            ({curr_pct}%)
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                with st.form("fast_sync_att_form"):
                    fc1, fc2, fc3 = st.columns(3)
                    with fc1:
                        new_total = st.number_input("Total Sessions Conducted", min_value=1, max_value=120, value=max(1, curr_total))
                    with fc2:
                        new_attended = st.number_input("Total Sessions Attended", min_value=0, max_value=int(new_total), value=min(curr_attended, int(new_total)))
                    with fc3:
                        proj_pct = calculate_attendance(new_attended, new_total)
                        st.markdown(f"<div style='margin-top: 1.7rem; font-size: 1.1rem; font-weight: 800; color: #00FF66; text-shadow: 0 0 8px rgba(0,255,102,0.3);'>Calculated: {proj_pct}%</div>", unsafe_allow_html=True)

                    btn_sync = st.form_submit_button("💾 Save & Sync Official Attendance Record", type="primary", use_container_width=True)
                    if btn_sync:
                        _sync_student_attendance(fast_sid, fast_subid, int(new_total), int(new_attended))
                        st.success(f"✅ Attendance updated for {fast_stu}! New record: {new_attended}/{new_total} ({proj_pct}%)")
                        st.rerun()

            st.markdown("---")

            # ── 2. SINGLE SESSION ATTENDANCE LOGGER ───────
            col_single, col_view = st.columns([1, 1.2])

            with col_single:
                with st.container(border=True):
                    st.markdown("#### 📅 Mark Single Class Attendance")
                    with st.form("mark_single_att_form", clear_on_submit=True):
                        s_stu = st.selectbox("Student *", list(stu_map.keys()), key="ms_stu")
                        s_sub = st.selectbox("Subject *", list(subj_map.keys()), key="ms_sub")
                        s_date = st.date_input("Class Date", value=datetime.date.today(), key="ms_date")
                        s_stat = st.selectbox("Status", ["Present", "Absent", "Excused"], key="ms_stat")
                        s_rem = st.text_input("Remarks", placeholder="e.g. Regular Lecture, Lab session", key="ms_rem")

                        btn_mark = st.form_submit_button("Mark Attendance", type="primary", use_container_width=True)
                        if btn_mark:
                            with get_db() as db:
                                existing = db.query(AttendanceRecord).filter(
                                    AttendanceRecord.student_id == stu_map[s_stu],
                                    AttendanceRecord.subject_id == subj_map[s_sub],
                                    AttendanceRecord.date == s_date
                                ).first()
                                if existing:
                                    existing.status = s_stat
                                    existing.remarks = s_rem or existing.remarks
                                    st.success(f"Updated attendance on {s_date} to {s_stat}!")
                                else:
                                    db.add(AttendanceRecord(
                                        student_id=stu_map[s_stu],
                                        subject_id=subj_map[s_sub],
                                        date=s_date,
                                        status=s_stat,
                                        remarks=s_rem or "Logged via Admin"
                                    ))
                                    st.success(f"Added attendance on {s_date}: {s_stat}")
                                db.commit()
                            st.rerun()

            # ── 3. DETAILED LOGS INSPECTOR & EDITOR ────────
            with col_view:
                with st.container(border=True):
                    st.markdown("#### 🔍 Historical Attendance Logs")
                    v_stu = st.selectbox("View Student Logs", list(stu_map.keys()), key="v_stu")
                    v_sid = stu_map[v_stu]

                    with get_db() as db:
                        records = (
                            db.query(AttendanceRecord)
                            .options(joinedload(AttendanceRecord.subject))
                            .filter(AttendanceRecord.student_id == v_sid)
                            .order_by(AttendanceRecord.date.desc())
                            .limit(100)
                            .all()
                        )
                        log_data = []
                        for r in records:
                            log_data.append({
                                "id": r.id,
                                "Date": str(r.date),
                                "Subject": r.subject.code if r.subject else "N/A",
                                "Status": r.status,
                                "Remarks": r.remarks or "",
                            })

                    if not log_data:
                        st.info("No attendance logs recorded yet for this student.")
                    else:
                        st.dataframe([{k: v for k, v in r.items() if k != "id"} for r in log_data[:15]], use_container_width=True)
                        st.caption(f"Showing newest 15 of {len(log_data)} total logs.")

                        # Quick edit/delete selector
                        log_labels = {f"{r['Date']} | {r['Subject']} | {r['Status']} (ID {r['id']})": r["id"] for r in log_data}
                        chosen_log = st.selectbox("Select record to modify", list(log_labels.keys()), key="sel_mod_log")
                        chosen_rec_id = log_labels[chosen_log]
                        rec_info = next(r for r in log_data if r["id"] == chosen_rec_id)

                        with st.form("mod_log_form"):
                            mc1, mc2 = st.columns(2)
                            with mc1:
                                new_log_stat = st.selectbox("Status", ["Present", "Absent", "Excused"],
                                                           index=["Present", "Absent", "Excused"].index(rec_info["Status"]))
                            with mc2:
                                new_log_rem = st.text_input("Remarks", value=rec_info["Remarks"])

                            bc1, bc2 = st.columns(2)
                            with bc1:
                                if st.form_submit_button("Update", type="primary", use_container_width=True):
                                    with get_db() as db:
                                        rec = db.query(AttendanceRecord).filter(AttendanceRecord.id == chosen_rec_id).first()
                                        if rec:
                                            rec.status = new_log_stat
                                            rec.remarks = new_log_rem
                                            db.commit()
                                    st.success("Record updated!")
                                    st.rerun()
                            with bc2:
                                if st.form_submit_button("Delete", use_container_width=True):
                                    with get_db() as db:
                                        rec = db.query(AttendanceRecord).filter(AttendanceRecord.id == chosen_rec_id).first()
                                        if rec:
                                            db.delete(rec)
                                            db.commit()
                                    st.warning("Record deleted!")
                                    st.rerun()

    # ══════════════════════════════════════════════════
    #  TAB 3 – EXAMINATION SCHEDULES
    # ══════════════════════════════════════════════════
    with tab_exams:
        st.subheader("📝 Examination Management")
        students = _load_all_students()
        subj_map = _load_subjects()

        if not students or not subj_map:
            st.warning("Please add students and subjects first.")
        else:
            stu_map = {f"{s['name']} ({s['roll_no']})": s["id"] for s in students}

            ex_col1, ex_col2 = st.columns([1, 1.2])

            with ex_col1:
                with st.container(border=True):
                    st.markdown("#### ➕ Schedule New Examination")
                    with st.form("add_exam_admin_form", clear_on_submit=True):
                        e_stu = st.selectbox("Student *", list(stu_map.keys()), key="adm_ex_stu")
                        e_subj = st.selectbox("Subject *", list(subj_map.keys()), key="adm_ex_subj")
                        e_type = st.selectbox("Exam Type", ["Midterm", "Final", "Practical", "Quiz", "Class Test"])
                        e_date = st.date_input("Exam Date *", min_value=datetime.date.today(), key="adm_ex_date")

                        tc1, tc2 = st.columns(2)
                        with tc1:
                            e_start = st.text_input("Start Time", value="10:00")
                        with tc2:
                            e_end = st.text_input("End Time", value="13:00")

                        vc1, vc2 = st.columns(2)
                        with vc1:
                            e_venue = st.text_input("Hall / Venue", value="Examination Hall A")
                        with vc2:
                            e_max = st.number_input("Max Marks", min_value=10, max_value=200, value=100)

                        e_syl = st.text_area("Syllabus Breakdown", placeholder="e.g. Modules 1 to 4 with numericals")

                        if st.form_submit_button("Schedule Exam", type="primary", use_container_width=True):
                            with get_db() as db:
                                db.add(Examination(
                                    student_id=stu_map[e_stu],
                                    subject_id=subj_map[e_subj],
                                    exam_type=e_type,
                                    exam_date=e_date,
                                    start_time=e_start,
                                    end_time=e_end,
                                    venue=e_venue,
                                    max_marks=int(e_max),
                                    syllabus=e_syl.strip() or "Standard curriculum",
                                    preparation_status="Not Started"
                                ))
                                db.commit()
                            st.success(f"Examination scheduled for {e_stu}!")
                            st.rerun()

            with ex_col2:
                with st.container(border=True):
                    st.markdown("#### 📋 Current Scheduled Examinations")
                    vx_stu = st.selectbox("Filter Student", list(stu_map.keys()), key="vx_stu")
                    vx_sid = stu_map[vx_stu]

                    with get_db() as db:
                        exams = (
                            db.query(Examination)
                            .options(joinedload(Examination.subject))
                            .filter(Examination.student_id == vx_sid)
                            .order_by(Examination.exam_date.asc())
                            .all()
                        )
                        exam_list = [{
                            "id": e.id,
                            "Course": e.subject.code if e.subject else "",
                            "Type": e.exam_type,
                            "Date": str(e.exam_date),
                            "Time": f"{e.start_time} - {e.end_time}",
                            "Venue": e.venue,
                            "Status": e.preparation_status,
                        } for e in exams]

                    if not exam_list:
                        st.info("No examinations scheduled for this student.")
                    else:
                        st.dataframe([{k: v for k, v in e.items() if k != "id"} for e in exam_list], use_container_width=True)

                        exam_opts = {f"{e['Date']} | {e['Course']} - {e['Type']}": e["id"] for e in exam_list}
                        sel_ex = st.selectbox("Select Exam to Edit/Delete", list(exam_opts.keys()), key="sel_ex_opt")
                        sel_eid = exam_opts[sel_ex]
                        curr_ex = next(e for e in exam_list if e["id"] == sel_eid)

                        with st.form("edit_exam_admin_form"):
                            ne_venue = st.text_input("Venue", value=curr_ex["Venue"])
                            ne_status = st.selectbox("Preparation Status", ["Not Started", "In Progress", "Prepared"],
                                                     index=["Not Started", "In Progress", "Prepared"].index(curr_ex["Status"]))
                            
                            ec1, ec2 = st.columns(2)
                            with ec1:
                                if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
                                    with get_db() as db:
                                        rec = db.query(Examination).filter(Examination.id == sel_eid).first()
                                        if rec:
                                            rec.venue = ne_venue
                                            rec.preparation_status = ne_status
                                            db.commit()
                                    st.success("Exam details updated!")
                                    st.rerun()
                            with ec2:
                                if st.form_submit_button("Delete Exam", use_container_width=True):
                                    with get_db() as db:
                                        rec = db.query(Examination).filter(Examination.id == sel_eid).first()
                                        if rec:
                                            db.delete(rec)
                                            db.commit()
                                    st.warning("Exam removed!")
                                    st.rerun()

    # ══════════════════════════════════════════════════
    #  TAB 4 – COURSE ASSIGNMENTS
    # ══════════════════════════════════════════════════
    with tab_assignments:
        st.subheader("📚 Course Assignment Management")
        students = _load_all_students()
        subj_map = _load_subjects()

        if not students or not subj_map:
            st.warning("Please add students and subjects first.")
        else:
            stu_map = {f"{s['name']} ({s['roll_no']})": s["id"] for s in students}
            as_col1, as_col2 = st.columns([1, 1.2])

            with as_col1:
                with st.container(border=True):
                    st.markdown("#### ➕ Assign Coursework")
                    with st.form("add_asgn_admin_form", clear_on_submit=True):
                        as_stu = st.selectbox("Student *", list(stu_map.keys()), key="adm_as_stu")
                        as_subj = st.selectbox("Course Subject *", list(subj_map.keys()), key="adm_as_subj")
                        as_title = st.text_input("Assignment Title *", placeholder="e.g. Distributed Database Sharding Lab")
                        as_desc = st.text_area("Description / Problem Details", placeholder="Detailed instructions...")

                        dc1, dc2 = st.columns(2)
                        with dc1:
                            as_due = st.date_input("Submission Deadline", min_value=datetime.date.today(), value=datetime.date.today() + datetime.timedelta(days=7))
                        with dc2:
                            as_pri = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)

                        as_marks = st.number_input("Maximum Marks", min_value=10, max_value=200, value=100)

                        if st.form_submit_button("Post Assignment", type="primary", use_container_width=True):
                            if not as_title.strip():
                                st.error("Title cannot be empty.")
                            else:
                                with get_db() as db:
                                    db.add(Assignment(
                                        student_id=stu_map[as_stu],
                                        subject_id=subj_map[as_subj],
                                        title=as_title.strip(),
                                        description=as_desc.strip() or None,
                                        due_date=as_due,
                                        priority=as_pri,
                                        max_marks=int(as_marks),
                                        status="Pending"
                                    ))
                                    db.commit()
                                st.success("Assignment successfully assigned!")
                                st.rerun()

            with as_col2:
                with st.container(border=True):
                    st.markdown("#### 📋 Existing Student Assignments")
                    vas_stu = st.selectbox("Filter by Student", list(stu_map.keys()), key="vas_stu")
                    vas_sid = stu_map[vas_stu]

                    with get_db() as db:
                        asgns = (
                            db.query(Assignment)
                            .options(joinedload(Assignment.subject))
                            .filter(Assignment.student_id == vas_sid)
                            .order_by(Assignment.due_date.asc())
                            .all()
                        )
                        asgn_list = [{
                            "id": a.id,
                            "Title": a.title,
                            "Course": a.subject.code if a.subject else "",
                            "Due": str(a.due_date),
                            "Priority": a.priority,
                            "Status": a.status,
                            "Marks": a.max_marks
                        } for a in asgns]

                    if not asgn_list:
                        st.info("No assignments found for this student.")
                    else:
                        st.dataframe([{k: v for k, v in a.items() if k != "id"} for a in asgn_list], use_container_width=True)

                        asgn_opts = {f"{a['Title']} (Due {a['Due']})": a["id"] for a in asgn_list}
                        sel_as = st.selectbox("Select Assignment to Update", list(asgn_opts.keys()), key="sel_as_opt")
                        sel_asid = asgn_opts[sel_as]
                        curr_as = next(a for a in asgn_list if a["id"] == sel_asid)

                        with st.form("upd_asgn_admin_form"):
                            new_as_stat = st.selectbox("Submission Status", ["Pending", "Submitted", "Graded", "Overdue"],
                                                      index=["Pending", "Submitted", "Graded", "Overdue"].index(curr_as["Status"]))
                            new_as_pri = st.selectbox("Priority Level", ["High", "Medium", "Low"],
                                                     index=["High", "Medium", "Low"].index(curr_as["Priority"]))

                            bc1, bc2 = st.columns(2)
                            with bc1:
                                if st.form_submit_button("Update Status", type="primary", use_container_width=True):
                                    with get_db() as db:
                                        rec = db.query(Assignment).filter(Assignment.id == sel_asid).first()
                                        if rec:
                                            rec.status = new_as_stat
                                            rec.priority = new_as_pri
                                            db.commit()
                                    st.success("Assignment updated!")
                                    st.rerun()
                            with bc2:
                                if st.form_submit_button("Delete Assignment", use_container_width=True):
                                    with get_db() as db:
                                        rec = db.query(Assignment).filter(Assignment.id == sel_asid).first()
                                        if rec:
                                            db.delete(rec)
                                            db.commit()
                                    st.warning("Assignment deleted.")
                                    st.rerun()

    # ══════════════════════════════════════════════════
    #  TAB 5 – STUDENT TASKS
    # ══════════════════════════════════════════════════
    with tab_tasks:
        st.subheader("📋 Student Task & Goal Management")
        students = _load_all_students()
        subj_map = _load_subjects()

        if not students:
            st.warning("Please register a student first.")
        else:
            stu_map = {f"{s['name']} ({s['roll_no']})": s["id"] for s in students}
            tk_col1, tk_col2 = st.columns([1, 1.2])

            with tk_col1:
                with st.container(border=True):
                    st.markdown("#### ➕ Add Academic Task")
                    with st.form("add_task_admin_form", clear_on_submit=True):
                        t_stu = st.selectbox("Student *", list(stu_map.keys()), key="adm_t_stu")
                        t_title = st.text_input("Task Title *", placeholder="e.g. Practice BCNF Decomposition")
                        t_desc = st.text_area("Task Description", placeholder="e.g. Solve questions 1-10")
                        t_subj = st.selectbox("Related Subject", ["General (No Subject)"] + list(subj_map.keys()), key="adm_t_subj")

                        tc1, tc2 = st.columns(2)
                        with tc1:
                            t_pri = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
                        with tc2:
                            t_due = st.date_input("Due Date", min_value=datetime.date.today(), value=datetime.date.today() + datetime.timedelta(days=3))

                        if st.form_submit_button("Add Task", type="primary", use_container_width=True):
                            if not t_title.strip():
                                st.error("Task title cannot be empty.")
                            else:
                                sub_id = subj_map.get(t_subj) if t_subj != "General (No Subject)" else None
                                with get_db() as db:
                                    db.add(Task(
                                        student_id=stu_map[t_stu],
                                        subject_id=sub_id,
                                        title=t_title.strip(),
                                        description=t_desc.strip() or None,
                                        priority=t_pri,
                                        due_date=t_due,
                                        status="Pending"
                                    ))
                                    db.commit()
                                st.success("Task added!")
                                st.rerun()

            with tk_col2:
                with st.container(border=True):
                    st.markdown("#### 📋 Current Tasks")
                    vt_stu = st.selectbox("Select Student", list(stu_map.keys()), key="adm_vt_stu")
                    vt_sid = stu_map[vt_stu]

                    with get_db() as db:
                        tasks = (
                            db.query(Task)
                            .options(joinedload(Task.subject))
                            .filter(Task.student_id == vt_sid)
                            .order_by(Task.due_date.asc())
                            .all()
                        )
                        task_list = [{
                            "id": t.id,
                            "Title": t.title,
                            "Subject": t.subject.code if t.subject else "General",
                            "Due": str(t.due_date),
                            "Priority": t.priority,
                            "Status": t.status,
                        } for t in tasks]

                    if not task_list:
                        st.info("No tasks recorded for this student.")
                    else:
                        st.dataframe([{k: v for k, v in t.items() if k != "id"} for t in task_list], use_container_width=True)

                        task_opts = {f"{t['Title']} ({t['Status']})": t["id"] for t in task_list}
                        sel_t = st.selectbox("Select Task to Modify", list(task_opts.keys()), key="adm_sel_task")
                        sel_tid = task_opts[sel_t]
                        curr_t = next(t for t in task_list if t["id"] == sel_tid)

                        with st.form("upd_task_admin_form"):
                            nt_stat = st.selectbox("Status", ["Pending", "Completed"],
                                                  index=["Pending", "Completed"].index(curr_t["Status"]) if curr_t["Status"] in ["Pending", "Completed"] else 0)
                            nt_pri = st.selectbox("Priority", ["High", "Medium", "Low"],
                                                 index=["High", "Medium", "Low"].index(curr_t["Priority"]))

                            bc1, bc2 = st.columns(2)
                            with bc1:
                                if st.form_submit_button("Update Task", type="primary", use_container_width=True):
                                    with get_db() as db:
                                        rec = db.query(Task).filter(Task.id == sel_tid).first()
                                        if rec:
                                            rec.status = nt_stat
                                            rec.priority = nt_pri
                                            db.commit()
                                    st.success("Task updated!")
                                    st.rerun()
                            with bc2:
                                if st.form_submit_button("Delete Task", use_container_width=True):
                                    with get_db() as db:
                                        rec = db.query(Task).filter(Task.id == sel_tid).first()
                                        if rec:
                                            db.delete(rec)
                                            db.commit()
                                    st.warning("Task deleted.")
                                    st.rerun()

    # ══════════════════════════════════════════════════
    #  TAB 6 – CLASS TIMETABLE
    # ══════════════════════════════════════════════════
    with tab_timetable:
        st.subheader("🗓️ Academic Timetable Manager")
        students = _load_all_students()
        subj_map = _load_subjects()
        teacher_map = _load_teachers()

        if not students or not subj_map:
            st.warning("Please add students and subjects first.")
        else:
            stu_map = {f"{s['name']} ({s['roll_no']})": s["id"] for s in students}
            DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

            tt_col1, tt_col2 = st.columns([1, 1.2])

            with tt_col1:
                with st.container(border=True):
                    st.markdown("#### ➕ Add Timetable Slot")
                    with st.form("add_tt_admin_form", clear_on_submit=True):
                        tt_stu = st.selectbox("Student *", list(stu_map.keys()), key="adm_tt_stu")
                        tt_subj = st.selectbox("Course Subject *", list(subj_map.keys()), key="adm_tt_subj")
                        tt_teach = st.selectbox("Faculty Instructor", ["Default Faculty"] + list(teacher_map.keys()), key="adm_tt_teach")
                        tt_day = st.selectbox("Day of Week", DAYS, key="adm_tt_day")

                        tc1, tc2 = st.columns(2)
                        with tc1:
                            tt_start = st.text_input("Start Time (HH:MM)", value="09:00")
                        with tc2:
                            tt_end = st.text_input("End Time (HH:MM)", value="10:30")

                        tt_room = st.text_input("Classroom Venue", value="Room 301")

                        if st.form_submit_button("Add Lecture Slot", type="primary", use_container_width=True):
                            teach_id = teacher_map.get(tt_teach) if tt_teach != "Default Faculty" else None
                            with get_db() as db:
                                db.add(TimetableEntry(
                                    student_id=stu_map[tt_stu],
                                    subject_id=subj_map[tt_subj],
                                    teacher_id=teach_id,
                                    day_of_week=tt_day,
                                    start_time=tt_start,
                                    end_time=tt_end,
                                    classroom=tt_room
                                ))
                                db.commit()
                            st.success("Timetable slot added!")
                            st.rerun()

            with tt_col2:
                with st.container(border=True):
                    st.markdown("#### 📋 Current Timetable Entries")
                    vtt_stu = st.selectbox("Select Student", list(stu_map.keys()), key="adm_vtt_stu")
                    vtt_sid = stu_map[vtt_stu]

                    with get_db() as db:
                        entries = (
                            db.query(TimetableEntry)
                            .options(joinedload(TimetableEntry.subject), joinedload(TimetableEntry.teacher))
                            .filter(TimetableEntry.student_id == vtt_sid)
                            .order_by(TimetableEntry.day_of_week, TimetableEntry.start_time)
                            .all()
                        )
                        tt_rows = [{
                            "id": e.id,
                            "Day": e.day_of_week,
                            "Subject": e.subject.code if e.subject else "",
                            "Time": f"{e.start_time} - {e.end_time}",
                            "Venue": e.classroom,
                            "Teacher": e.teacher.name if e.teacher else "Faculty",
                        } for e in entries]

                    if not tt_rows:
                        st.info("No timetable slots configured for this student.")
                    else:
                        st.dataframe([{k: v for k, v in r.items() if k != "id"} for r in tt_rows], use_container_width=True)

                        tt_opts = {f"{r['Day']} {r['Time']} | {r['Subject']}": r["id"] for r in tt_rows}
                        sel_tt = st.selectbox("Select Slot to Delete", list(tt_opts.keys()), key="adm_sel_tt")
                        sel_ttid = tt_opts[sel_tt]

                        if st.button("🗑️ Delete Selected Slot", type="primary", use_container_width=True):
                            with get_db() as db:
                                rec = db.query(TimetableEntry).filter(TimetableEntry.id == sel_ttid).first()
                                if rec:
                                    db.delete(rec)
                                    db.commit()
                            st.success("Slot deleted!")
                            st.rerun()
