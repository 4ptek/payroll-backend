from rest_framework.response import Response

def custom_response(data, message, status, pagination=None):
    response_data = {
        "status": "success",
        "message": message,
        "data": data,
    }
    
    # Agar pagination data aya hai to usay response mein add karein
    if pagination:
        response_data["pagination"] = pagination

    return Response(response_data, status=status)