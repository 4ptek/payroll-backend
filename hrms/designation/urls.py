from django.urls import path
from .views import DesignationCreateView, DesignationUpdateDeleteView

urlpatterns = [
    path('create/', DesignationCreateView.as_view(), name='create-designation'),
    path('<int:id>/', DesignationUpdateDeleteView.as_view(), name='update-delete-designation'),
]