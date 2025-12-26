from rest_framework import serializers
from .models import Organizations
from .models import Organizationroles
from designation.models import Designations
from rest_framework.validators import UniqueValidator  
from django.utils import timezone
from branches.serializers import BranchSerializer
from department.serializers import DepartmentSerializer
from branches.models import Branches
from department.models import Departments


class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designations
        fields = ['id', 'title', 'organizationid', 'isactive']

class OrganizationRoleSerializer(serializers.ModelSerializer):
    designation_details = serializers.SerializerMethodField()

    class Meta:
        model = Organizationroles
        fields = ['id', 'name', 'reportto', 'organizationid', 'designation_details']
        read_only_fields = ['organizationid'] 
        extra_kwargs = {
            'name': {'validators': [UniqueValidator(queryset=Organizationroles.objects.all())]}
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.reportto:
            data['reportto'] = {
                "id": instance.reportto.id,
                "name": instance.reportto.name,
            }
        return data
    
    def get_designation_details(self, obj):
        try:
            designation = Designations.objects.get(
                title=obj.name,
                organizationid=obj.organizationid,
                isdelete=False
            )
            return DesignationSerializer(designation).data
        except Designations.DoesNotExist:
            return None
    
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departments
        fields = ["id", "name"]
        read_only_fields = ["id"]

class BranchSerializer(serializers.ModelSerializer):
    departments = DepartmentSerializer(many=True, write_only=True)

    class Meta:
        model = Branches
        fields = ['id', 'name', 'address', 'city', 'departments']
            
    def to_representation(self, instance):
        response = super().to_representation(instance)
        
        active_departments = Departments.objects.filter(branchid=instance.id, isdelete=False)
        
        response['departments'] = DepartmentSerializer(active_departments, many=True).data
        return response

class OrganizationSerializer(serializers.ModelSerializer):
    branches = BranchSerializer(many=True, required=False) 
    
    class Meta:
        model = Organizations
        fields = [
            'id', 'name', 'code', 'email', 'phone', 'address', 'country',
            'currency', 'timezone', 'organizationlogo', 'createdby', 
            'isactive', 'isdelete', 'createdat', 'updatedby', 'updateat', 
            'deletedby', 'deleteat', 'branches'
        ]
        read_only_fields = ['createdby', 'updatedby', 'deletedby', 'createdat', 'updateat', 'deleteat', 'id']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        active_branches = Branches.objects.filter(organizationid=instance.id, isdelete=False)
        response['branches'] = BranchSerializer(active_branches, many=True).data
        return response

    def validate_email(self, value):
        qs = Organizations.objects.filter(email=value, isdelete=False)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This email is already used.")
        return value

    def validate_code(self, value):
        qs = Organizations.objects.filter(code=value, isdelete=False)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This code is already used.")
        return value
    
    def validate_phone(self, value):
        qs = Organizations.objects.filter(phone=value, isdelete=False)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This phone number is already used.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        branches_data = validated_data.pop('branches', [])

        org = Organizations.objects.create(
            **validated_data,
            createdby=request.user if request else None,
            createdat=timezone.now(),
            isactive=True,
            isdelete=False
        )

        for branch_data in branches_data:
            departments_data = branch_data.pop('departments', []) 
            
            branch = Branches.objects.create(
                organizationid=org,
                **branch_data,
                createdby=request.user if request else None,
                createdat=timezone.now(),
                isactive=True,
                isdelete=False
            )
            
            for dept_data in departments_data:
                Departments.objects.create(
                    organizationid=org,
                    branchid=branch,
                    **dept_data, # name yahan se milega
                    createdby=request.user if request else None,
                    createdat=timezone.now(),
                    isactive=True,
                    isdelete=False
                )

        return org

    def update(self, instance, validated_data):
        request = self.context.get('request')
        branches_data = validated_data.pop('branches', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.updatedby = request.user if request else None
        instance.updateat = timezone.now()
        instance.save()

        for branch_item in branches_data:
            departments_data = branch_item.pop('departments', [])
            branch = Branches.objects.create(
                organizationid=instance,
                **branch_item,
                createdby=request.user if request else None,
                createdat=timezone.now(),
                isactive=True,
                isdelete=False
            )
            for dept_item in departments_data:
                Departments.objects.create(
                    organizationid=instance,
                    branchid=branch,
                    **dept_item,
                    createdby=request.user if request else None,
                    createdat=timezone.now(),
                    isactive=True,
                    isdelete=False
                )

        return instance