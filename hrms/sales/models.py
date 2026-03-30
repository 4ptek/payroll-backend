from django.db import models


class SalesTeams(models.Model):
    id = models.IntegerField(primary_key=True)
    organizationid = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='organizationid')
    departmentid = models.ForeignKey('department.Departments', models.DO_NOTHING, db_column='departmentid', blank=True, null=True)
    name = models.TextField()
    description = models.TextField(blank=True, null=True)
    teamleaderid = models.ForeignKey('employee.Employees', models.DO_NOTHING, db_column='teamleaderid', blank=True, null=True)
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    createdby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='createdby', blank=True, null=True)
    updateat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='salesteams_updatedby_set', blank=True, null=True)
    deleteat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='salesteams_deletedby_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sales_teams'


class SalesTeamMembers(models.Model):
    id = models.IntegerField(primary_key=True)
    organizationid = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='organizationid')
    teamid = models.ForeignKey(SalesTeams, models.DO_NOTHING, db_column='teamid')
    employeeid = models.ForeignKey('employee.Employees', models.DO_NOTHING, db_column='employeeid')
    joiningdate = models.DateField(blank=True, null=True)
    leavingdate = models.DateField(blank=True, null=True)
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    createdby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='createdby', blank=True, null=True)
    updateat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='salesteammembers_updatedby_set', blank=True, null=True)
    deleteat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='salesteammembers_deletedby_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sales_team_members'
        unique_together = (('employeeid', 'teamid'),)


class SalesCommissionStructures(models.Model):
    id = models.IntegerField(primary_key=True)
    organizationid = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='organizationid')
    name = models.TextField()
    applylevel = models.TextField()                 # 'TEAM' or 'INDIVIDUAL'
    teamid = models.ForeignKey(SalesTeams, models.DO_NOTHING, db_column='teamid', blank=True, null=True)
    employeeid = models.ForeignKey('employee.Employees', models.DO_NOTHING, db_column='employeeid', blank=True, null=True)
    commissiontype = models.TextField()             # 'PERCENTAGE', 'FIXED', 'TIERED'
    commissionvalue = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    effectivefrom = models.DateField()
    effectiveto = models.DateField(blank=True, null=True)
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    createdby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='createdby', blank=True, null=True)
    updateat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='salescommissionstructures_updatedby_set', blank=True, null=True)
    deleteat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='salescommissionstructures_deletedby_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sales_commission_structures'


class SalesCommissionTiers(models.Model):
    id = models.IntegerField(primary_key=True)
    commissionstructureid = models.ForeignKey(SalesCommissionStructures, models.DO_NOTHING, db_column='commissionstructureid')
    minamount = models.DecimalField(max_digits=15, decimal_places=2)
    maxamount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    commissionpercentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    commissionfixed = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sales_commission_tiers'


class SalesTargets(models.Model):
    id = models.IntegerField(primary_key=True)
    organizationid = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='organizationid')
    targetlevel = models.TextField()               # 'TEAM' or 'INDIVIDUAL'
    teamid = models.ForeignKey(SalesTeams, models.DO_NOTHING, db_column='teamid', blank=True, null=True)
    employeeid = models.ForeignKey('employee.Employees', models.DO_NOTHING, db_column='employeeid', blank=True, null=True)
    targetmonth = models.IntegerField()
    targetyear = models.IntegerField()
    targetamount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    createdby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='createdby', blank=True, null=True)
    updateat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='salestargets_updatedby_set', blank=True, null=True)
    deleteat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='salestargets_deletedby_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sales_targets'
        unique_together = (('teamid', 'targetmonth', 'targetyear'), ('employeeid', 'targetmonth', 'targetyear'),)


class SalesEntries(models.Model):
    id = models.IntegerField(primary_key=True)
    organizationid = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='organizationid')
    employeeid = models.ForeignKey('employee.Employees', models.DO_NOTHING, db_column='employeeid')
    teamid = models.ForeignKey(SalesTeams, models.DO_NOTHING, db_column='teamid', blank=True, null=True)
    saledate = models.DateField()
    saletype = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    unitprice = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    totalamount = models.DecimalField(max_digits=15, decimal_places=2)
    remarks = models.TextField(blank=True, null=True)
    isverified = models.BooleanField(blank=True, null=True)
    verifiedby = models.ForeignKey('employee.Employees', models.DO_NOTHING, db_column='verifiedby', related_name='salesentries_verifiedby_set', blank=True, null=True)
    verifiedat = models.DateTimeField(blank=True, null=True)
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    createdby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='createdby', blank=True, null=True)
    updateat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='salesentries_updatedby_set', blank=True, null=True)
    deleteat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='salesentries_deletedby_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sales_entries'


class SalesMonthlyReports(models.Model):
    id = models.IntegerField(primary_key=True)
    organizationid = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='organizationid')
    employeeid = models.ForeignKey('employee.Employees', models.DO_NOTHING, db_column='employeeid')
    teamid = models.ForeignKey(SalesTeams, models.DO_NOTHING, db_column='teamid', blank=True, null=True)
    reportmonth = models.IntegerField()
    reportyear = models.IntegerField()
    individualtarget = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    teamtarget = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    totalindividualsales = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    totalteamsales = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    achievementpercentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    basicsalary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    commissionearned = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    totalpayout = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    commissionstructureid = models.ForeignKey(SalesCommissionStructures, models.DO_NOTHING, db_column='commissionstructureid', blank=True, null=True)
    isgeneratedmanually = models.BooleanField(blank=True, null=True)
    generatedat = models.DateTimeField(blank=True, null=True)
    generatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='generatedby', blank=True, null=True)
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    createdby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='createdby', related_name='salesmonthlyreports_createdby_set', blank=True, null=True)
    updateat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='salesmonthlyreports_updatedby_set', blank=True, null=True)
    deleteat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='salesmonthlyreports_deletedby_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sales_monthly_reports'
        unique_together = (('employeeid', 'reportmonth', 'reportyear'),)