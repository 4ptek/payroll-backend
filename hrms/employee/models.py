from django.db import models
from django.utils import timezone

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
    organizationroleid = models.ForeignKey('organization.Organizationroles', models.DO_NOTHING, db_column='organizationroleid', blank=True, null=True)
    employeetype = models.TextField(blank=True, null=True)
    bankaccountnumber = models.TextField(blank=True, null=True)
    picture = models.TextField(blank=True, null=True)
    isuser = models.BooleanField(blank=True, null=True)
    isnew = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'employees'
        
        
class EmployeeOffboarding(models.Model):
    employee = models.ForeignKey(
        'Employees',
        models.DO_NOTHING,
        db_column='employee_id'
    )

    offboarding_type = models.CharField(max_length=50)
    last_working_day = models.DateField()
    reason = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=30,
        default='PENDING'
    )
    # PENDING | IN_PROGRESS | COMPLETED | REJECTED

    requested_by = models.ForeignKey(
        'users.Users',
        models.DO_NOTHING,
        db_column='requested_by',
        related_name='offboarding_requested_by'
    )

    requested_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'employee_offboarding'