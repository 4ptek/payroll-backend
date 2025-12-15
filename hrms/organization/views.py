from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Organizations, Organizationroles
from .serializers import OrganizationSerializer, OrganizationRoleSerializer
from designation.serializers import DesignationSerializer
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from Helpers.ResponseHandler import custom_response
from django.db import transaction

class CustomPagination(PageNumberPagination):
    page_size = 10                 
    page_size_query_param = 'limit'
    max_page_size = None


class OrganizationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organizations = Organizations.objects.filter(isdelete=False).order_by('-id')
        paginator = CustomPagination()
        result_page = paginator.paginate_queryset(organizations, request)
        
        if result_page is not None:
            serializer = OrganizationSerializer(result_page, many=True)
            paginated_data = {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data
            }
            
            return custom_response(
                data=paginated_data, 
                message="Organization list fetched successfully", 
                status=status.HTTP_200_OK
            )
            
        serializer = OrganizationSerializer(organizations, many=True)
        return custom_response(
            data=serializer.data, 
            message="Organization list fetched successfully", 
            status=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = OrganizationSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            org = serializer.save()
            output_serializer = OrganizationSerializer(org, context={'request': request})
            
            return custom_response(
                data=output_serializer.data, 
                message="Organization created successfully", 
                status=status.HTTP_201_CREATED
            )
            
        return custom_response(
            data=serializer.errors, 
            message="Validation Error", 
            status=status.HTTP_400_BAD_REQUEST
        )


class OrganizationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Organizations.objects.get(pk=pk, isdelete=False)
        except Organizations.DoesNotExist:
            return None

    def get(self, request, pk):
        organization = self.get_object(pk)
        if not organization:
            return Response(
                {"detail": "Organization not found"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = OrganizationSerializer(organization)
        return Response(serializer.data)

    def patch(self, request, pk):
        organization = self.get_object(pk)
        if not organization:
            return Response(
                {"detail": "Organization not found"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = OrganizationSerializer(
            organization, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save(updatedby=request.user, updateat=timezone.now())
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        organization = self.get_object(pk)
        if not organization:
            return Response(
                {"detail": "Organization not found"}, status=status.HTTP_404_NOT_FOUND
            )
        organization.isdelete = True
        organization.deletedby = request.user
        organization.deleteat = timezone.now()
        organization.save()
        return Response(
            {"detail": "Organization deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class OrganizationRoleCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrganizationRoleSerializer(data=request.data)
        
        if serializer.is_valid():
            org_id = request.auth.get("org_id") if request.auth else None
            
            if not org_id:
                return custom_response(
                    message="Organization not found in token",
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            try:
                with transaction.atomic():
                    role_instance = serializer.save(organizationid_id=org_id)
                    
                    designation_input = {
                        "title": role_instance.name,
                    }
                    
                    desig_serializer = DesignationSerializer(data=designation_input)
                    
                    if desig_serializer.is_valid():
                        desig_instance = desig_serializer.save(
                            organizationid_id=org_id,
                            createdby=request.user,
                            createdat=timezone.now(),
                            isactive=True,
                            isdelete=False
                        )
                    else:
                        raise Exception(f"Designation Error: {desig_serializer.errors}")
            
            except Exception as e:
                return custom_response(
                    data=str(e),
                    message="Error creating Role or Designation",
                    status=status.HTTP_400_BAD_REQUEST
                )

            response_data = {
                "role": serializer.data,
                "designation": desig_serializer.data 
            }

            return custom_response(
                data=response_data,
                message="Organization Role and Designation created successfully",
                status=status.HTTP_201_CREATED
            )
            
        return custom_response(
            data=serializer.errors,
            message="Validation Error",
            status=status.HTTP_400_BAD_REQUEST
        )
        
    def get(self, request):
        org_id = request.auth.get("org_id") if request.auth else None
        
        if not org_id:
            return custom_response(
                message="Organization not found in token",
                status=status.HTTP_400_BAD_REQUEST
            )
            
        roles = Organizationroles.objects.filter(
            organizationid_id=org_id
        ).order_by("id")

        serializer = OrganizationRoleSerializer(roles, many=True)
        
        return custom_response(
            data=serializer.data,
            message="Organization Roles fetched successfully",
            status=status.HTTP_200_OK
        )
