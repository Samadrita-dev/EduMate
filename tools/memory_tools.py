import json
import datetime
from typing import Optional, List, Dict, Any
from database.db import get_db
from database.models import MemoryItem

SENSITIVE_KEYWORDS = ["password", "token", "secret", "credit_card", "cvv", "ssn", "pin"]

def save_memory(
    student_id: int,
    memory_type: str,
    key: str,
    value: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Saves a memory item for a student after privacy and security screening.
    memory_type: 'short_term', 'long_term', or 'episodic'
    """
    if memory_type not in ["short_term", "long_term", "episodic"]:
        return {"success": False, "error": "Invalid memory type. Use short_term, long_term, or episodic."}

    # Privacy filter: reject sensitive credentials
    combined_text = f"{key} {value}".lower()
    for kw in SENSITIVE_KEYWORDS:
        if kw in combined_text:
            return {"success": False, "error": f"Security restriction: Sensitive key/value '{kw}' cannot be stored in memory."}

    meta_str = json.dumps(metadata) if metadata else None

    with get_db() as db:
        # Check if key already exists for this student and type (update if exists)
        existing = db.query(MemoryItem).filter(
            MemoryItem.student_id == student_id,
            MemoryItem.memory_type == memory_type,
            MemoryItem.key == key.strip()
        ).first()

        if existing:
            existing.value = value.strip()
            existing.metadata_json = meta_str
            existing.updated_at = datetime.datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return {"success": True, "action": "updated", "memory": existing.to_dict()}
        else:
            item = MemoryItem(
                student_id=student_id,
                memory_type=memory_type,
                key=key.strip(),
                value=value.strip(),
                metadata_json=meta_str
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            return {"success": True, "action": "created", "memory": item.to_dict()}

def retrieve_memory(
    student_id: int,
    memory_type: Optional[str] = None,
    key: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieves memories strictly isolated to the specified student."""
    with get_db() as db:
        query = db.query(MemoryItem).filter(MemoryItem.student_id == student_id)
        if memory_type:
            query = query.filter(MemoryItem.memory_type == memory_type)
        if key:
            query = query.filter(MemoryItem.key.ilike(f"%{key.strip()}%"))

        items = query.order_by(MemoryItem.updated_at.desc()).all()
        return {
            "success": True,
            "count": len(items),
            "memories": [m.to_dict() for m in items]
        }

def delete_memory(memory_id: int, student_id: int) -> Dict[str, Any]:
    """Allows user to inspect and permanently remove specific memories."""
    with get_db() as db:
        item = db.query(MemoryItem).filter(
            MemoryItem.id == memory_id,
            MemoryItem.student_id == student_id
        ).first()

        if not item:
            return {"success": False, "error": f"Memory #{memory_id} not found."}

        db.delete(item)
        db.commit()
        return {"success": True, "message": f"Memory item #{memory_id} successfully deleted."}

def clear_student_memory(student_id: int, memory_type: Optional[str] = None) -> Dict[str, Any]:
    """Clears all or type-specific memories for a student upon consent."""
    with get_db() as db:
        query = db.query(MemoryItem).filter(MemoryItem.student_id == student_id)
        if memory_type:
            query = query.filter(MemoryItem.memory_type == memory_type)
        deleted_count = query.delete(synchronize_session=False)
        db.commit()
        return {"success": True, "deleted_count": deleted_count}
