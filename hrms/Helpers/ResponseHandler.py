from rest_framework.response import Response

def custom_response(data=None, message="Success", status=200):
    """
    Standardized response structure.
    """
    return Response({
        "status_code": status,
        "message": message,
        "data": data
    }, status=status)