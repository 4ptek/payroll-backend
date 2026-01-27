from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Designations
from .serializers import DesignationCreateSerializer, DesignationUpdateSerializer

class DesignationCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Designations.objects.all()
    serializer_class = DesignationCreateSerializer

    def perform_create(self, serializer):
        serializer.save(
            createdat=timezone.now(),
            isactive=True,
            isdelete=False,
            createdby=self.request.user
        )

class DesignationUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Designations.objects.filter(isdelete=False)
    serializer_class = DesignationUpdateSerializer
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)

        serializer.save(
            updatedby=request.user,
            updateat=timezone.now()
        )
        
        return Response({
            "message": "Designation updated successfully",
            "data": serializer.data,
            "status": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Soft Delete Logic
        instance.isdelete = True
        instance.isactive = False 
        instance.deletedby = request.user
        instance.deleteat = timezone.now()
        instance.save()
        
        return Response({
            "message": "Designation deleted successfully",
            "status": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)