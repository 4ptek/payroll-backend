from department.models import Departments
from rest_framework import serializers

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departments
        fields = ["id", "name"]
        read_only_fields = ["id"]
