from .serializers import ErrorSerializer
from rest_framework.response import Response

def create_error_response(status_code, message, code=None, details=None):
    """
    Создает стандартизированный ответ об ошибке
    """
    error_data = {
        'status': 'error',
        'message': message
    }
    
    if code:
        error_data['code'] = code
    
    if details:
        error_data['details'] = details
    
    serializer = ErrorSerializer(error_data)
    return Response(serializer.data, status=status_code)