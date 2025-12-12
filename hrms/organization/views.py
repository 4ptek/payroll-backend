from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Organizations, Organizationroles
from .serializers import OrganizationSerializer, OrganizationRoleSerializer
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination

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
            return paginator.get_paginated_response(serializer.data)

        serializer = OrganizationSerializer(organizations, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = OrganizationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            org = serializer.save()  # createdby handled in serializer.create()
            output_serializer = OrganizationSerializer(org, context={'request': request})
            print(output_serializer.data)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
            org_id = request.auth.get("org_id")
            if not org_id:
                return Response(
                    {"detail": "Organization not found in token"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer.save(organizationid_id=org_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def get(self, request):
        org_id = request.auth.get("org_id")
        if not org_id:
            return Response(
            {"detail": "Organization not found in token"},
            status=status.HTTP_400_BAD_REQUEST,
        )

        roles = Organizationroles.objects.filter(
        organizationid_id=org_id
        ).order_by("id")

        serializer = OrganizationRoleSerializer(roles, many=True)
        return Response(serializer.data)
