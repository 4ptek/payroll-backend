from django.urls import path
from .views import DepartmentCreateView, DepartmentUpdateDeleteView

urlpatterns = [
    path('create/', DepartmentCreateView.as_view(), name='create-department'),
    path('<int:id>/', DepartmentUpdateDeleteView.as_view(), name='update-delete-department'),
]