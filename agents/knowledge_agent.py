from typing import Dict, Any, Optional
from rag.retriever import DocumentRetriever

class KnowledgeAgent:
    """Specialized agent responsible for retrieving grounded facts from college policy documents."""

    def __init__(self):
        self.agent_name = "KNOWLEDGE_AGENT"
        self.retriever = DocumentRetriever()

    def execute(self, action: str = "search", params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params or {}
        act = action.lower()

        if act in ["content", "read_doc"]:
            filename = params.get("filename", "")
            res = self.retriever.retrieve_document_content(filename)
            return {"agent": self.agent_name, "action": act, "result": res}

        else:
            query = params.get("query", "")
            top_k = params.get("top_k", 3)
            res = self.retriever.search_documents(query, top_k=top_k)
            return {"agent": self.agent_name, "action": "search_documents", "result": res}
