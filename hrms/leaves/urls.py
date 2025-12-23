from django.urls import path
from .views import LeavePeriodListCreateView, LeaveTypeListCreateView, LeaveBalanceListView, LeaveRequestListCreateView

urlpatterns = [
    path('leave-periods/', LeavePeriodListCreateView.as_view(), name='leave-periods'),
    path('leave-types/', LeaveTypeListCreateView.as_view(), name='leave-types'),
    path('leave-balances/', LeaveBalanceListView.as_view(), name='leave-balances'),
    path('leave-requests/', LeaveRequestListCreateView.as_view(), name='leave-requests'),
]