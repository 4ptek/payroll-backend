from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from .models import Rooms, Bookings
from .serializers import RoomSerializer, BookingSerializer

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
        org_id = self.request.query_params.get('org_id') # Organization Filter Added

        # Apply Filters
        if org_id:
            queryset = queryset.filter(organizationid=org_id)
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        if date:
            queryset = queryset.filter(booking_date=date)
            
        # Pagination ke liye ordering zaroori hai (Latest bookings pehle)
        return queryset.order_by('-booking_date', '-start_time')

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            created_at=timezone.now()
        )