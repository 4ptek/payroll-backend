from django.urls import path
from .views import AssignPermissionsAPI, GetSidebarModulesAPI, GetAllRolesPermissionMatrixAPI

urlpatterns = [
    path('assign-permissions', AssignPermissionsAPI.as_view(), name='assign-permissions'),
    path('sidebar/<int:roleId>', GetSidebarModulesAPI.as_view(), name='get-sidebar-modules'),
    path('permissions-matrix', GetAllRolesPermissionMatrixAPI.as_view(), name='get-permission-matrix'),
]