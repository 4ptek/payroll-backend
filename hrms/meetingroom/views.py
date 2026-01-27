from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Rooms, Bookings
from .serializers import RoomSerializer, BookingSerializer, RoomUpdateSerializer


class StandardPagination(PageNumberPagination):
    page_size = 10  # Ek page par 10 records
    page_size_query_param = 'page_size'
    max_page_size = 100

class RoomListCreateView(generics.ListCreateAPIView):
    queryset = Rooms.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        org_id = self.request.query_params.get('org_id')
        
        if org_id:
            queryset = queryset.filter(organizationid=org_id)
            
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
    pagination_class = StandardPagination

    def get_queryset(self):
        # Optimization
        queryset = super().get_queryset().select_related(
            'room', 'organizationid'
        ).prefetch_related(
            'bookinginvited_set', 
            'bookinginvited_set__userid'
        )
        
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
        # if start_date:
        #     queryset = queryset.filter(booking_date__gte=start_date)     
        # if end_date:
        #     queryset = queryset.filter(booking_date__lte=end_date)
        if start_date and end_date:
            queryset = queryset.filter(booking_date__range=[start_date, end_date])        

        return queryset.order_by('-booking_date', '-start_time')
    
class RoomUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Rooms.objects.all()
    serializer_class = RoomUpdateSerializer 
    lookup_field = 'room_id'
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "Room deleted successfully"}, status=status.HTTP_200_OK)
