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
        
class EmployeeFinalSettlement(models.Model):
    offboarding = models.OneToOneField(
        'employee.EmployeeOffboarding',
        models.DO_NOTHING,
        db_column='offboardingid',
        related_name='final_settlement'
    )

    employee = models.ForeignKey(
        'employee.Employees',
        models.DO_NOTHING,
        db_column='employeeid'
    )

    last_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    leave_encashment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # --- CHANGE 1: Is field ko Comment out kar dein ---
    # Kyunki ye DB generated hai, Django ko iske baare mein batane ki zaroorat nahi
    # net_payable = models.DecimalField(
    #     max_digits=12,
    #     decimal_places=2,
    #     editable=False
    # )

    status = models.CharField(
        max_length=30,
        default='DRAFT'
    )

    remarks = models.TextField(blank=True, null=True)

    createdby = models.ForeignKey(
        'users.Users',
        models.DO_NOTHING,
        db_column='createdby',
        related_name='finalsettlement_createdby_set'
    )

    createdat = models.DateTimeField(auto_now_add=True)

    updatedby = models.ForeignKey(
        'users.Users',
        models.DO_NOTHING,
        db_column='updatedby',
        related_name='finalsettlement_updatedby_set',
        blank=True,
        null=True
    )

    updateat = models.DateTimeField(blank=True, null=True)

    isactive = models.BooleanField(default=True)
    isdelete = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'employee_final_settlement'

    def __str__(self):
        return f"Settlement - Employee {self.employee_id}"

    # --- CHANGE 2: Save method ko simple bana dein ---
    # Calculation hata dein, kyunki DB ye khud karega
    def save(self, *args, **kwargs):
        # self.net_payable = ... (YE LINE DELETE KAR DEIN)
        super().save(*args, **kwargs)