from rest_framework import serializers
from .models import Attendancepolicies, Attendance
from organization.models import Organizations
from users.models import Users

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['id', 'username', 'email'] # Customize these fields as needed
        
class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizations
        fields = ['id', 'name', 'code'] # Add whatever fields you want to show

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