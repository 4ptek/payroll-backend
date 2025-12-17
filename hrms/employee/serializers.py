from rest_framework import serializers
from .models import Employees
from organization.models import Organizations
from branches.models import Branches
from department.models import Departments
from designation.models import Designations
from users.models import Users

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizations
        fields = ['id', 'name']

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branches
        fields = ['id', 'name']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departments
        fields = ['id', 'name']

class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designations
        fields = ['id', 'title']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['id', 'username', 'email']

class EmployeeSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(source='organizationid', read_only=True)
    branch = BranchSerializer(source='branchid', read_only=True)
    department = DepartmentSerializer(source='departmentid', read_only=True)
    designation = DesignationSerializer(source='designationid', read_only=True)
    
    class Meta:
        model = Employees
        fields = [
            'id', 'organizationid', 'organization',
            'employeecode', 'firstname', 'lastname', 'gender',
            'cnic', 'dateofbirth', 'dateofappointment',
            'branchid', 'branch',
            'departmentid', 'department',
            'designationid', 'designation',
            'basicsalary', 'attendancemachineid',
            'employeetype', 'bankaccountnumber', 'picture',
            'isuser', 'isnew', 'organizationroleid', 'isactive', 'isdelete'
        ]

    def validate_employeecode(self, value):
        qs = Employees.objects.filter(employeecode=value, isdelete=False)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
            
        if qs.exists():
            raise serializers.ValidationError("This employee code is already used.")
        return value
    
    def validate_cnic(self, value):
        if value:
            qs = Employees.objects.filter(cnic=value, isdelete=False)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError("This CNIC is already used.")
        return value
    
    def validate_attendancemachineid(self, value):
        if value:
            qs = Employees.objects.filter(attendancemachineid=value, isdelete=False)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError("This Machine ID is already used.")
        return value