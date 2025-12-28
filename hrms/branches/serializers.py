from branches.models import Branches
from department.serializers import DepartmentSerializer
from rest_framework import serializers
from department.models import Departments

class BranchSerializer(serializers.ModelSerializer):
    # Fetch departments manually using a method
    departments = serializers.SerializerMethodField()

    class Meta:
        model = Branches
        fields = ['id', 'name', 'address', 'city', 'departments']

    def get_departments(self, obj):
        # Sirf wo departments layen jo delete nahi huay
        qs = Departments.objects.filter(branchid=obj.id, isdelete=False)
        return DepartmentSerializer(qs, many=True).data


class BranchCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branches
        # We include all fields, but some will be read_only because the backend handles them
        fields = '__all__'
        read_only_fields = ('createdby', 'createdat', 'updatedby', 'updateat', 'deletedby', 'deleteat', 'isdelete')