from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

class CodeGenerationError(Exception):
    """Custom exception for code generation errors"""
    pass

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, CodeGenerationError):
        return Response(
            {'error': str(exc)},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    return response