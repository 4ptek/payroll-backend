from rest_framework import serializers
from .models import Attendancepolicies, Attendance, Attendancedetail
from organization.models import Organizations
from users.models import Users
from employee.models import Employees

class EmployeeMiniSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='departmentid.name', read_only=True)
    designation_name = serializers.CharField(source='designationid.name', read_only=True)

    class Meta:
        model = Employees
        fields = ['id', 'employeecode', 'firstname', 'lastname', 'department_name', 'designation_name', 'picture']

class AttendanceDetailReportSerializer(serializers.ModelSerializer):
    employee_details = EmployeeMiniSerializer(source='employeeid', read_only=True)

    class Meta:
        model = Attendancedetail
        fields = ['id', 'attendancedate', 'status', 'checkin', 'checkout', 'totalhours', 'remarks', 'employee_details']
        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['id', 'username', 'email'] # Customize these fields as needed
        
class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizations
        fields = ['id', 'name', 'code'] # Add whatever fields you want to show

class AttendanceDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendancedetail
        fields = '__all__'

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    attendanceid = serializers.IntegerField(required=True)
    calculation_mode = serializers.ChoiceField(choices=['manual', 'auto'], default='auto')


class AttendancePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendancepolicies
        fields = '__all__'
        
class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'

    def to_representation(self, instance):
        """
        Override to show full object details for Organization and Policy
        instead of just the ID when reading data (GET).
        """
        response = super().to_representation(instance)
        
        # Replace 'organizationid' ID with full Organization object
        if instance.organizationid:
            response['organizationid'] = OrganizationSerializer(instance.organizationid).data
            
        # Replace 'attendancepolicyid' ID with full Policy object
        if instance.attendancepolicyid:
            response['attendancepolicyid'] = AttendancePolicySerializer(instance.attendancepolicyid).data
            
        if instance.processedby:
            response['processedby'] = UserSerializer(instance.processedby).data
            
        if instance.createdby:
            response['createdby'] = UserSerializer(instance.createdby).data
            
        return response