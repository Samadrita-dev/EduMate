# 🎓 EduMate: Agentic AI-Based Intelligent Student Management System

> **Tagline:** *Your Intelligent Academic Companion*  
> **Status:** Fully Functional & Tested • Suitable for College-Level Agentic AI Demonstration

EduMate is a comprehensive, production-grade **Agentic AI academic management ecosystem** engineered for college students. Moving far beyond static dashboards and basic conversational chatbots, EduMate integrates **LangGraph multi-agent coordination**, **ChromaDB-backed Retrieval-Augmented Generation (RAG)**, **persistent three-tier memory**, **human-in-the-loop approval gates**, and **Hugging Face educational analytics** into an intuitive Streamlit interface.

---

## 🌟 Key Capabilities & Architectural Highlights

1. **Genuine Multi-Agent Architecture (LangGraph)**
   - **Central Coordinator Agent:** Orchestrates goal planning, intent extraction, agent routing, state synthesis, and failure recovery.
   - **Task Management Agent:** Full lifecycle management of to-dos, priorities, deadlines, and overdue audits.
   - **Attendance Agent:** Audits official attendance, enforces the 75% Senate threshold, detects debarment risks (<65%), and computes mathematically required future sessions.
   - **Timetable Agent:** Manages daily/weekly lecture schedules, highlights conflicts, and discovers unoccupied study windows.
   - **Exam Agent:** Tracks midterms and finals countdowns, syllabus scope, and student revision readiness.
   - **Meeting Agent:** Searches faculty directory and schedules consultations with timetable conflict validation.
   - **Knowledge / RAG Agent:** Semantic search over verified college regulations, examination rules, and syllabus documents.
   - **Notification Agent:** Surfaces proactive alerts for approaching deadlines, exam notices, and attendance warnings.

2. **Retrieval-Augmented Generation (RAG) with ChromaDB**
   - Indexes official college documents (`attendance_policy.txt`, `examination_rules.txt`, `academic_calendar.txt`, `syllabus_cs.txt`, `assignment_guidelines.txt`).
   - Sentence-Transformers embedding pipeline with strict source citation to prevent rule hallucination.

3. **Three-Tier Persistent Memory System**
   - **Short-Term Memory:** In-session conversation turns, intermediate tool calls, and LangGraph execution traces.
   - **Long-Term Memory:** Consensual student preferences (preferred study hours, focus areas, break intervals) stored per student.
   - **Episodic Memory:** Historical records of approved revision plans and past milestone decisions.
   - **Privacy Filtering:** Automatic rejection of sensitive tokens (passwords, secrets) and user deletion controls.

4. **Human-In-The-Loop Approval Workflow**
   - Consequential actions (such as faculty meeting bookings, study plan commits, and bulk deletions) stage a formal proposal.
   - Students review, approve, or reject proposals before any state changes are committed to the database.

5. **Local LLM Integration (Ollama) with Resilient Fallback**
   - Configurable for local models such as `llama3.2`, `mistral`, or `qwen2.5:3b`.
   - **Zero-Cost Operation:** No paid OpenAI or proprietary API keys required.
   - **Smart Fallback Engine:** If Ollama is offline or uninstalled, EduMate seamlessly transitions to its built-in rule-based agent mode, executing the exact same LangGraph workflows, tools, and RAG pipelines without interruption.

6. **Educational Analytics (Hugging Face Datasets)**
   - Integrates empirical educational research data (`imodels/student-performance`).
   - Analyzes study hours vs. exam performance and provides a Scikit-Learn predictive grade forecaster.
   - Clear architectural boundary: Public research data is strictly used for benchmarking, while logged-in student records remain private.

---

## 🏗️ Architecture Overview

