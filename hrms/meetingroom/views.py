from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from .models import Rooms, Bookings
from .serializers import RoomSerializer, BookingSerializer
from user_rbac.models import Modules
from workflow.utils import initiate_workflow
from rest_framework.response import Response
from rest_framework import status
from .utils import generate_unique_otp

# --- 1. Custom Pagination Class ---
class StandardPagination(PageNumberPagination):
    page_size = 10  # Ek page par 10 records
    page_size_query_param = 'page_size'
    max_page_size = 100

# --- 2. Room API ---
class RoomListCreateView(generics.ListCreateAPIView):
    queryset = Rooms.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination  # Pagination Added

    def get_queryset(self):
        queryset = super().get_queryset()
        org_id = self.request.query_params.get('org_id')
        
        if org_id:
            queryset = queryset.filter(organizationid=org_id)
            
        # Pagination ke liye order_by zaroori hai
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            created_at=timezone.now()
        )


# --- 3. Booking API ---
class BookingListCreateView(generics.ListCreateAPIView):
    queryset = Bookings.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination  # Pagination Added

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filters parameters
        room_id = self.request.query_params.get('room_id')
        date = self.request.query_params.get('date')
        org_id = self.request.query_params.get('org_id') 
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        # Apply Filters
        if org_id:
            queryset = queryset.filter(organizationid=org_id)
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        if date:
            queryset = queryset.filter(booking_date=date)
        if start_date:
            queryset = queryset.filter(booking_date__gte=start_date) # >= start_date        
        if end_date:
            queryset = queryset.filter(booking_date__lte=end_date)
        if start_date and end_date:
            queryset = queryset.filter(booking_date__range=[start_date, end_date])
            
        # Pagination ke liye ordering zaroori hai (Latest bookings pehle)
        return queryset.order_by('-booking_date', '-start_time')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking_instance = serializer.save(
            created_by=self.request.user,
            created_at=timezone.now(),
            otp=generate_unique_otp()
        )
        try:
            org_instance = getattr(request.user, 'organizationid', None)
            initiator = getattr(request.user, 'employeeid', None)
            module_id_val = 63

            try:
                module_instance = Modules.objects.get(pk=module_id_val)
            except Modules.DoesNotExist:
                print("Module not found for Booking Workflow")
                module_instance = None
                
            if initiator and org_instance and module_instance:
                initiate_workflow(
                    record_id=booking_instance.booking_id,
                    module_id=module_instance,
                    organization_id=org_instance,
                    initiator_employee=initiator,
                    user=request.user
                )
                print(f"Workflow initiated for Booking ID: {booking_instance.booking_id}")
            else:
                print("Skipped Workflow: Missing Initiator, Org ID, or Module")

        except Exception as e:
            print(f"Exception in Booking Workflow Block: {str(e)}")
            
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)