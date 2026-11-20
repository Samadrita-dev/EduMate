import os
from pathlib import Path
from typing import List, Dict, Any
from config import DOCUMENTS_DIR

class DocumentLoader:
    """Loads and splits academic college policy documents."""
    
    def __init__(self, doc_dir: Path = DOCUMENTS_DIR):
        self.doc_dir = Path(doc_dir)

    def load_documents(self) -> List[Dict[str, Any]]:
        """Reads all text documents from documents directory."""
        if not self.doc_dir.exists():
            return []

        documents = []
        for file_path in self.doc_dir.glob("*.*"):
            if file_path.suffix.lower() in [".txt", ".md", ".json"]:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                    documents.append({
                        "filename": file_path.name,
                        "path": str(file_path),
                        "content": text
                    })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
        return documents

    def split_text(self, text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> List[str]:
        """Splits long text into overlapping chunks respecting paragraph and line breaks."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += ("\n\n" + para if current_chunk else para)
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                # If paragraph itself is longer than chunk_size, split by sentences or chunks
                if len(para) > chunk_size:
                    for i in range(0, len(para), chunk_size - chunk_overlap):
                        sub_chunk = para[i:i + chunk_size]
                        if sub_chunk:
                            chunks.append(sub_chunk)
                    current_chunk = ""
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def process_all_chunks(self, chunk_size: int = 500, chunk_overlap: int = 100) -> List[Dict[str, Any]]:
        """Loads all documents and returns structured chunks with source metadata."""
        docs = self.load_documents()
        all_chunks = []
        for doc in docs:
            chunks = self.split_text(doc["content"], chunk_size, chunk_overlap)
            for idx, ch in enumerate(chunks):
                all_chunks.append({
                    "id": f"{doc['filename']}_{idx}",
                    "document": doc["filename"],
                    "chunk_index": idx,
                    "text": ch
                })
        return all_chunks
