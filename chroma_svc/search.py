# Owner: Person A
"""
ChromaDB Vector Similarity Search Functions.
Performs semantic retrieval against `train_info` and `policy_faq` collections.
"""

from typing import List, Dict, Any, Optional
from .client import get_chroma_client, get_embedding_model

def search_trains(query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
    client = get_chroma_client()
    try:
        collection = client.get_collection(name="train_info")
    except Exception:
        # Collection not yet ingested
        return []

    model = get_embedding_model()
    query_vector = model.encode([query_text]).tolist()

    results = collection.query(
        query_embeddings=query_vector,
        n_results=limit,
        include=["metadatas", "documents", "distances"]
    )

    formatted = []
    if results and results["ids"] and len(results["ids"][0]) > 0:
        ids = results["ids"][0]
        metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)
        documents = results["documents"][0] if results.get("documents") else [""] * len(ids)
        distances = results["distances"][0] if results.get("distances") else [1.0] * len(ids)

        for i in range(len(ids)):
            # Cosine distance in Chroma: score = 1 - distance (or 1 / (1 + dist))
            dist = distances[i] if i < len(distances) else 1.0
            similarity = round(max(0.0, 1.0 - dist), 4)

            meta = metadatas[i] if i < len(metadatas) else {}
            formatted.append({
                "train_number": meta.get("train_number", ids[i]),
                "train_name": meta.get("train_name", ""),
                "train_type": meta.get("train_type", ""),
                "source": meta.get("source", ""),
                "destination": meta.get("destination", ""),
                "description": documents[i],
                "similarity_score": similarity,
                "metadata": meta
            })

    return formatted


def search_faq(query_text: str, limit: int = 5, category: Optional[str] = None) -> List[Dict[str, Any]]:
    client = get_chroma_client()
    try:
        collection = client.get_collection(name="policy_faq")
    except Exception:
        # Collection not yet ingested
        return []

    model = get_embedding_model()
    query_vector = model.encode([query_text]).tolist()

    where_filter = {"category": category} if category else None

    results = collection.query(
        query_embeddings=query_vector,
        n_results=limit,
        where=where_filter,
        include=["metadatas", "documents", "distances"]
    )

    formatted = []
    if results and results["ids"] and len(results["ids"][0]) > 0:
        ids = results["ids"][0]
        metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)
        documents = results["documents"][0] if results.get("documents") else [""] * len(ids)
        distances = results["distances"][0] if results.get("distances") else [1.0] * len(ids)

        for i in range(len(ids)):
            dist = distances[i] if i < len(distances) else 1.0
            similarity = round(max(0.0, 1.0 - dist), 4)
            meta = metadatas[i] if i < len(metadatas) else {}

            formatted.append({
                "chunk_id": ids[i],
                "title": meta.get("title", ""),
                "category": meta.get("category", "General"),
                "content": documents[i],
                "similarity_score": similarity
            })

    return formatted
