from django.urls import path
from .views import CreatePayrollView, PayrollDetailView, PayrollProcessView

urlpatterns = [
    path('generate/', CreatePayrollView.as_view(), name='generate-payroll'),
    path('<int:id>/', PayrollDetailView.as_view(), name='payroll-detail'),
    path('process/<int:id>', PayrollProcessView.as_view(), name='payroll-process'),
    
]