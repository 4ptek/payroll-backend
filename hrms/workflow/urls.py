from django.urls import path
from .views import WorkflowCreateView, WorkflowListView, WorkflowDetailView, WorkflowActionView

urlpatterns = [
    path('create/', WorkflowCreateView.as_view(), name='create-workflow'),
    path('list/', WorkflowListView.as_view(), name='list-workflow'),
    path('list/<int:pk>/', WorkflowDetailView.as_view(), name='detail-workflow'),
    path('action/', WorkflowActionView.as_view(), name='workflow-action'),
]