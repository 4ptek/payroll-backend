from django.db import models


class Payroll(models.Model):
    organizationid = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='organizationid', blank=True, null=True)
    periodstart = models.DateField()
    periodend = models.DateField()
    status = models.TextField(blank=True, null=True)
    processedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='processedby', blank=True, null=True)
    processedat = models.DateTimeField(blank=True, null=True)
    createdby = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='createdby', related_name='payroll_createdby_set', blank=True, null=True)
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='payroll_updatedby_set', blank=True, null=True)
    updateat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='payroll_deletedby_set', blank=True, null=True)
    deleteat = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'payroll'


class PayrollDetails(models.Model):
    payroll = models.ForeignKey(Payroll, models.DO_NOTHING)
    employee = models.ForeignKey('employee.Employees', models.DO_NOTHING)
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_working_days = models.IntegerField(blank=True, null=True)
    present_days = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    absent_days = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    late_days = models.IntegerField(blank=True, null=True)
    penalty_days = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    payable_days = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_allowances = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'payroll_details'
