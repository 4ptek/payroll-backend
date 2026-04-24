from django.urls import path
from .views import (
    PlatformCreateView,
    PlatformListView,
    PlatformDetailView,
    EmployeeEmailCreateView,
    EmployeeEmailListView,
    EmployeeEmailDetailView,
    PlatformAccountCreateView,
    PlatformAccountListView,
    PlatformAccountDetailView,
    EmployeePlatformProfileView,
)

urlpatterns = [
    path('', PlatformCreateView.as_view(), name='platform-create'),
    path('list', PlatformListView.as_view(), name='platform-list'),
    path('<int:platform_id>/', PlatformDetailView.as_view(), name='platform-detail'),
    path('emails/', EmployeeEmailCreateView.as_view(), name='employee-email-create'),
    path('emails/list', EmployeeEmailListView.as_view(), name='employee-email-list'),
    path('emails/<int:email_id>/', EmployeeEmailDetailView.as_view(), name='employee-email-detail'),
    path('accounts/', PlatformAccountCreateView.as_view(), name='platform-account-create'),
    path('accounts/list', PlatformAccountListView.as_view(), name='platform-account-list'),
    path('accounts/<int:account_id>/', PlatformAccountDetailView.as_view(), name='platform-account-detail'),
    path('accounts/employee/<int:employee_id>/', EmployeePlatformProfileView.as_view(), name='employee-platform-profile'),
]