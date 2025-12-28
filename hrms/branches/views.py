from django.shortcuts import render
from rest_framework import generics
from branches.models import Branches
from branches.serializers import BranchCreateSerializer
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

# Create your views here.
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