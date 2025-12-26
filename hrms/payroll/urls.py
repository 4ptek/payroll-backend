from django.urls import path
from .views import CreatePayrollView, PayrollDetailView, PayrollProcessView, PayrollListView, EmployeeSalarySlipView

urlpatterns = [
    path('generate/', CreatePayrollView.as_view(), name='generate-payroll'),
    path('<int:id>/', PayrollDetailView.as_view(), name='payroll-detail'),
    path('process/<int:id>', PayrollProcessView.as_view(), name='payroll-process'),
    path('list/', PayrollListView.as_view(), name='payroll-list'),
    path('salary-slip/<int:payroll_id>/<int:employee_id>/', EmployeeSalarySlipView.as_view(), name='salary-slip-detail'),
]