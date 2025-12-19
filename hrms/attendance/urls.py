from django.urls import path
from .views import AttendancePolicyListCreateView, AttendanceListCreateView, ProcessAttendanceView

urlpatterns = [
    # Endpoint: /api/attendance/
    # Endpoint with filter: /api/attendance/attendance-policies/?organizationid=123
    path('attendance-policies/', AttendancePolicyListCreateView.as_view(), name='attendance-policy-list-create'),
    path('', AttendanceListCreateView.as_view(), name='attendance-list-create'),
    path('<int:pk>/process/', ProcessAttendanceView.as_view(), name='attendance-process'),
]