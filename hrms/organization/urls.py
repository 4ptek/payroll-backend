from django.urls import path
from .views import OrganizationListView, OrganizationDetailView, OrganizationRoleCreateView, OrganizationRoleDetailView

urlpatterns = [
    path('', OrganizationListView.as_view(), name='organization-list-create'),
    path('<int:pk>', OrganizationDetailView.as_view(), name='organization-detail'),
    path('role', OrganizationRoleCreateView.as_view(), name='organization-role-create'),
    path('role/<int:pk>/', OrganizationRoleDetailView.as_view(), name='org-role-detail'),
]
