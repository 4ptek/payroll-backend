from rest_framework import serializers
from .models import LeavePeriods, LeaveTypes

class LeavePeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeavePeriods
        fields = '__all__'
        read_only_fields = ['created_at', 'created_by', 'organization']

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveTypes
        fields = '__all__'
        read_only_fields = ['created_at', 'created_by', 'organization']