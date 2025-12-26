# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Attendancepolicies(models.Model):
    organizationid = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='organizationid')
    name = models.TextField()
    description = models.TextField(blank=True, null=True)
    shiftstart = models.TimeField()
    shiftend = models.TimeField()
    graceperiodmins = models.IntegerField()
    halfdayaftermins = models.IntegerField()
    workinghoursperday = models.DecimalField(max_digits=5, decimal_places=2)
    overtimeafterhours = models.DecimalField(max_digits=5, decimal_places=2)
    maxovertimeperday = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    weeklyoff = models.JSONField(blank=True, null=True)
    leavedeductionafterlates = models.IntegerField(blank=True, null=True)
    attendancesource = models.TextField(blank=True, null=True)
    effectivefrom = models.DateField()
    effectiveto = models.DateField(blank=True, null=True)
    createdby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='createdby')
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='attendancepolicies_updatedby_set')
    updateat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='attendancepolicies_deletedby_set')
    deleteat = models.DateTimeField(blank=True, null=True)
    extras = models.JSONField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'attendancepolicies'


class Attendancedetail(models.Model):
    attendanceid = models.ForeignKey('Attendance', models.DO_NOTHING, db_column='attendanceid', blank=True, null=True)
    employeeid = models.ForeignKey('employee.Employees', models.DO_NOTHING, db_column='employeeid', blank=True, null=True)
    attendancedate = models.DateField()
    checkin = models.DateTimeField(blank=True, null=True)
    checkout = models.DateTimeField(blank=True, null=True)
    totalhours = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    createdby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='createdby', blank=True, null=True)
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='attendancedetail_updatedby_set', blank=True, null=True)
    updateat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='attendancedetail_deletedby_set', blank=True, null=True)
    deleteat = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'attendancedetail'


class Attendance(models.Model):
    organizationid = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='organizationid', blank=True, null=True)
    startdate = models.DateField()
    enddate = models.DateField()
    description = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    processedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='processedby', blank=True, null=True)
    processedat = models.DateTimeField(blank=True, null=True)
    createdby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='createdby', related_name='attendance_createdby_set', blank=True, null=True)
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='attendance_updatedby_set', blank=True, null=True)
    updateat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='attendance_deletedby_set', blank=True, null=True)
    deleteat = models.DateTimeField(blank=True, null=True)
    attendancepolicyid = models.ForeignKey(Attendancepolicies, models.DO_NOTHING, db_column='attendancepolicyid', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'attendance'
