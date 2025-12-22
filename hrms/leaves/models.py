# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class LeavePeriods(models.Model):
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='created_by', blank=True, null=True)
    organization = models.ForeignKey(
        'organization.Organizations', # Replace with your actual Organizations model name
        models.DO_NOTHING, 
        db_column='organization_id', 
        blank=True, 
        null=True
    )

    class Meta:
        managed = False
        db_table = 'leave_periods'


class LeaveTypes(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10)
    default_days = models.DecimalField(max_digits=5, decimal_places=2)
    is_paid = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='created_by', blank=True, null=True)
    organization = models.ForeignKey(
        'organization.Organizations', # Replace with your actual Organizations model name
        models.DO_NOTHING, 
        db_column='organization_id', 
        blank=True, 
        null=True
    )
    
    class Meta:
        managed = False
        db_table = 'leave_types'


class LeaveBalances(models.Model):
    employee = models.ForeignKey('employee.Employees', models.DO_NOTHING)
    leave_type = models.ForeignKey(LeaveTypes, models.DO_NOTHING, blank=True, null=True)
    leave_period = models.ForeignKey(LeavePeriods, models.DO_NOTHING, blank=True, null=True)
    total_allocated = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    used = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='created_by', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'leave_balances'
        unique_together = (('employee', 'leave_type', 'leave_period'),)


class LeaveRequests(models.Model):
    employee = models.ForeignKey('employee.Employees', models.DO_NOTHING)
    leave_type = models.ForeignKey(LeaveTypes, models.DO_NOTHING, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    day_count = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    manager_comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='created_by', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'leave_requests'
