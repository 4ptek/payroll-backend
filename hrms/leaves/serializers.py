from rest_framework import serializers
from .models import LeavePeriods, LeaveTypes
from .models import LeaveBalances, LeaveRequests
from rest_framework import pagination

class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class LeaveBalanceSerializer(serializers.ModelSerializer):
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    leave_period_name = serializers.CharField(source='leave_period.name', read_only=True)

    class Meta:
        model = LeaveBalances
        fields = '__all__'

class LeaveRequestSerializer(serializers.ModelSerializer):
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    employee_name = serializers.CharField(source='employee.fullname', read_only=True)

    class Meta:
        model = LeaveRequests
        fields = '__all__'
        read_only_fields = ['status', 'created_by', 'created_at']

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