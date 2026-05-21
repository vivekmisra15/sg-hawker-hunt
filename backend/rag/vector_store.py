"""
ChromaDB vector store for the hawker knowledge base.

Embedding approach: chromadb.utils.embedding_functions.DefaultEmbeddingFunction
  — uses all-MiniLM-L6-v2 via ONNX runtime (bundled with chromadb).

Why not Anthropic via OpenAIEmbeddingFunction adapter:
  The OpenAIEmbeddingFunction sends requests to /v1/embeddings with an OpenAI
  request shape ({"input": [...], "model": "..."}). Anthropic's embedding
  endpoint uses a completely different shape and auth header format, so the
  adapter is incompatible. DefaultEmbeddingFunction produces quality 384-dim
  embeddings suitable for this use case without any external API call.
"""
import logging
import os
from typing import Optional

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

logger = logging.getLogger(__name__)

# Resolve path relative to this file so it works regardless of cwd
_CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
_COLLECTION_NAME = "hawker_knowledge"


class VectorStore:
    def __init__(self, path: str = _CHROMA_PATH):
        self._client = chromadb.PersistentClient(path=os.path.abspath(path))
        self._ef = DefaultEmbeddingFunction()
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, docs: list[dict]) -> None:
        """
        Add documents to the collection.
        Each doc: {id: str, text: str, metadata: dict}
        metadata keys: centre_name, stall_name, cuisine, region, tags (list[str]→joined str),
                       is_michelin (bool→str), is_halal (bool→str),
                       best_time, avoid_time, price_range
        ChromaDB metadata values must be str/int/float/bool — no nested dicts.
        """
        if not docs:
            return
        # ChromaDB requires metadata values to be primitive types
        sanitised_meta = []
        for d in docs:
            m = {k: (", ".join(v) if isinstance(v, list) else str(v) if isinstance(v, bool) else v)
                 for k, v in d.get("metadata", {}).items()}
            sanitised_meta.append(m)

        self._collection.upsert(
            ids=[d["id"] for d in docs],
            documents=[d["text"] for d in docs],
            metadatas=sanitised_meta,
        )

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        cuisine_filter: Optional[str] = None,
        region_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        Semantic search over the knowledge base.
        Returns list of {text, metadata, distance}.

        When cuisine_filter or region_filter is provided, a ChromaDB where-clause
        restricts results to matching documents.  Falls back to unfiltered query
        if the filtered query returns 0 results.
        """
        count = self.collection_size()
        if count == 0:
            return []
        actual_n = min(n_results, count)

        where = self._build_where(cuisine_filter, region_filter)

        if where:
            results = self._collection.query(
                query_texts=[query_text],
                n_results=actual_n,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
            docs = results["documents"][0]
            if not docs:
                logger.debug(
                    "Filtered query returned 0 results (cuisine=%s, region=%s) — falling back to unfiltered",
                    cuisine_filter, region_filter,
                )
                where = None  # fall through to unfiltered

        if not where:
            results = self._collection.query(
                query_texts=[query_text],
                n_results=actual_n,
                include=["documents", "metadatas", "distances"],
            )

        output = []
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]
        for text, meta, dist in zip(docs, metas, dists):
            output.append({"text": text, "metadata": meta, "distance": dist})
        return output

    @staticmethod
    def _build_where(
        cuisine_filter: Optional[str], region_filter: Optional[str]
    ) -> Optional[dict]:
        """Build a ChromaDB where-clause from optional filters."""
        conditions = []
        if cuisine_filter:
            conditions.append({"cuisine": {"$eq": cuisine_filter}})
        if region_filter:
            conditions.append({"region": {"$eq": region_filter}})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def collection_size(self) -> int:
        return self._collection.count()

    def warmup(self) -> None:
        """Pre-warm the embedding function to cache the ONNX model.
        Call this at startup (e.g., in FastAPI lifespan) to avoid timeout on first query.
        """
        self._ef(["warmup"])
