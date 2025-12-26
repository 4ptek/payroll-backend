from django.urls import path
from .views import LeavePeriodListCreateView, LeaveTypeListCreateView

urlpatterns = [
    path('leave-periods/', LeavePeriodListCreateView.as_view(), name='leave-periods'),
    path('leave-types/', LeaveTypeListCreateView.as_view(), name='leave-types'),
]