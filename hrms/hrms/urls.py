from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('employees/', include('employee.urls')),
    path('organizations/', include('organization.urls')),
    path('user_rbac/', include('user_rbac.urls')),
    path('workflow/', include('workflow.urls')),
    path('attendance/', include('attendance.urls')),
    path('meeting/', include('meetingroom.urls')),
    path('leaves/', include('leaves.urls')),
    path('salaryStructure/', include('salary_structure.urls')),
    path('payroll/', include('payroll.urls')),
    path('dashboard/', include('dashboard.urls')),
]
