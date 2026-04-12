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
import os
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

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
        metadata keys: centre_name, stall_name, cuisine, tags (str),
                       is_michelin (bool→str), is_halal (bool→str),
                       best_time, avoid_time, price_range
        ChromaDB metadata values must be str/int/float/bool — no nested dicts.
        """
        if not docs:
            return
        # ChromaDB requires metadata values to be primitive types
        sanitised_meta = []
        for d in docs:
            m = {k: (str(v) if isinstance(v, bool) else v)
                 for k, v in d.get("metadata", {}).items()}
            sanitised_meta.append(m)

        self._collection.upsert(
            ids=[d["id"] for d in docs],
            documents=[d["text"] for d in docs],
            metadatas=sanitised_meta,
        )

    def query(self, query_text: str, n_results: int = 5) -> list[dict]:
        """
        Semantic search over the knowledge base.
        Returns list of {text, metadata, distance}.
        """
        count = self.collection_size()
        if count == 0:
            return []
        actual_n = min(n_results, count)
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

    def collection_size(self) -> int:
        return self._collection.count()
