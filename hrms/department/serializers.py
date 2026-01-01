from department.models import Departments
from rest_framework import serializers

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departments
        fields = ["id", "name"]
        read_only_fields = ["id"]


class DepartmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departments
        fields = '__all__'
        read_only_fields = ('createdby', 'createdat', 'updatedby', 'updateat', 'deletedby', 'deleteat', 'isdelete')

class DepartmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departments
        fields = ['name']