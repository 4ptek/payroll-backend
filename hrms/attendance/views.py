from django.shortcuts import render
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from .models import Attendancepolicies, Attendance
from .serializers import AttendancePolicySerializer, AttendanceSerializer
from rest_framework.views import APIView
from Helpers.ResponseHandler import custom_response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

class AttendancePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100 

class AttendancePolicyListCreateView(generics.ListCreateAPIView):
    serializer_class = AttendancePolicySerializer
    pagination_class = AttendancePagination

    def get_queryset(self):
        """
        Filters policies by organizationid, shift times, source, and active status.
        """
        queryset = Attendancepolicies.objects.all()
        
        org_id = self.request.query_params.get('organizationid')
        if org_id is not None:
            queryset = queryset.filter(organizationid=org_id)

        # --- New Filters ---
        
        # 1. Filter by Shift Start (e.g., ?shiftstart=09:00:00)
        shift_start = self.request.query_params.get('shiftstart')
        if shift_start is not None:
            queryset = queryset.filter(shiftstart=shift_start)

        # 2. Filter by Shift End (e.g., ?shiftend=18:00:00)
        shift_end = self.request.query_params.get('shiftend')
        if shift_end is not None:
            queryset = queryset.filter(shiftend=shift_end)

        # 3. Filter by Attendance Source (e.g., ?attendancesource=Biometric)
        attendance_source = self.request.query_params.get('attendancesource')
        if attendance_source is not None:
            queryset = queryset.filter(attendancesource__icontains=attendance_source)

        # 4. Filter by Is Active (e.g., ?isactive=true)
        is_active = self.request.query_params.get('isactive')
        if is_active is not None:
            # Convert string 'true'/'false' from URL to Python Boolean
            if is_active.lower() == 'true':
                queryset = queryset.filter(isactive=True)
            elif is_active.lower() == 'false':
                queryset = queryset.filter(isactive=False)
            
        return queryset.order_by('-id') # Best practice: order by ID for consistent pagination
    
class AttendanceListCreateView(generics.ListCreateAPIView):
    serializer_class = AttendanceSerializer
    pagination_class = AttendancePagination  # 2. Attach Pagination here

    def get_queryset(self):
        """
        Supports filtering by:
        - organizationid
        - attendancepolicyid
        - startdate (Exact match)
        - enddate (Exact match)
        - status (Exact match, e.g., 'Open', 'Closed')
        """
        queryset = Attendance.objects.all().order_by('-id')
        
        # 1. Filter by Organization ID
        org_id = self.request.query_params.get('organizationid')
        if org_id:
            queryset = queryset.filter(organizationid_id=org_id)
            
        # 2. Filter by Attendance Policy ID
        policy_id = self.request.query_params.get('attendancepolicyid')
        if policy_id:
            queryset = queryset.filter(attendancepolicyid_id=policy_id)

        # 3. Filter by Start Date
        start_date = self.request.query_params.get('startdate')
        if start_date:
            queryset = queryset.filter(startdate=start_date)

        # 4. Filter by End Date
        end_date = self.request.query_params.get('enddate')
        if end_date:
            queryset = queryset.filter(enddate=end_date)

        # 5. Filter by Status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status__iexact=status)

        return queryset
    
    
class ProcessAttendanceView(APIView):
    def post(self, request, pk):
        """
        Process an attendance cycle.
        """
        attendance = get_object_or_404(Attendance, pk=pk)

        # Check if already processed
        if attendance.status == 'Processed':
             # Error case ke liye standard response ya custom error structure use karein
             return custom_response(
                 data=None,
                 message="This attendance cycle is already processed.", # Typo fixed here
                 http_status=status.HTTP_400_BAD_REQUEST,
                 status_str="error" # Explicitly saying this is an error
             )

        # Update fields
        attendance.status = 'Processed'
        attendance.processedat = timezone.now()
        
        user_id = request.data.get('processedby')
        if user_id:
            attendance.processedby_id = user_id
        
        attendance.save()
        
        # Prepare response data
        data = {
            "id": attendance.id,
            "status": attendance.status,
            "processedat": attendance.processedat,
            "processedby": attendance.processedby_id
        }

        return custom_response(
            data=data, 
            message="Attendance processed successfully.", 
            status=status.HTTP_200_OK
        )