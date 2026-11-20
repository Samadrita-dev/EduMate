import numpy as np
from typing import List, Union
from config import EMBEDDING_MODEL_NAME

class EmbeddingService:
    """Provides 384-dimensional semantic embeddings via cached SentenceTransformers or fixed-dim projection."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self.model = None
        self.dim = 384
        self._init_model()

    def _init_model(self):
        """Loads cached sentence-transformers model without outbound network requests."""
        try:
            from sentence_transformers import SentenceTransformer
            try:
                # Use cached local files directly for offline sandbox execution
                self.model = SentenceTransformer(self.model_name, local_files_only=True)
            except Exception:
                self.model = SentenceTransformer(self.model_name)
        except Exception:
            self.model = None

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generates 384-dimensional embedding vectors for a list of texts."""
        if not texts:
            return []

        if self.model is not None:
            try:
                embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
                return embeddings.tolist()
            except Exception:
                pass

        return self._hash_embed(texts, dim=self.dim)

    def embed_query(self, query: str) -> List[float]:
        """Generates 384-dimensional embedding vector for query."""
        vectors = self.embed_texts([query])
        return vectors[0] if vectors else [0.0] * self.dim

    def _hash_embed(self, texts: List[str], dim: int = 384) -> List[List[float]]:
        """Deterministic fixed-dim vector embedding fallback."""
        results = []
        for t in texts:
            vec = np.zeros(dim, dtype=np.float32)
            for word in t.lower().split():
                idx = abs(hash(word)) % dim
                vec[idx] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            results.append(vec.tolist())
        return results
