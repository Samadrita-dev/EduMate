import json
import re
import requests
from typing import Dict, Any, Optional, List
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
from llm.prompts import INTENT_EXTRACTION_PROMPT, SYSTEM_COORDINATOR_PROMPT

class OllamaClient:
    """
    Manages local LLM inference via Ollama with robust status detection,
    error handling, and intelligent rule-based fallback when Ollama is offline.
    """
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = OLLAMA_TIMEOUT

    def check_connection(self) -> Dict[str, Any]:
        """
        Tests if Ollama daemon is actively running and lists available models.
        """
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2.0)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                model_installed = any(self.model in m for m in models)
                return {
                    "available": True,
                    "connected_url": self.base_url,
                    "configured_model": self.model,
                    "model_installed": model_installed,
                    "available_models": models,
                    "message": f"Connected to Ollama. Model: {self.model}"
                }
            else:
                return {
                    "available": False,
                    "error": f"Ollama HTTP {resp.status_code}",
                    "message": "Ollama service responded with an error."
                }
        except requests.exceptions.RequestException as e:
            return {
                "available": False,
                "error": str(e),
                "message": (
                    f"Local LLM (Ollama) is not running at {self.base_url}. "
                    "EduMate is operating in Smart Fallback Agent mode. "
                    "To enable local LLM: Install Ollama (https://ollama.com) and run `ollama run llama3.2`."
                )
            }

    def generate(self, prompt: str, system: Optional[str] = SYSTEM_COORDINATOR_PROMPT) -> Dict[str, Any]:
        """Sends prompt to local Ollama instance."""
        conn = self.check_connection()
        if not conn["available"]:
            return {
                "success": False,
                "error": conn["message"],
                "fallback_needed": True
            }

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system or "",
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }

        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "text": data.get("response", "").strip(),
                    "model": self.model
                }
            else:
                return {
                    "success": False,
                    "error": f"Ollama generation failed: HTTP {resp.status_code}",
                    "fallback_needed": True
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Ollama request error: {str(e)}",
                "fallback_needed": True
            }

    def parse_intent(self, user_query: str) -> Dict[str, Any]:
        """
        Extracts user intent, target agents, and entities.
        If Ollama is available, uses the local LLM.
        If Ollama is offline, utilizes deterministic semantic classification.
        """
        conn = self.check_connection()
        if conn["available"]:
            prompt = INTENT_EXTRACTION_PROMPT.format(user_query=user_query)
            gen_res = self.generate(prompt)
            if gen_res.get("success"):
                try:
                    # Extract JSON substring
                    raw_text = gen_res["text"]
                    json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                    if json_match:
                        parsed = json.loads(json_match.group(0))
                        parsed["source"] = "ollama"
                        return parsed
                except Exception:
                    pass

        # Fallback Deterministic NLP Parser
        return self._fallback_rule_intent_parser(user_query)

    def _fallback_rule_intent_parser(self, query: str) -> Dict[str, Any]:
        """
        Deterministic intent and entity extractor ensuring complete,
        uninterrupted multi-agent operation when local LLM is offline.
        """
        q = query.lower()
        entities: Dict[str, Any] = {}

        # Extract potential subject code
        subj_match = re.search(r"\b(cs50[1-5]|os|dbms|networks|ai|software engineering)\b", q)
        if subj_match:
            entities["subject"] = subj_match.group(1).upper()

        # Extract dates or days
        day_match = re.search(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|today|tomorrow)\b", q)
        if day_match:
            entities["day"] = day_match.group(1).capitalize()

        # Extract teacher name
        teacher_match = re.search(r"(dr\.\s+\w+|prof\.\s+\w+|rajesh|ananya|vikram|sneha|miller)", q)
        if teacher_match:
            entities["teacher"] = teacher_match.group(0).title()

        # Classify intent & target agents
        if any(w in q for w in ["study plan", "revision plan", "schedule my week", "plan my week", "prepare schedule", "study schedule", "plan my study", "plan my", "prepare a study plan", "manage everything"]):
            return {
                "intent": "study_plan",
                "target_agents": ["TIMETABLE_AGENT", "EXAM_AGENT", "TASK_AGENT", "COORDINATOR"],
                "requires_approval": True,
                "entities": entities,
                "summary_goal": "Generate coordinated study and revision plan.",
                "source": "smart_rule_engine"
            }
        elif any(w in q for w in ["policy", "rule", "condonation", "detention", "regulation", "guideline", "calendar", "grading scale"]):
            return {
                "intent": "knowledge",
                "target_agents": ["KNOWLEDGE_AGENT"],
                "requires_approval": False,
                "entities": entities,
                "summary_goal": "Retrieve verified academic guidelines from documents.",
                "source": "smart_rule_engine"
            }
        elif any(w in q for w in ["attendance", "present", "absent", "missed class", "bunk", "shortage"]):
            return {
                "intent": "attendance",
                "target_agents": ["ATTENDANCE_AGENT"],
                "requires_approval": False,
                "entities": entities,
                "summary_goal": "Check attendance and calculate required classes.",
                "source": "smart_rule_engine"
            }
        elif any(w in q for w in ["timetable", "schedule", "routine", "what class", "free slot", "next class"]):
            return {
                "intent": "timetable",
                "target_agents": ["TIMETABLE_AGENT"],
                "requires_approval": False,
                "entities": entities,
                "summary_goal": "Retrieve timetable and free time slots.",
                "source": "smart_rule_engine"
            }
        elif any(w in q for w in ["exam", "examination", "midterm", "final", "test", "syllabus"]):
            if any(w in q for w in ["rule", "policy", "pass mark", "grading", "malpractice"]):
                return {
                    "intent": "knowledge",
                    "target_agents": ["KNOWLEDGE_AGENT"],
                    "requires_approval": False,
                    "entities": entities,
                    "summary_goal": "Query examination policy and rules from documents.",
                    "source": "smart_rule_engine"
                }
            return {
                "intent": "exam",
                "target_agents": ["EXAM_AGENT"],
                "requires_approval": False,
                "entities": entities,
                "summary_goal": "Retrieve upcoming examinations and countdown.",
                "source": "smart_rule_engine"
            }
        elif any(w in q for w in ["meet", "meeting", "appointment", "office hour", "teacher", "faculty", "professor"]):
            requires_app = any(w in q for w in ["book", "request", "schedule", "fix"])
            return {
                "intent": "meeting",
                "target_agents": ["MEETING_AGENT", "TIMETABLE_AGENT"],
                "requires_approval": requires_app,
                "entities": entities,
                "summary_goal": "Faculty consultation or meeting request.",
                "source": "smart_rule_engine"
            }
        elif any(w in q for w in ["task", "to-do", "todo", "assignment", "homework", "pending work", "due"]):
            requires_app = any(w in q for w in ["delete", "remove"])
            return {
                "intent": "task",
                "target_agents": ["TASK_AGENT"],
                "requires_approval": requires_app,
                "entities": entities,
                "summary_goal": "Manage academic tasks and assignments.",
                "source": "smart_rule_engine"
            }
        elif any(w in q for w in ["rule", "policy", "calendar", "document", "regulation", "handbook", "library"]):
            return {
                "intent": "knowledge",
                "target_agents": ["KNOWLEDGE_AGENT"],
                "requires_approval": False,
                "entities": entities,
                "summary_goal": "Retrieve verified academic guidelines from documents.",
                "source": "smart_rule_engine"
            }
        elif any(w in q for w in ["notification", "alert", "reminder"]):
            return {
                "intent": "notification",
                "target_agents": ["NOTIFICATION_AGENT"],
                "requires_approval": False,
                "entities": entities,
                "summary_goal": "Review academic reminders and notifications.",
                "source": "smart_rule_engine"
            }
        else:
            return {
                "intent": "general",
                "target_agents": ["COORDINATOR"],
                "requires_approval": False,
                "entities": entities,
                "summary_goal": "General academic query.",
                "source": "smart_rule_engine"
            }
