from django.urls import path
from .views import EmployeeListView, EmployeeDetailView

urlpatterns = [
    path('', EmployeeListView.as_view(), name='employee-list-create'),
    path('<int:pk>', EmployeeDetailView.as_view(), name='employee-detail'),
]
