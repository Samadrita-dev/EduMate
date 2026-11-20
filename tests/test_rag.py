import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rag.document_loader import DocumentLoader
from rag.vector_store import EduMateVectorStore
from rag.retriever import DocumentRetriever

def test_rag_pipeline():
    # 1. Document loader
    loader = DocumentLoader()
    chunks = loader.process_all_chunks()
    assert len(chunks) > 0, "College documents should be loaded and chunked"
    assert any("attendance_policy" in c["document"] for c in chunks)

    # 2. Vector store indexing
    store = EduMateVectorStore()
    idx_res = store.build_or_refresh_index()
    assert idx_res["success"] is True

    # 3. Search and source attribution
    retriever = DocumentRetriever()
    search_res = retriever.search_documents("minimum attendance requirement", top_k=2)
    assert search_res["found"] is True
    assert len(search_res["sources"]) > 0
    top_doc = search_res["top_document"]
    assert "attendance_policy.txt" in top_doc, f"Expected attendance policy as top doc, got {top_doc}"

    print("✅ test_rag_pipeline passed!")

if __name__ == "__main__":
    test_rag_pipeline()
