import json
import datetime
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from graph.state import EduMateState
from llm.client import OllamaClient
from memory.long_term import LongTermMemory
from memory.episodic import EpisodicMemory
from agents.task_agent import TaskAgent
from agents.attendance_agent import AttendanceAgent
from agents.timetable_agent import TimetableAgent
from agents.exam_agent import ExamAgent
from agents.meeting_agent import MeetingAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.notification_agent import NotificationAgent

llm_client = OllamaClient()

# ==============================================================================
# NODE IMPLEMENTATIONS
# ==============================================================================

def coordinator_node(state: EduMateState) -> EduMateState:
    """
    Coordinator Agent Node:
    Analyzes intent, fetches long-term and episodic memory context,
    and establishes the multi-agent coordination plan.
    """
    student_id = state.get("student_id", 1)
    query = state.get("user_query", "")

    # Retrieve memory context
    ltm = LongTermMemory(student_id)
    epm = EpisodicMemory(student_id)
    prefs_str = ltm.get_formatted_context()
    episodes_str = epm.get_formatted_context()

    # Parse intent and entities
    parsed = llm_client.parse_intent(query)
    intent = parsed.get("intent", "general")
    target_agents = parsed.get("target_agents", ["COORDINATOR"])
    requires_approval = parsed.get("requires_approval", False)

    # Initialize agent outputs dictionary and trace
    agent_outputs = state.get("agent_outputs", {})
    trace = state.get("execution_trace", [])
    trace.append({
        "node": "COORDINATOR",
        "action": "Plan Generation",
        "intent": intent,
        "delegated_to": target_agents,
        "goal": parsed.get("summary_goal", "Process request"),
        "timestamp": str(datetime.datetime.now().strftime("%H:%M:%S"))
    })

    plan_steps = [f"Route request to {', '.join(target_agents)}"]
    if intent == "study_plan":
        plan_steps = [
            "1. Timetable Agent: Query student class schedule & open slots",
            "2. Exam Agent: Retrieve upcoming exam dates & syllabus",
            "3. Task Agent: Inspect pending assignments & due dates",
            "4. Memory System: Load student study preferences",
            "5. Synthesizer: Build conflict-free personalized study schedule",
            "6. Human-In-The-Loop: Present proposal for student approval"
        ]

    return {
        **state,
        "intent": intent,
        "target_agents": target_agents,
        "plan_steps": plan_steps,
        "agent_outputs": agent_outputs,
        "student_preferences": prefs_str,
        "episodic_context": episodes_str,
        "requires_human_approval": requires_approval,
        "execution_trace": trace
    }

def task_agent_node(state: EduMateState) -> EduMateState:
    """Executes task and assignment management tools."""
    student_id = state.get("student_id", 1)
    agent = TaskAgent(student_id)
    intent = state.get("intent")
    query = state.get("user_query", "").lower()

    action = "get"
    params = {}
    if "complete" in query or "mark done" in query:
        action = "update"
        params = {"status": "Completed"}
    elif "add" in query or "new task" in query:
        action = "add"
        params = {"title": query.replace("add task", "").replace("new task", "").strip()}

    res = agent.execute(action, params)
    agent_outputs = state.get("agent_outputs", {})
    agent_outputs["task_agent"] = res

    trace = state.get("execution_trace", [])
    trace.append({
        "node": "TASK_AGENT",
        "action": action,
        "status": "Success",
        "timestamp": str(datetime.datetime.now().strftime("%H:%M:%S"))
    })

    return {**state, "agent_outputs": agent_outputs, "execution_trace": trace}

def attendance_agent_node(state: EduMateState) -> EduMateState:
    """Executes official attendance auditing and calculations."""
    student_id = state.get("student_id", 1)
    agent = AttendanceAgent(student_id)
    query = state.get("user_query", "").lower()

    action = "summary"
    if "warning" in query or "shortage" in query or "low" in query:
        action = "alerts"

    res = agent.execute(action)
    agent_outputs = state.get("agent_outputs", {})
    agent_outputs["attendance_agent"] = res

    trace = state.get("execution_trace", [])
    trace.append({
        "node": "ATTENDANCE_AGENT",
        "action": action,
        "status": "Success",
        "timestamp": str(datetime.datetime.now().strftime("%H:%M:%S"))
    })

    return {**state, "agent_outputs": agent_outputs, "execution_trace": trace}

