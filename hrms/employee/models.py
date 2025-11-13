# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Employees(models.Model):
    organizationid = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='organizationid')
    employeecode = models.TextField(unique=True, blank=True, null=True)
    firstname = models.TextField()
    lastname = models.TextField(blank=True, null=True)
    gender = models.TextField(blank=True, null=True)
    cnic = models.TextField(blank=True, null=True)
    dateofbirth = models.DateField(blank=True, null=True)
    dateofappointment = models.DateField(blank=True, null=True)
    branchid = models.ForeignKey('branches.Branches', models.DO_NOTHING, db_column='branchid', blank=True, null=True)
    departmentid = models.ForeignKey('department.Departments', models.DO_NOTHING, db_column='departmentid', blank=True, null=True)
    designationid = models.ForeignKey('designation.Designations', models.DO_NOTHING, db_column='designationid', blank=True, null=True)
    basicsalary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    createdby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='createdby', blank=True, null=True)
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='employees_updatedby_set', blank=True, null=True)
    updateat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='employees_deletedby_set', blank=True, null=True)
    deleteat = models.DateTimeField(blank=True, null=True)
    attendancemachineid = models.CharField(max_length=550, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'employees'
