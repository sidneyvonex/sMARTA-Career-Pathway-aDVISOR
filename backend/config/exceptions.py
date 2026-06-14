from django_ratelimit.exceptions import Ratelimited
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    if isinstance(exc, Ratelimited):
        return Response(
            {'data': None, 'error': True, 'message': 'Rate limit exceeded. Please try again later.'},
            status=429,
        )
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            'data': None,
            'error': True,
            'message': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
        }
    return response