```
                                  +---------------------------+
                                  |   Streamlit UI Dashboard  |
                                  |  (14 Interactive Modules) |
                                  +-------------+-------------+
                                                |
                                                v
                                  +---------------------------+
                                  |     Coordinator Agent     |
                                  |    (LangGraph Workflow)   |
                                  +-------------+-------------+
                                                |
         +--------------------------------------+--------------------------------------+
         |                   |                  |                   |                  |
         v                   v                  v                   v                  v
+-----------------+ +-----------------+ +-----------------+ +-----------------+ +-----------------+
|   Task Agent    | |Attendance Agent | | Timetable Agent | |   Exam Agent    | |  Meeting Agent  |
| (CRUD & Due)    | | (75% Math Calc) | |(Conflict & Gaps)| | (Countdown/Prep)| |(Faculty Booking)|
+--------+--------+ +--------+--------+ +--------+--------+ +--------+--------+ +--------+--------+
         |                   |                  |                   |                  |
         +--------------------------------------+--------------------------------------+
                                                |
                                                v
                                  +---------------------------+
                                  |  Human-In-The-Loop Gate   | <--- Student Approves / Rejects
                                  +-------------+-------------+
                                                |
                         +----------------------+----------------------+
                         |                                             |
                         v                                             v
              +---------------------+                       +---------------------+
              |    Knowledge Agent  |                       |  Three-Tier Memory  |
              |   (RAG + ChromaDB)  |                       | (Short/Long/Episode)|
              +----------+----------+                       +----------+----------+
                         |                                             |
                         +----------------------+----------------------+
                                                |
                                                v
                                  +---------------------------+
                                  |     SQLite / SQLAlchemy   |
                                  | (12 Relational DB Tables) |
                                  +---------------------------+
```

---

## 📁 Project Directory Structure

