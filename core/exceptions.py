from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            "error": True,
            "message": response.data.get('detail', str(exc)),
        }
        if isinstance(exc, ValidationError):
            response.data["field"] = list(exc.detail.keys())[0] if exc.detail else None
    return response