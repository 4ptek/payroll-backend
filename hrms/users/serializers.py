from django.utils import timezone
from rest_framework import serializers
from .models import Users, Userroles
from organization.models import Organizations
from employee.models import Employees
from .utils import make_password
from rest_framework.validators import UniqueValidator   

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
        extra_kwargs = {
            'rolename': {'validators': [UniqueValidator(queryset=Userroles.objects.all())]}
        }
    def create(self, validated_data):
        request = self.context.get("request")
        org_id = request.auth.get("org_id") if hasattr(request, "auth") else None    
        org_instance = Organizations.objects.get(id=org_id) if org_id else None
        validated_data['createdby'] = org_instance
        validated_data['isactive'] = True
        validated_data['isdelete'] = False
        validated_data['createdat'] = timezone.now()
        return super().create(validated_data)

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
    
    def validate_email(self, value):
        if value and Users.objects.filter(email=value, isdelete=False).exists():
            raise serializers.ValidationError("This email is already used.")
        return value
    
    def validate_username(self, value):
        if Users.objects.filter(username=value, isdelete=False).exists():
            raise serializers.ValidationError("This username is already used.")
        return value
    
