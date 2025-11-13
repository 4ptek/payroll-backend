from rest_framework import serializers
from .models import Users, Userroles
from organization.models import Organizations
from employee.models import Employees
from .utils import make_password

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizations
        fields = ['id', 'name'] 

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employees
        fields = ['id', 'firstname', 'lastname']

class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Userroles
        fields = ['id', 'rolename']

class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = [
            'id', 'username', 'email', 'phone', 'lastlogin', 
            'organizationid', 'roleid', 'employeeid', 
            'isactive', 'isdelete', 'userpassword'
        ]
        extra_kwargs = {
            'userpassword': {'write_only': True}
        }

    def create(self, validated_data):
        raw_password = validated_data.get('userpassword')
        if raw_password:
            validated_data['userpassword'] = make_password(raw_password)
        return super().create(validated_data)
    
    
    def update(self, instance, validated_data):
        raw_password = validated_data.get('userpassword')
        if raw_password:
            validated_data['userpassword'] = make_password(raw_password)
        return super().update(instance, validated_data)