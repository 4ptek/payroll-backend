from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.utils import timezone
from .models import LeavePeriods, LeaveTypes
from .serializers import LeavePeriodSerializer, LeaveTypeSerializer

# --- 1. Pagination Class ---
class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# --- 2. Custom Response Helper (As provided) ---
def custom_response(data, message, status, pagination=None, status_str=None): 
    """
    Standardized response wrapper.
    """
    if status_str is None:
        if 200 <= status < 300:
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

    return Response(response_data, status=status)