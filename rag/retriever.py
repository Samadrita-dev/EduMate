from typing import List, Dict, Any, Optional
from rag.vector_store import EduMateVectorStore
from config import DOCUMENTS_DIR

class DocumentRetriever:
    """High-level document retriever for Knowledge Agent."""

    def __init__(self):
        self.vector_store = EduMateVectorStore()

    def search_documents(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Retrieves top relevant passages from college policies and documents.
        Returns document citations and relevance confidence.
        """
        results = self.vector_store.search(query=query, top_k=top_k)
        if not results or results[0]["relevance_score"] < 0.15:
            return {
                "found": False,
                "query": query,
                "message": "No verified college document matches found with sufficient confidence.",
                "sources": []
            }

        sources = []
        formatted_evidence = []
        for r in results:
            sources.append({
                "document": r["document"],
                "relevance_score": r["relevance_score"],
                "snippet": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"]
            })
            formatted_evidence.append(f"--- Document: {r['document']} (Confidence: {r['relevance_score']}) ---\n{r['text']}")

        return {
            "found": True,
            "query": query,
            "top_document": results[0]["document"],
            "evidence_context": "\n\n".join(formatted_evidence),
            "sources": sources
        }

    def retrieve_document_content(self, filename: str) -> Dict[str, Any]:
        """Fetches full text content of a named document."""
        target_path = DOCUMENTS_DIR / filename
        if not target_path.exists():
            return {"success": False, "error": f"Document '{filename}' does not exist."}

        try:
            with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return {"success": True, "filename": filename, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_indexed_documents(self) -> List[str]:
        """Lists all document names present in documents directory."""
        if not DOCUMENTS_DIR.exists():
            return []
        return [f.name for f in DOCUMENTS_DIR.glob("*.*") if f.suffix in [".txt", ".md", ".json"]]
