from django.urls import path
from .views import AssignPermissionsAPI, GetSidebarModulesAPI, GetAllRolesPermissionMatrixAPI, ModuleListAPIView, ModuleDetailAPIView

urlpatterns = [
    path('assign-permissions', AssignPermissionsAPI.as_view(), name='assign-permissions'),
    path('sidebar/<int:roleId>', GetSidebarModulesAPI.as_view(), name='get-sidebar-modules'),
    path('permissions-matrix', GetAllRolesPermissionMatrixAPI.as_view(), name='get-permission-matrix'),
    path('modules/', ModuleListAPIView.as_view(), name='module-list'),
    path('modules/<int:pk>/', ModuleDetailAPIView.as_view(), name='module-detail'),
]