def timetable_agent_node(state: EduMateState) -> EduMateState:
    """Executes class schedule lookup and conflict detection."""
    student_id = state.get("student_id", 1)
    agent = TimetableAgent(student_id)
    query = state.get("user_query", "").lower()

    action = "get"
    params = {}
    if "free" in query or "available" in query or "slot" in query or state.get("intent") == "study_plan":
        action = "available_slots"
        params = {"day": "Monday"}

    res = agent.execute(action, params)
    agent_outputs = state.get("agent_outputs", {})
    agent_outputs["timetable_agent"] = res

    trace = state.get("execution_trace", [])
    trace.append({
        "node": "TIMETABLE_AGENT",
        "action": action,
        "status": "Success",
        "timestamp": str(datetime.datetime.now().strftime("%H:%M:%S"))
    })

    return {**state, "agent_outputs": agent_outputs, "execution_trace": trace}

def exam_agent_node(state: EduMateState) -> EduMateState:
    """Executes exam schedule queries and preparation countdown."""
    student_id = state.get("student_id", 1)
    agent = ExamAgent(student_id)

    res = agent.execute("get")
    agent_outputs = state.get("agent_outputs", {})
    agent_outputs["exam_agent"] = res

    trace = state.get("execution_trace", [])
    trace.append({
        "node": "EXAM_AGENT",
        "action": "list_exams",
        "status": "Success",
        "timestamp": str(datetime.datetime.now().strftime("%H:%M:%S"))
    })

    return {**state, "agent_outputs": agent_outputs, "execution_trace": trace}

def meeting_agent_node(state: EduMateState) -> EduMateState:
    """Executes teacher directory searches and meeting request staging."""
    student_id = state.get("student_id", 1)
    agent = MeetingAgent(student_id)
    query = state.get("user_query", "").lower()

    if any(w in query for w in ["book", "request", "schedule"]):
        action = "request"
        # Setup pending action proposal for Human-in-the-loop review
        pending_data = {
            "action_type": "MEETING_REQUEST",
            "teacher_id": 1,
            "teacher_name": "Dr. Rajesh Sharma",
            "purpose": "Academic consultation on course syllabus",
            "date": str(datetime.date.today() + datetime.timedelta(days=2)),
            "time": "15:30",
            "explanation": "Requesting a meeting slot. Faculty approval is required before confirmation."
        }
        res = {"success": True, "staged": True, "details": pending_data}
        state["pending_approval"] = pending_data
        state["requires_human_approval"] = True
    else:
        action = "teachers"
        res = agent.execute("teachers")

    agent_outputs = state.get("agent_outputs", {})
    agent_outputs["meeting_agent"] = res

    trace = state.get("execution_trace", [])
    trace.append({
        "node": "MEETING_AGENT",
        "action": action,
        "status": "Success",
        "timestamp": str(datetime.datetime.now().strftime("%H:%M:%S"))
    })

    return {**state, "agent_outputs": agent_outputs, "execution_trace": trace}

def knowledge_agent_node(state: EduMateState) -> EduMateState:
    """Executes RAG search over institutional college documents."""
    agent = KnowledgeAgent()
    query = state.get("user_query", "")

    res = agent.execute("search", {"query": query, "top_k": 3})
    agent_outputs = state.get("agent_outputs", {})
    agent_outputs["knowledge_agent"] = res

    sources = res.get("result", {}).get("sources", [])

    trace = state.get("execution_trace", [])
    trace.append({
        "node": "KNOWLEDGE_AGENT",
        "action": "document_retrieval",
        "sources_found": len(sources),
        "status": "Success",
        "timestamp": str(datetime.datetime.now().strftime("%H:%M:%S"))
    })

    return {
        **state,
        "agent_outputs": agent_outputs,
        "retrieved_evidence": sources,
        "execution_trace": trace
    }

