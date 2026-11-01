# Owner: Person A
"""
ChromaDB vector query service for semantic train search and policy/FAQ retrieval.
"""

from .client import get_chroma_client, get_embedding_model
from .search import search_trains, search_faq

__all__ = ["get_chroma_client", "get_embedding_model", "search_trains", "search_faq"]
