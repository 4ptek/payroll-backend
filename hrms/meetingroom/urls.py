from django.urls import path
from .views import RoomListCreateView, BookingListCreateView

urlpatterns = [
    path('rooms/', RoomListCreateView.as_view(), name='room-list-create'),
    path('bookings/', BookingListCreateView.as_view(), name='booking-list-create'),
]