from django.urls import path
from .views import BranchCreateView

urlpatterns = [
    path('create/', BranchCreateView.as_view(), name='create-branch'),
]