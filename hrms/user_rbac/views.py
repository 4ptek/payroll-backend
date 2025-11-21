from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

from user_rbac.service import RbacService
from .serializers import AssignPermissionSerializer 
#from hrms.permissions import HasRbacPermission # Custom permission from previous chat

class AssignPermissionsAPI(APIView):
    permission_classes = [IsAuthenticated] 
    def post(self, request):
        serializer = AssignPermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = serializer.validated_data
    
        rbac_service = RbacService()
        
        current_user_id = request.auth.get("user_id")
        
        result = rbac_service.assign_permissions(
            dto['role_id'],
            dto['module_id'],
            dto['is_enable'],
            dto['organization_id'],
            current_user_id
        )
        
        return Response(result, status=status.HTTP_200_OK)


class GetSidebarModulesAPI(APIView):
    permission_classes = [IsAuthenticated] 
    
    def get(self, request, roleId):
        try:
            role_id = int(roleId)
        except ValueError:
            return Response({"detail": "Invalid role ID format."}, status=status.HTTP_400_BAD_REQUEST)
        
        rbac_service = RbacService()
        modules = rbac_service.get_modules_by_role(role_id)
        
        return Response(modules, status=status.HTTP_200_OK)


class GetAllRolesPermissionMatrixAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        
        rbac_service = RbacService()
        matrix = rbac_service.get_all_roles_permission_matrix()
        
        return Response(matrix, status=status.HTTP_200_OK)