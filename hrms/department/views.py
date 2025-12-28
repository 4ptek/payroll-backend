from django.shortcuts import render
from rest_framework import generics
from department.models import Departments
from department.serializers import DepartmentCreateSerializer
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone   

class DepartmentCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    
    queryset = Departments.objects.all()
    serializer_class = DepartmentCreateSerializer

    def perform_create(self, serializer):
        serializer.save(
            createdat=timezone.now(),
            isactive=True,
            isdelete=False,
            createdby=self.request.user if self.request.user.is_authenticated else None
        )
