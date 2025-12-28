from django.urls import path
from .views import DepartmentCreateView

urlpatterns = [
    path('create/', DepartmentCreateView.as_view(), name='create-department'),
]