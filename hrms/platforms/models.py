from django.db import models


class Platforms(models.Model):
    id = models.IntegerField(primary_key=True)
    organizationid = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='organizationid')
    name = models.TextField()
    description = models.TextField(blank=True, null=True)
    icon = models.TextField(blank=True, null=True)
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    createdby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='createdby', blank=True, null=True)
    updateat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='platforms_updatedby_set', blank=True, null=True)
    deleteat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='platforms_deletedby_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'platforms'


class EmployeeEmails(models.Model):
    id = models.IntegerField(primary_key=True)
    organizationid = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='organizationid')
    employeeid = models.ForeignKey('employee.Employees', models.DO_NOTHING, db_column='employeeid')
    email = models.TextField()
    isprimary = models.BooleanField(blank=True, null=True)
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    createdby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='createdby', blank=True, null=True)
    updateat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='employeeemails_updatedby_set', blank=True, null=True)
    deleteat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='employeeemails_deletedby_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'employee_emails'
        unique_together = (('employeeid', 'email'),)


class EmployeePlatformAccounts(models.Model):
    id = models.IntegerField(primary_key=True)
    organizationid = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='organizationid')
    employeeid = models.ForeignKey('employee.Employees', models.DO_NOTHING, db_column='employeeid')
    platformid = models.ForeignKey(Platforms, models.DO_NOTHING, db_column='platformid')
    employeeemailid = models.ForeignKey(EmployeeEmails, models.DO_NOTHING, db_column='employeeemailid')
    username = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    createdby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='createdby', blank=True, null=True)
    updateat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='employeeplatformaccounts_updatedby_set', blank=True, null=True)
    deleteat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='employeeplatformaccounts_deletedby_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'employee_platform_accounts'
        unique_together = (('employeeid', 'platformid', 'employeeemailid'),)