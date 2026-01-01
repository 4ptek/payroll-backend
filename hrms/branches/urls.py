from django.urls import path
from .views import BranchCreateView, BranchUpdateDeleteView

urlpatterns = [
    path('create/', BranchCreateView.as_view(), name='create-branch'),
    path('<int:id>/', BranchUpdateDeleteView.as_view(), name='update-delete-branch'),
]