from django.urls import path
from .views import OrgAdminDashboardView, HRAdminDashboardView, EmployeeDashboardView

urlpatterns = [
    path('org-admin/', OrgAdminDashboardView.as_view(), name='dashboard-org'),
    path('hr-admin/', HRAdminDashboardView.as_view(), name='dashboard-hr'),
    path('employee/', EmployeeDashboardView.as_view(), name='dashboard-employee'),
]