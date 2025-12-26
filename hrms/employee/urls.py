from django.urls import path
from .views import EmployeeListView, EmployeeDetailView, EmployeeOffboardingListView, EmployeeOffboardingCreateView, EmployeeOffboardingDetailView, WorkflowChecklistView

urlpatterns = [
    path('', EmployeeListView.as_view(), name='employee-list-create'),
    path('<int:pk>', EmployeeDetailView.as_view(), name='employee-detail'),
    path('offboarding/', EmployeeOffboardingListView.as_view()),
    path('offboarding/create/', EmployeeOffboardingCreateView.as_view()),
    path('offboarding/<int:pk>/', EmployeeOffboardingDetailView.as_view()),
    path('workflow/checklist/<int:record_id>/<str:module_name>/', WorkflowChecklistView.as_view()),
]
