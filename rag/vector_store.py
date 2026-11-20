import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import CHROMA_PERSIST_DIR
from rag.document_loader import DocumentLoader
from rag.embeddings import EmbeddingService

class EduMateVectorStore:
    """Manages document vector indexing using ChromaDB with resilient fallback."""

    def __init__(self, persist_dir: Path = CHROMA_PERSIST_DIR):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = "edumate_docs"
        self.embedder = EmbeddingService()
        self.chroma_client = None
        self.chroma_collection = None
        self.fallback_chunks: List[Dict[str, Any]] = []
        self._init_store()

    def _init_store(self):
        """Attempts to initialize ChromaDB; falls back to structured JSON index if unavailable."""
        try:
            import chromadb
            self.chroma_client = chromadb.PersistentClient(path=str(self.persist_dir))
            self.chroma_collection = self.chroma_client.get_or_create_collection(name=self.collection_name)
        except Exception as e:
            self.chroma_client = None
            self.chroma_collection = None

    def build_or_refresh_index(self) -> Dict[str, Any]:
        """Loads all college documents from documents/ and indexes them."""
        loader = DocumentLoader()
        chunks = loader.process_all_chunks()
        if not chunks:
            return {"success": False, "indexed_count": 0, "message": "No documents found to index."}

        texts = [c["text"] for c in chunks]
        ids = [c["id"] for c in chunks]
        metadatas = [{"document": c["document"], "chunk_index": c["chunk_index"]} for c in chunks]

        # Use ChromaDB if active
        if self.chroma_collection is not None:
            try:
                embeddings = self.embedder.embed_texts(texts)
                self.chroma_collection.upsert(
                    ids=ids,
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
                return {
                    "success": True,
                    "engine": "ChromaDB",
                    "indexed_count": len(chunks),
                    "persist_dir": str(self.persist_dir)
                }
            except Exception as e:
                pass

        # Fallback in-memory / JSON persisted vector index
        embeddings = self.embedder.embed_texts(texts)
        self.fallback_chunks = []
        for i, c in enumerate(chunks):
            self.fallback_chunks.append({
                "id": ids[i],
                "document": metadatas[i]["document"],
                "text": texts[i],
                "embedding": embeddings[i] if i < len(embeddings) else []
            })

        fallback_cache = self.persist_dir / "fallback_index.json"
        try:
            with open(fallback_cache, "w", encoding="utf-8") as f:
                json.dump(self.fallback_chunks, f)
        except Exception:
            pass

        return {
            "success": True,
            "engine": "Semantic Fallback Index",
            "indexed_count": len(self.fallback_chunks)
        }

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Performs vector similarity search against indexed document chunks."""
        if not query or not query.strip():
            return []

        # If ChromaDB collection exists and has documents
        if self.chroma_collection is not None:
            try:
                count = self.chroma_collection.count()
                if count == 0:
                    self.build_or_refresh_index()

                query_embed = self.embedder.embed_query(query)
                results = self.chroma_collection.query(
                    query_embeddings=[query_embed],
                    n_results=min(top_k, max(1, self.chroma_collection.count())),
                    include=["documents", "metadatas", "distances"]
                )

                hits = []
                docs = results.get("documents", [[]])[0]
                metas = results.get("metadatas", [[]])[0]
                dists = results.get("distances", [[]])[0]

                for i in range(len(docs)):
                    d = float(dists[i]) if (dists and len(dists) > i) else 0.5
                    sim_score = round(1.0 / (1.0 + max(0.0, d)), 3)
                    hits.append({
                        "document": metas[i].get("document", "Document") if metas else "Document",
                        "text": docs[i],
                        "relevance_score": sim_score
                    })
                return hits
            except Exception:
                pass

        # Fallback Cosine Similarity Search
        if not self.fallback_chunks:
            fallback_cache = self.persist_dir / "fallback_index.json"
            if fallback_cache.exists():
                try:
                    with open(fallback_cache, "r", encoding="utf-8") as f:
                        self.fallback_chunks = json.load(f)
                except Exception:
                    pass

        if not self.fallback_chunks:
            self.build_or_refresh_index()

        query_embed = np.array(self.embedder.embed_query(query))
        q_norm = np.linalg.norm(query_embed)

        scored = []
        for ch in self.fallback_chunks:
            emb = np.array(ch.get("embedding", []))
            if len(emb) == len(query_embed) and q_norm > 0:
                e_norm = np.linalg.norm(emb)
                sim = np.dot(query_embed, emb) / (q_norm * e_norm) if e_norm > 0 else 0.0
            else:
                # Term overlap heuristic
                q_words = set(query.lower().split())
                c_words = set(ch["text"].lower().split())
                sim = len(q_words.intersection(c_words)) / max(1, len(q_words))

            scored.append({
                "document": ch["document"],
                "text": ch["text"],
                "relevance_score": round(float(sim), 3)
            })

        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored[:top_k]
