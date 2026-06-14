from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            'data': None,
            'error': True,
            'message': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
        }
    return response
