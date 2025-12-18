from rest_framework import serializers
from .models import Employees, EmployeeOffboarding
from organization.models import Organizations
from branches.models import Branches
from department.models import Departments
from designation.models import Designations
from users.models import Users
from employee.models import EmployeeFinalSettlement

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

class EmployeeFinalSettlementInputSerializer(serializers.Serializer):
    last_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    leave_encashment = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, default=0
    )
    bonus = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, default=0
    )
    other_earnings = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, default=0
    )
    deductions = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, default=0
    )
    remarks = serializers.CharField(required=False, allow_blank=True)


    
class EmployeeOffboardingCreateSerializer(serializers.ModelSerializer):

    settlement = EmployeeFinalSettlementInputSerializer(write_only=True)

    class Meta:
        model = EmployeeOffboarding
        fields = [
            'employee',
            'offboarding_type',
            'last_working_day',
            'reason',
            'settlement'
        ]

    def validate_employee(self, value):
        if not value.isactive:
            raise serializers.ValidationError("Employee is already inactive.")

        if EmployeeOffboarding.objects.filter(
            employee=value,
            status__in=['PENDING', 'IN_PROGRESS'],
            is_active=True
        ).exists():
            raise serializers.ValidationError(
                "Offboarding already initiated for this employee."
            )

        return value
    
class EmployeeOffboardingSerializer(serializers.ModelSerializer):

    employee_name = serializers.SerializerMethodField()

    employee = EmployeeSerializer(read_only=True)
    class Meta:
        model = EmployeeOffboarding
        fields = [
            'id',
            'employee',
            'employee_name',
            'offboarding_type',
            'last_working_day',
            'reason',
            'status',
            'requested_by',
            'requested_at',
            'completed_at'
        ]

    def get_employee_name(self, obj):
        return f"{obj.employee.firstname} {obj.employee.lastname or ''}"


class EmployeeFinalSettlementSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmployeeFinalSettlement
        fields = [
            'id',
            'offboarding',
            'employee',
            'last_salary',
            'leave_encashment',
            'bonus',
            'other_earnings',
            'deductions',
            'net_payable',
            'status',
            'remarks'
        ]
        read_only_fields = ['net_payable', 'status']

    def validate(self, attrs):
        employee = attrs.get('employee')
        offboarding = attrs.get('offboarding')

        existing = EmployeeFinalSettlement.objects.filter(
            employee=employee,
            isdelete=False,
            status__in=['DRAFT', 'IN_PROGRESS', 'APPROVED']
        ).exists()

        if existing:
            raise serializers.ValidationError(
                "Final settlement already exists for this employee."
            )

        # ensure same offboarding doesn't create multiple settlements
        if EmployeeFinalSettlement.objects.filter(
            offboarding=offboarding,
            isdelete=False
        ).exists():
            raise serializers.ValidationError(
                "Final settlement already created for this offboarding."
            )

        return attrs