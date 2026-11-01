# Owner: Person A
"""
ChromaDB Persistent Client and Local Embedding Model Loader.
Configured for offline execution using sentence-transformers all-MiniLM-L6-v2
cached locally in `./models/all-MiniLM-L6-v2`.
"""

import os
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

REPO_ROOT = Path(__file__).resolve().parent.parent
CHROMA_DATA_DIR = REPO_ROOT / "chroma_data"
MODEL_DIR = REPO_ROOT / "models" / "all-MiniLM-L6-v2"

_client = None
_model = None

def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is not None:
        return _model

    if MODEL_DIR.exists() and any(MODEL_DIR.iterdir()):
        # Load cached offline model
        _model = SentenceTransformer(str(MODEL_DIR))
    else:
        # Download and cache into ./models/all-MiniLM-L6-v2
        MODEL_DIR.parent.mkdir(parents=True, exist_ok=True)
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        _model.save(str(MODEL_DIR))

    return _model

def get_chroma_client() -> chromadb.PersistentClient:
    global _client
    if _client is not None:
        return _client

    CHROMA_DATA_DIR.mkdir(parents=True, exist_ok=True)
    _client = chromadb.PersistentClient(
        path=str(CHROMA_DATA_DIR),
        settings=Settings(anonymized_telemetry=False, allow_reset=True)
    )
    return _client
