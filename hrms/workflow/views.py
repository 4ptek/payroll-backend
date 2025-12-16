from django.shortcuts import render
from .serializers import WorkflowsSerializer, WorkflowsGetSerializer
from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from .models import Workflows
from .serializers import WorkflowsSerializer
from Helpers.ResponseHandler import custom_response
from django.utils import timezone

class WorkflowListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        workflows = Workflows.objects.filter(isactive=True, isdelete=False)

        serializer = WorkflowsGetSerializer(workflows, many=True)
        
        return custom_response(
            data=serializer.data,
            message="Workflows fetched successfully",
            status=status.HTTP_200_OK
        )
        
class WorkflowDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            workflow = Workflows.objects.get(pk=pk, isactive=True, isdelete=False)
        except Workflows.DoesNotExist:
            return custom_response(
                message="Workflow not found",
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = WorkflowsGetSerializer(workflow)
        
        return custom_response(
            data=serializer.data,
            message="Workflow details fetched successfully",
            status=status.HTTP_200_OK
        )        

class WorkflowCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WorkflowsSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            
            serializer.save(
                createdby=request.user,
                updatedby=request.user,
                deletedby=request.user,
                createdat=timezone.now(),
                isactive=True,
                isdelete=False
            )

            return custom_response(
                data=serializer.data,
                message="Workflow created successfully",
                status=status.HTTP_201_CREATED
            )
        
        return custom_response(
            data=serializer.errors,
            message="Validation Error",
            status=status.HTTP_400_BAD_REQUEST
        )