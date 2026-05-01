"""RAG service — manages ChromaDB collection of past posts."""
import os
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from sqlalchemy.orm import Session
from app.config import settings
from app.services.embedding_service import EmbeddingService
from app.utils.logger import logger
COLLECTION_NAME = "linkedin_posts"
class RAGService:
    _client = None
    _collection = None
    def __init__(self, db: Session):
        self.db = db
        self.embedder = EmbeddingService(db=db)
        self._ensure_client()
    @classmethod
    def _ensure_client(cls):
        if cls._client is None:
            os.makedirs(settings.chroma_persist_dir, exist_ok=True)
            cls._client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            cls._collection = cls._client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"ChromaDB ready at {settings.chroma_persist_dir}")
    @property
    def collection(self):
        return self.__class__._collection
    def upsert_post(self, post_id, user_id, content, topic, style):
        if not content or not content.strip():
            logger.warning(f"Skipping upsert for post {post_id}: empty content")
            return
        embedding = self.embedder.embed_text(
            text=content, user_id=user_id, post_id=post_id, operation="rag_upsert"
        )
        self.collection.upsert(
            ids=[f"post_{post_id}"],
            embeddings=[embedding],
            documents=[content],
            metadatas=[{
                "post_id": post_id,
                "user_id": user_id,
                "topic": topic[:500],
                "style": style,
            }],
        )
        logger.info(f"Upserted post {post_id} to ChromaDB")
    def delete_post(self, post_id):
        try:
            self.collection.delete(ids=[f"post_{post_id}"])
            logger.info(f"Deleted post {post_id} from ChromaDB")
        except Exception as e:
            logger.warning(f"Failed to delete post {post_id} from Chroma: {e}")
    def retrieve_similar(self, query_text, user_id, top_k=3, style_filter=None):
        if self.collection.count() == 0:
            return []
        query_embedding = self.embedder.embed_text(
            text=query_text, user_id=user_id, operation="rag_retrieve"
        )
        where = {"user_id": user_id}
        if style_filter:
            where = {"$and": [{"user_id": user_id}, {"style": style_filter}]}
        results = self.collection.query(
            query_embeddings=[query_embedding], n_results=top_k, where=where
        )
        items = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                distance = results["distances"][0][i]
                similarity = max(0.0, 1.0 - distance)
                items.append({
                    "post_id": results["metadatas"][0][i]["post_id"],
                    "content": results["documents"][0][i],
                    "topic": results["metadatas"][0][i].get("topic", ""),
                    "style": results["metadatas"][0][i].get("style", ""),
                    "similarity": round(similarity, 4),
                })
        return items
    def check_repetition(self, new_content, user_id, threshold=0.85):
        similar = self.retrieve_similar(new_content, user_id, top_k=1)
        if not similar:
            return {"is_repetitive": False, "max_similarity": 0.0, "similar_post_id": None}
        top = similar[0]
        is_repetitive = top["similarity"] >= threshold
        if is_repetitive:
            logger.warning(
                f"Repetition detected! Similarity={top['similarity']:.2f} to post_id={top['post_id']}"
            )
        return {
            "is_repetitive": is_repetitive,
            "max_similarity": top["similarity"],
            "similar_post_id": top["post_id"],
        }
    def stats(self):
        return {
            "total_documents": self.collection.count(),
            "collection_name": COLLECTION_NAME,
            "persist_dir": settings.chroma_persist_dir,
        }