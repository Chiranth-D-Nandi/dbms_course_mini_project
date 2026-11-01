# Owner: Person A
"""
Standardized error formatting and exception handlers for tatkal_core.
Ensures all errors return an envelope matching the OpenAPI specification:
{
    "error": {
        "code": "...",
        "message": "...",
        "details": {}
    }
}
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        customized_data = {
            "error": {
                "code": exc.__class__.__name__.upper(),
                "message": str(exc),
                "details": response.data,
            }
        }
        response.data = customized_data
        return response

    return Response(
        {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": str(exc),
                "details": {},
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
