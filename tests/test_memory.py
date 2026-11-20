import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from memory.episodic import EpisodicMemory

def test_memory_layers_and_privacy():
    student_id = 1

    # 1. Short-Term Memory
    stm = ShortTermMemory(max_history=5)
    stm.add_message("user", "Hello")
    stm.add_message("assistant", "Hi Aarav")
    assert len(stm.get_context_history()) == 2
    stm.log_agent_action("TASK_AGENT", "add", {"id": 10})
    assert len(stm.get_latest_trace()) == 1

    # 2. Long-Term Memory
    ltm = LongTermMemory(student_id)
    save_res = ltm.set_preference("test_study_hour", "Prefers 8 PM")
    assert save_res["success"] is True
    mem_id = save_res["memory"]["id"]

    val = ltm.get_preference_by_key("test_study_hour")
    assert val == "Prefers 8 PM"

    # Privacy Protection Test: Rejection of sensitive tokens
    sec_res = ltm.set_preference("user_password", "MySecret123!")
    assert sec_res["success"] is False, "Sensitive password must be rejected by memory filter"

    # Cleanup test memory
    del_res = ltm.delete_preference(mem_id)
    assert del_res["success"] is True

    # 3. Episodic Memory
    epm = EpisodicMemory(student_id)
    ep_res = epm.record_episode("unit_test_episode", "Passed automated unit testing")
    assert ep_res["success"] is True
    episodes = epm.get_episodes()
    assert any(e["key"] == "unit_test_episode" for e in episodes)

    print("✅ test_memory_layers_and_privacy passed!")

if __name__ == "__main__":
    test_memory_layers_and_privacy()