```
EduMate/
│
├── app.py                         # Master Streamlit Application & Routing
├── config.py                      # System Configuration & Path Defaults
├── requirements.txt               # Complete Python Dependencies
├── .env.example                   # Environment Variables Template
├── README.md                      # Comprehensive Project Documentation
├── edumate.db                     # SQLite Database (Auto-created & Seeded)
│
├── pages/                         # 14 Modular UI Pages
│   ├── dashboard.py               # Comprehensive Academic KPI Dashboard
│   ├── ai_assistant.py            # Chat Assistant & Human-In-The-Loop Approval
│   ├── tasks.py                   # To-Do List & Assignment Priority Manager
│   ├── attendance.py              # Official Attendance Tracker & Math Calculator
│   ├── timetable.py               # Daily/Weekly Schedule & Free Slot Finder
│   ├── assignments.py             # Coursework Submissions & Deadlines
│   ├── exams.py                   # Exam Countdowns & Syllabus Coverage
│   ├── teachers.py                # Faculty Directory & Cabin Locations
│   ├── meetings.py                # Meeting Requests & Timetable Conflict Check
│   ├── study_planner.py           # Autonomous Conflict-Free Study Planner
│   ├── notifications.py           # In-App Alerts & Proactive Reminder Auditor
│   ├── documents_rag.py           # Institutional Policy Explorer (ChromaDB)
│   ├── analytics_hf.py            # Hugging Face Benchmarks & Grade Predictor
│   └── profile_settings.py        # Multi-Student Switcher & Privacy Settings
│
├── agents/                        # Specialized LangGraph Agents
│   ├── coordinator.py             # Master Coordinator Agent
│   ├── task_agent.py              # Task Management Agent
│   ├── attendance_agent.py        # Attendance Calculation Agent
│   ├── timetable_agent.py         # Timetable & Free Slot Agent
│   ├── exam_agent.py              # Examination Agent
│   ├── meeting_agent.py           # Meeting Scheduler Agent
│   ├── knowledge_agent.py         # Knowledge / RAG Agent
│   └── notification_agent.py      # Notification & Proactive Alert Agent
│
├── graph/                         # LangGraph Orchestration Subsystem
│   ├── state.py                   # Central TypedDict Shared State
│   └── workflow.py                # StateGraph Compilation, Nodes & Conditional Edges
│
├── llm/                           # Local LLM Layer
│   ├── client.py                  # Ollama API Client with Smart Rule Fallback
│   └── prompts.py                 # Structured Agent Prompts
│
├── rag/                           # ChromaDB Retrieval-Augmented Generation
│   ├── document_loader.py         # Document Chunking & Metadata Extraction
│   ├── embeddings.py              # Sentence-Transformers (all-MiniLM-L6-v2)
│   ├── vector_store.py            # ChromaDB Persistent Vector Storage
│   └── retriever.py               # Evidence Retrieval & Source Attribution
│
├── memory/                        # Three-Tier Memory Architecture
│   ├── short_term.py              # Conversation Turns & Agent Traces
│   ├── long_term.py               # Persistent Consensual Preferences
│   └── episodic.py                # Historical Plans & Interaction Memory
│
├── tools/                         # Functional Python Tool Library
│   ├── task_tools.py              # Task CRUD Tools
│   ├── attendance_tools.py        # 75% Formula & Consecutive Class Calculators
│   ├── timetable_tools.py         # Schedule Conflict & Open Slot Tools
│   ├── exam_tools.py              # Exam Queries & Readiness Trackers
│   ├── meeting_tools.py           # Conflict-Validated Meeting Booking Tools
│   ├── notification_tools.py      # Proactive Background Auditors
│   └── memory_tools.py            # Privacy-Screened Memory Management Tools
│
├── database/                      # Relational Storage Layer
│   ├── db.py                      # SQLAlchemy Engine & Scoped Sessions
│   ├── models.py                  # 12 Normalized Relational Schema Models
│   └── seed.py                    # Sample Student, Faculty & Academic Data
│
├── datasets/                      # Hugging Face Dataset Integration
│   └── hf_loader.py               # Dataset Fetcher, Correlation & Scikit-Learn Model
│
├── documents/                     # Sample College Institutional Policies
│   ├── academic_calendar.txt      # Semester Milestone Dates
│   ├── attendance_policy.txt      # 75% Rule, 65% Floor & Condonation
│   ├── examination_rules.txt      # Pass Marks (40%), CIA (50%) & Grading
│   ├── syllabus_cs.txt            # 5th Sem Computer Science Syllabus
│   └── assignment_guidelines.txt  # Late Penalties & Plagiarism Policy
│
├── tests/                         # Comprehensive Unit & Integration Test Suite
│   ├── test_db.py                 # Schema, Seeding & Isolation Tests
│   ├── test_tools.py              # Tool CRUD & Math Formula Tests
│   ├── test_agents.py             # Agent Execution & Coordination Tests
│   ├── test_memory.py             # Memory Tier & Privacy Security Tests
│   ├── test_rag.py                # ChromaDB Indexing & Attribution Tests
│   └── test_failure_modes.py      # Ollama Offline, Bad IDs & Conflict Tests
│
└── utils/
    └── ui_components.py           # High-End Academic CSS & UI Components
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python:** 3.10, 3.11, or 3.12 installed.
- **Git** (optional).
- *(Optional for Local LLM)* **Ollama:** Downloaded from [ollama.com](https://ollama.com).

### 2. Installation
Navigate to the project root directory:
```bash
cd EduMate
```

Install all required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed Database
The application automatically creates and seeds the SQLite database (`edumate.db`) on startup. To manually re-seed or test:
```bash
python database/seed.py
```

### 4. (Optional) Run Local LLM with Ollama
If you wish to use a local LLM, start Ollama in a separate terminal:
```bash
ollama run llama3.2
```
*Note: If Ollama is not running, EduMate automatically switches to its Smart Agent Fallback mode, so the full multi-agent application remains 100% functional.*

### 5. Launch the Application
Run the Streamlit application:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Running the Automated Test Suite

EduMate includes automated unit and integration tests verifying all features and failure modes:

```bash
# Test Database Models & Student Isolation
python tests/test_db.py

# Test Mathematical Formulas & Tools
python tests/test_tools.py

# Test Multi-Agent Coordination & Human-In-The-Loop
python tests/test_agents.py

# Test Three-Tier Memory & Privacy Filtering
python tests/test_memory.py

# Test RAG Vector Search & Attribution
python tests/test_rag.py

# Test Failure Modes & Edge Conditions
python tests/test_failure_modes.py
```

Or run all suites in sequence:
```bash
python -m unittest discover tests/
```

---

## 🔒 Security, Privacy & Data Isolation

- **Student Isolation:** Every database query filters by `student_id`. A student cannot access or mutate another student's tasks, meetings, or preferences.
- **Official Records Protection:** Normal students cannot edit official faculty attendance logs or examination schedules.
- **Memory Security:** Memory items are screened; attempts to store passwords, API secrets, or credit card numbers are rejected.
- **Human-In-The-Loop:** Consequential actions stage a proposal and require explicit confirmation (`Approve` / `Reject`) before database writes occur.
