# Owner: Person A
"""
ChromaDB Vector Search API endpoints.
Provides semantic retrieval for trains (e.g. "overnight sleeper to Chennai")
and policy rules/FAQs (e.g. "can I get a refund on Tatkal ticket?").
"""

import sys
from pathlib import Path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Ensure repo root is on sys.path for chroma_svc import
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from chroma_svc.search import search_trains, search_faq

class VectorTrainSearchView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        limit = int(request.query_params.get("limit", 5))

        if not query:
            return Response({
                "error": {
                    "code": "MISSING_QUERY",
                    "message": "Query parameter 'q' is required for semantic train search.",
                    "details": {}
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            results = search_trains(query_text=query, limit=limit)
            return Response({
                "query": query,
                "count": len(results),
                "results": results
            })
        except Exception as e:
            return Response({
                "error": {
                    "code": "VECTOR_SEARCH_ERROR",
                    "message": f"Semantic train search failed: {str(e)}",
                    "details": {}
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VectorFaqSearchView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        category = request.query_params.get("category", "").strip() or None
        limit = int(request.query_params.get("limit", 5))

        if not query:
            return Response({
                "error": {
                    "code": "MISSING_QUERY",
                    "message": "Query parameter 'q' is required for policy/FAQ search.",
                    "details": {}
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            results = search_faq(query_text=query, limit=limit, category=category)
            return Response({
                "query": query,
                "category": category,
                "count": len(results),
                "results": results
            })
        except Exception as e:
            return Response({
                "error": {
                    "code": "VECTOR_SEARCH_ERROR",
                    "message": f"Policy search failed: {str(e)}",
                    "details": {}
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