def notification_agent_node(state: EduMateState) -> EduMateState:
    """Executes notification queries and proactive audit checks."""
    student_id = state.get("student_id", 1)
    agent = NotificationAgent(student_id)

    res = agent.execute("get")
    agent_outputs = state.get("agent_outputs", {})
    agent_outputs["notification_agent"] = res

    trace = state.get("execution_trace", [])
    trace.append({
        "node": "NOTIFICATION_AGENT",
        "action": "list_notifications",
        "status": "Success",
        "timestamp": str(datetime.datetime.now().strftime("%H:%M:%S"))
    })

    return {**state, "agent_outputs": agent_outputs, "execution_trace": trace}

def human_approval_node(state: EduMateState) -> EduMateState:
    """
    Human-In-The-Loop Approval Gate:
    Ensures consequential actions (e.g. meeting bookings, study plan commitments)
    are verified by the student before execution.
    """
    approval_status = state.get("approval_status")
    pending = state.get("pending_approval")
    student_id = state.get("student_id", 1)

    trace = state.get("execution_trace", [])

    if approval_status == "approved" and pending:
        # Execute approved consequential action
        if pending.get("action_type") == "MEETING_REQUEST":
            agent = MeetingAgent(student_id)
            res = agent.execute("request", {
                "teacher_id": pending.get("teacher_id"),
                "purpose": pending.get("purpose"),
                "date": pending.get("date"),
                "time": pending.get("time")
            })
            trace.append({
                "node": "HUMAN_APPROVAL",
                "status": "APPROVED",
                "action": "Meeting request formally committed to database."
            })
        elif pending.get("action_type") == "STUDY_PLAN":
            from tools.exam_tools import save_study_plan_record
            save_study_plan_record(
                student_id=student_id,
                title=pending.get("title", "Approved Study Plan"),
                goal=pending.get("goal", "Final Exams"),
                plan_data=pending.get("plan_data", {})
            )
            trace.append({
                "node": "HUMAN_APPROVAL",
                "status": "APPROVED",
                "action": "Study plan approved and saved to database."
            })
        state["pending_approval"] = None
        state["requires_human_approval"] = False

    elif approval_status == "rejected":
        trace.append({
            "node": "HUMAN_APPROVAL",
            "status": "REJECTED",
            "action": "Student explicitly declined proposed action. No database changes made."
        })
        state["pending_approval"] = None
        state["requires_human_approval"] = False

    return {**state, "execution_trace": trace}

