from django.shortcuts import render
from rest_framework import generics
from branches.models import Branches
from branches.serializers import BranchCreateSerializer, BranchUpdateSerializer
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status

class BranchCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    
    queryset = Branches.objects.all()
    serializer_class = BranchCreateSerializer

    def perform_create(self, serializer):
        serializer.save(
            createdat=timezone.now(),
            isactive=True,
            isdelete=False,
            createdby=self.request.user if self.request.user.is_authenticated else None
        )

class BranchUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Branches.objects.filter(isdelete=False)
    serializer_class = BranchUpdateSerializer
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)

        serializer.save(
            updatedby=request.user if request.user.is_authenticated else None,
            updateat=timezone.now()
        )
        
        return Response({
            "message": "Branch updated successfully",
            "data": serializer.data,
            "status": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        instance.isdelete = True
        instance.isactive = False 
        instance.deletedby = request.user if request.user.is_authenticated else None
        instance.deleteat = timezone.now()
        
        instance.save()
        
        return Response({
            "message": "Branch deleted successfully",
            "status": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)