from django.urls import path
from .views import RoomListCreateView, BookingListCreateView, RoomUpdateDeleteView

urlpatterns = [
    path('rooms/', RoomListCreateView.as_view(), name='room-list-create'),
    path('bookings/', BookingListCreateView.as_view(), name='booking-list-create'),
    path('rooms/<int:room_id>/', RoomUpdateDeleteView.as_view(), name='room-update-delete'),
]