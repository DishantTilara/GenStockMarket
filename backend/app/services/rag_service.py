import math
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.rag import Document, DocumentChunk


class RAGService:
    @staticmethod
    def _simple_text_embedding(text: str) -> List[float]:
        """Deterministic pseudo-embedding representation for local/fallback semantic search."""
        words = text.lower().split()
        vector = [0.0] * 64
        for i, word in enumerate(words):
            h = hash(word) % 64
            vector[h] += 1.0 / (1.0 + math.log(i + 2))
        norm = math.sqrt(sum(x ** 2 for x in vector)) or 1.0
        return [round(x / norm, 4) for x in vector]

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a ** 2 for a, b in zip(v1, v2))) or 1.0
        norm2 = math.sqrt(sum(b ** 2 for a, b in zip(v1, v2))) or 1.0
        return dot / (norm1 * norm2)

    @classmethod
    async def index_document(cls, db: AsyncSession, title: str, doc_type: str, content: str, symbol: Optional[str] = None) -> Document:
        doc = Document(
            title=title,
            doc_type=doc_type,
            symbol=symbol.upper() if symbol else None
        )
        db.add(doc)
        await db.flush()

        # Chunk content into ~300 word chunks
        words = content.split()
        chunk_size = 250
        chunks = []
        for idx, start_idx in enumerate(range(0, len(words), chunk_size)):
            chunk_text = " ".join(words[start_idx:start_idx + chunk_size])
            embedding = cls._simple_text_embedding(chunk_text)
            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=idx,
                content=chunk_text,
                embedding=embedding
            )
            db.add(chunk)
            chunks.append(chunk)

        await db.commit()
        await db.refresh(doc)
        return doc

    @classmethod
    async def semantic_search(cls, db: AsyncSession, query: str, symbol: Optional[str] = None, top_k: int = 4) -> List[Dict[str, Any]]:
        query_vec = cls._simple_text_embedding(query)

        stmt = select(DocumentChunk).join(Document)
        if symbol:
            stmt = stmt.where(Document.symbol == symbol.upper())

        res = await db.execute(stmt.limit(100))
        chunks = res.scalars().all()

        scored = []
        for ch in chunks:
            sim = cls._cosine_similarity(query_vec, ch.embedding or [])
            scored.append({
                "chunk_id": str(ch.id),
                "document_id": str(ch.document_id),
                "content": ch.content,
                "similarity_score": round(sim, 4)
            })

        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:top_k]
