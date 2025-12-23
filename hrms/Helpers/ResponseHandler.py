from rest_framework.response import Response

# Argument ka naam 'http_status' se change karke 'status' kar diya
def custom_response(data = None, message=None, status=None, pagination=None, status_str=None): 
    """
    Standardized response wrapper.
    """
    
    # 1. status check (variable name update kiya)
    if status_str is None:
        if 200 <= status < 300:  # yahan 'http_status' ki jagah 'status' use karein
            status_str = "success"
        else:
            status_str = "error"

    response_data = {
        "status": status_str,
        "message": message,
        "data": data,
    }
    
    if pagination:
        response_data["pagination"] = pagination

    # 2. Response return karte waqt bhi 'status' variable pass karein
    return Response(response_data, status=status)