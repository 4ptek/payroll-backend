from django.urls import path
from .views import SalaryStructureCreateView, SalaryStructureListView

urlpatterns = [
    path('', SalaryStructureCreateView.as_view(), name='create-salary-structure'),
    path('list', SalaryStructureListView.as_view(), name='list-salary-structure'),
    
]