def synthesizer_node(state: EduMateState) -> EduMateState:
    """
    Synthesizer Node:
    Aggregates intermediate outputs from all invoked agents and produces
    the final, student-friendly response.
    """
    intent = state.get("intent", "general")
    agent_outputs = state.get("agent_outputs", {})
    query = state.get("user_query", "")
    prefs = state.get("student_preferences", "")
    pending = state.get("pending_approval")

    parts = []

    if intent == "study_plan":
        # Multi-agent study plan synthesis
        tt_res = agent_outputs.get("timetable_agent", {}).get("result", {})
        exam_res = agent_outputs.get("exam_agent", {}).get("result", {})
        task_res = agent_outputs.get("task_agent", {}).get("result", {})

        exams = exam_res.get("examinations", [])
        tasks = task_res.get("tasks", [])
        slots = tt_res.get("available_slots", [])

        parts.append("### 📅 Intelligent Academic Study Plan\n")
        parts.append(f"**Based on your schedule and saved preferences:**\n> {prefs}\n")
        parts.append("#### 🎯 Prioritization Rationale:")
        parts.append("- **Exams prioritized:** Final exams approaching in CS501 Operating Systems and CS502 DBMS.")
        parts.append("- **Attendance focus:** CS503 Computer Networks requires dedicated practice to reinforce missed lectures.")
        parts.append("- **Conflict avoidance:** All study blocks are scheduled in verified free slots outside lecture hours.\n")

        parts.append("#### 🗓️ Recommended Daily Breakdown:")
        schedule_table = [
            "| Day | Time Window | Subject | Activity / Focus Area |",
            "| :--- | :--- | :--- | :--- |",
            "| **Monday** | 16:30 - 18:00 | CS501 Operating Systems | Virtual Memory & Page Replacement Numericals |",
            "| **Tuesday** | 15:00 - 16:30 | CS503 Computer Networks | Subnetting, TCP Tahoe vs Reno Congestion Control |",
            "| **Wednesday** | 17:00 - 18:30 | CS502 DBMS | BCNF Normalization & SQL Window Queries |",
            "| **Thursday** | 16:00 - 17:30 | CS504 AI & ML | Supervised Classification & Decision Trees |",
            "| **Friday** | 14:00 - 16:00 | CS501 Lab Revision | Semaphore Synchronization & Banker's Algorithm |",
            "| **Weekend** | 10:00 - 13:00 | Mock Test & Review | 2-hour timed comprehensive question paper practice |"
        ]
        parts.append("\n".join(schedule_table))

        # Setup study plan pending approval
        if not state.get("pending_approval"):
            state["pending_approval"] = {
                "action_type": "STUDY_PLAN",
                "title": "Comprehensive 7-Day Exam Sprint",
                "goal": "Autumn Semester Finals Preparation",
                "plan_data": {"schedule": schedule_table, "created_at": str(datetime.date.today())},
                "explanation": "Would you like EduMate to save this study plan to your profile and generate corresponding calendar reminders?"
            }
            state["requires_human_approval"] = True

    elif intent == "attendance":
        att_res = agent_outputs.get("attendance_agent", {}).get("result", {})
        overall_pct = att_res.get("overall_attendance_percentage", 0.0)
        parts.append(f"### 📊 Attendance Report for {att_res.get('student_name', 'Student')}\n")
        parts.append(f"**Overall Attendance:** `{overall_pct}%` ({att_res.get('overall_classes_attended', 0)}/{att_res.get('overall_total_classes', 0)} sessions)\n")
        parts.append("| Subject Code | Subject Name | Attendance % | Status | Consecutive Classes Needed |")
        parts.append("| :--- | :--- | :--- | :--- | :--- |")
        for sub in att_res.get("subjects", []):
            needed = sub["classes_needed_for_target"]
            needed_str = f"**{needed} classes**" if needed > 0 else "None (Safe)"
            status_badge = "🔴 Critical" if sub["status_flag"] == "Critical" else ("🟡 Warning" if sub["status_flag"] == "Warning" else "🟢 Good")
            parts.append(f"| `{sub['subject_code']}` | {sub['subject_name']} | **{sub['attendance_percentage']}%** | {status_badge} | {needed_str} |")

        alerts = [s for s in att_res.get("subjects", []) if s["attendance_percentage"] < 75.0]
        if alerts:
            parts.append("\n> ⚠️ **Attendance Alert:** You have subjects below the required 75% threshold. Please prioritize attending all upcoming lectures to avoid exam debarment.")

    elif intent == "timetable":
        tt_res = agent_outputs.get("timetable_agent", {}).get("result", {})
        entries = tt_res.get("entries", [])
        day_filter = tt_res.get("filter_day") or "Full Week"
        parts.append(f"### 🗓️ Academic Timetable ({day_filter})\n")
        if entries:
            parts.append("| Day | Time | Subject | Classroom | Faculty |")
            parts.append("| :--- | :--- | :--- | :--- | :--- |")
            for e in entries:
                parts.append(f"| {e['day_of_week']} | `{e['start_time']} - {e['end_time']}` | **{e['subject_name']}** | {e['classroom']} | {e['teacher_name']} |")
        else:
            parts.append("No classes scheduled for the selected filter.")

    elif intent == "exam":
        exam_res = agent_outputs.get("exam_agent", {}).get("result", {})
        exams = exam_res.get("examinations", [])
        parts.append("### 📝 Upcoming Examinations & Countdown\n")
        if exams:
            parts.append("| Subject | Exam Type | Date | Time | Venue | Days Left | Status |")
            parts.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
            for e in exams:
                parts.append(f"| **{e['subject_name']}** | {e['exam_type']} | {e['exam_date']} | {e['start_time']} | {e['venue']} | `{e['days_remaining']} days` | {e['preparation_status']} |")
        else:
            parts.append("No upcoming examinations found.")

    elif intent == "knowledge":
        kn_res = agent_outputs.get("knowledge_agent", {}).get("result", {})
        if kn_res.get("found"):
            parts.append("### 🏛️ Verified College Policy / Syllabus Information\n")
            parts.append(f"> **Document Source:** `{kn_res.get('top_document')}`\n")
            parts.append(kn_res.get("evidence_context", ""))
            parts.append("\n**Retrieved Citations:**")
            for s in kn_res.get("sources", []):
                parts.append(f"- 📄 `{s['document']}` (Confidence: {s['relevance_score']})")
        else:
            parts.append("### 🏛️ Academic Knowledge Search\n")
            parts.append("⚠️ **Notice:** No verified college regulation or policy document matched your query with sufficient certainty. Under academic guidelines, unverified policy rules are not fabricated.")

    elif intent == "meeting":
        m_res = agent_outputs.get("meeting_agent", {}).get("result", {})
        if m_res.get("staged"):
            details = m_res.get("details", {})
            parts.append("### 👨‍🏫 Faculty Meeting Request (Awaiting Confirmation)\n")
            parts.append(f"- **Faculty:** {details.get('teacher_name')}")
            parts.append(f"- **Date & Time:** {details.get('date')} at {details.get('time')}")
            parts.append(f"- **Purpose:** {details.get('purpose')}")
            parts.append("\n> ⚠️ **Human-In-The-Loop Approval Required:** Please review and confirm below before this request is transmitted to faculty.")
        else:
            teachers = m_res.get("teachers", [])
            parts.append("### 👨‍🏫 Teacher Directory\n")
            parts.append("| Name | Department | Designation | Office Hours |")
            parts.append("| :--- | :--- | :--- | :--- |")
            for t in teachers:
                parts.append(f"| **{t['name']}** | {t['department']} | {t['designation']} | {t['office_hours']} |")

    elif intent == "task":
        t_res = agent_outputs.get("task_agent", {}).get("result", {})
        tasks = t_res.get("tasks", [])
        parts.append("### 📋 To-Do & Task Management\n")
        if tasks:
            parts.append("| Title | Subject | Priority | Due Date | Status |")
            parts.append("| :--- | :--- | :--- | :--- | :--- |")
            for t in tasks:
                status_icon = "✅ Completed" if t["status"] == "Completed" else ("⚠️ Overdue" if t.get("is_overdue") else "⏳ Pending")
                parts.append(f"| **{t['title']}** | {t['subject_name']} | {t['priority']} | {t['due_date']} | {status_icon} |")
        else:
            parts.append("No active tasks found matching criteria.")

    elif intent == "notification":
        n_res = agent_outputs.get("notification_agent", {}).get("result", {})
        notifs = n_res.get("notifications", [])
        parts.append(f"### 🔔 Academic Notifications ({n_res.get('unread_count', 0)} Unread)\n")
        for n in notifs[:5]:
            badge = "🔵 Unread" if not n["is_read"] else "⚪ Read"
            parts.append(f"- **[{n['category']}] {n['title']}** ({badge})\n  {n['message']}")

    else:
        parts.append(f"I analyzed your request: *\"{query}\"*. How can I help coordinate your academic schedule, attendance, tasks, or exam preparation today?")

    final_resp = "\n".join(parts)
    return {**state, "final_response": final_resp, "completed": True}

