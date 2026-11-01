# Owner: Person A
"""
Tests for ChromaDB offline vector search API endpoints.
Verifies semantic retrieval of trains and policy FAQs using local sentence-transformers.
"""

import pytest
from rest_framework import status

@pytest.mark.django_db(databases=["default", "readonly"])
def test_vector_train_search_endpoint(api_client):
    resp = api_client.get("/api/search/trains/?q=fast+overnight+train+to+delhi")
    assert resp.status_code == status.HTTP_200_OK
    assert "results" in resp.data
    assert resp.data["count"] > 0
    top = resp.data["results"][0]
    assert "train_number" in top
    assert "similarity_score" in top
    assert top["similarity_score"] > 0.4


@pytest.mark.django_db(databases=["default", "readonly"])
def test_vector_faq_search_endpoint(api_client):
    resp = api_client.get("/api/search/faq/?q=can+I+get+refund+on+tatkal+ticket")
    assert resp.status_code == status.HTTP_200_OK
    assert "results" in resp.data
    assert resp.data["count"] > 0
    top = resp.data["results"][0]
    assert "title" in top
    assert "content" in top
    assert "similarity_score" in top
    assert top["similarity_score"] > 0.4
