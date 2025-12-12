from rest_framework import serializers
from .models import Organizations
from .models import Organizationroles
from rest_framework.validators import UniqueValidator  
from django.utils import timezone
from branches.serializers import BranchSerializer
from department.serializers import DepartmentSerializer
from branches.models import Branches
from department.models import Departments

class OrganizationRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizationroles
        fields = ['id', 'name', 'reportto', 'organizationid']
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

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departments
        fields = ["id", "name"]
        read_only_fields = ["id"]

# 2. Phir BranchSerializer ko sahi se define karein
class BranchSerializer(serializers.ModelSerializer):
    # Change: Isay MethodField se hata kar Nested Serializer bana dein
    # Taake ye writable ho jaye aur POST request mein data accept kare
    departments = DepartmentSerializer(many=True, write_only=True)

    class Meta:
        model = Branches
        fields = ['id', 'name', 'address', 'city', 'departments']

    # Hum 'to_representation' use karenge taake GET request par 
    # sirf active (isdelete=False) departments show hon.
    def to_representation(self, instance):
        response = super().to_representation(instance)
        
        # Filtering logic yahan lagayen
        active_departments = Departments.objects.filter(branchid=instance.id, isdelete=False)
        
        # Override the departments data in the response
        response['departments'] = DepartmentSerializer(active_departments, many=True).data
        return response

# 3. Phir OrganizationSerializer
class OrganizationSerializer(serializers.ModelSerializer):
    # 'read_only=True' hata diya taake Create karte waqt data pass ho sakay
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

    # --- Response Control ---
    def to_representation(self, instance):
        response = super().to_representation(instance)
        # Active branches lana
        active_branches = Branches.objects.filter(organizationid=instance.id, isdelete=False)
        response['branches'] = BranchSerializer(active_branches, many=True).data
        return response

    # --- Field Validations ---
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

    # --- CREATE Logic ---
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
            # AB YAHAN DATA MILEGA (Pehle ye ignore ho raha tha)
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

    # --- UPDATE Logic ---
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