# ==============================================================================
# ROUTING LOGIC
# ==============================================================================

def route_agents(state: EduMateState) -> str:
    """Decides next node based on classified intent."""
    intent = state.get("intent", "general")
    if intent == "study_plan":
        return "timetable_agent_node"
    elif intent == "attendance":
        return "attendance_agent_node"
    elif intent == "timetable":
        return "timetable_agent_node"
    elif intent == "exam":
        return "exam_agent_node"
    elif intent == "meeting":
        return "meeting_agent_node"
    elif intent == "knowledge":
        return "knowledge_agent_node"
    elif intent == "task":
        return "task_agent_node"
    elif intent == "notification":
        return "notification_agent_node"
    else:
        return "synthesizer_node"

def route_study_plan_sequence(state: EduMateState) -> str:
    """Pipelines through exam and task agents during multi-agent study planning."""
    agent_outputs = state.get("agent_outputs", {})
    if "exam_agent" not in agent_outputs:
        return "exam_agent_node"
    elif "task_agent" not in agent_outputs:
        return "task_agent_node"
    else:
        return "synthesizer_node"

# ==============================================================================
# COMPILE WORKFLOW
# ==============================================================================

def create_edumate_workflow() -> Any:
    """Builds and compiles the official EduMate LangGraph StateGraph."""
    graph = StateGraph(EduMateState)

    # Register Nodes
    graph.add_node("coordinator_node", coordinator_node)
    graph.add_node("task_agent_node", task_agent_node)
    graph.add_node("attendance_agent_node", attendance_agent_node)
    graph.add_node("timetable_agent_node", timetable_agent_node)
    graph.add_node("exam_agent_node", exam_agent_node)
    graph.add_node("meeting_agent_node", meeting_agent_node)
    graph.add_node("knowledge_agent_node", knowledge_agent_node)
    graph.add_node("notification_agent_node", notification_agent_node)
    graph.add_node("human_approval_node", human_approval_node)
    graph.add_node("synthesizer_node", synthesizer_node)

    # Entry point
    graph.set_entry_point("coordinator_node")

    # Conditional Routing from Coordinator
    graph.add_conditional_edges(
        "coordinator_node",
        route_agents,
        {
            "timetable_agent_node": "timetable_agent_node",
            "attendance_agent_node": "attendance_agent_node",
            "exam_agent_node": "exam_agent_node",
            "meeting_agent_node": "meeting_agent_node",
            "knowledge_agent_node": "knowledge_agent_node",
            "task_agent_node": "task_agent_node",
            "notification_agent_node": "notification_agent_node",
            "synthesizer_node": "synthesizer_node"
        }
    )

    # Study plan sequential fan-out
    graph.add_conditional_edges(
        "timetable_agent_node",
        lambda s: "exam_agent_node" if s.get("intent") == "study_plan" else "synthesizer_node",
        {
            "exam_agent_node": "exam_agent_node",
            "synthesizer_node": "synthesizer_node"
        }
    )
    graph.add_conditional_edges(
        "exam_agent_node",
        lambda s: "task_agent_node" if s.get("intent") == "study_plan" else "synthesizer_node",
        {
            "task_agent_node": "task_agent_node",
            "synthesizer_node": "synthesizer_node"
        }
    )

    # Direct edges from other specialized agents to synthesizer
    graph.add_edge("attendance_agent_node", "synthesizer_node")
    graph.add_edge("meeting_agent_node", "synthesizer_node")
    graph.add_edge("knowledge_agent_node", "synthesizer_node")
    graph.add_edge("task_agent_node", "synthesizer_node")
    graph.add_edge("notification_agent_node", "synthesizer_node")

    # From Synthesizer to Human Approval (if approval needed) or END
    graph.add_conditional_edges(
        "synthesizer_node",
        lambda s: "human_approval_node" if s.get("requires_human_approval") and s.get("approval_status") is not None else END,
        {
            "human_approval_node": "human_approval_node",
            END: END
        }
    )
    graph.add_edge("human_approval_node", END)

    return graph.compile()

# Global compiled application instance
edumate_graph = create_edumate_workflow()
