from django.db import models

class Workflows(models.Model):
    organizationid = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='organizationid')
    name = models.TextField()
    description = models.TextField(blank=True, null=True)
    
    createdby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='createdby', related_name='workflows_createdby_set')
    
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='workflows_updatedby_set')
    updateat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='workflows_deletedby_set')
    deleteat = models.DateTimeField(blank=True, null=True)
    moduleid = models.ForeignKey('user_rbac.Modules', models.DO_NOTHING, db_column='moduleid', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'workflows'


class Workflowlevel(models.Model):
    workflowid = models.ForeignKey(Workflows, models.DO_NOTHING, db_column='workflowid')
    flowlevel = models.IntegerField()
    
    approverid = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='approverid', blank=True, null=True, related_name='workflow_approvals')
    
    autoapprove = models.BooleanField(blank=True, null=True)
    timelimit = models.IntegerField(blank=True, null=True)
    isfinallevel = models.BooleanField(blank=True, null=True)
    
    createdby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='createdby', related_name='workflowlevel_createdby_set')
    
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='workflowlevel_updatedby_set')
    updateat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='workflowlevel_deletedby_set')
    deleteat = models.DateTimeField(blank=True, null=True)
    isparallel = models.BooleanField(blank=True, null=True)
    employeeid = models.ForeignKey('employee.Employees', models.DO_NOTHING, db_column='employeeid', related_name='workflowlevel_employeeid_set', blank=True, null=True)
    name = models.CharField(max_length=550, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'workflowlevel'


class Workflowrecords(models.Model):
    workflowid = models.ForeignKey(Workflows, models.DO_NOTHING, db_column='workflowid')
    recordid = models.IntegerField()
    initiatorid = models.ForeignKey('employee.Employees', models.DO_NOTHING, db_column='initiatorid')
    currentlevel = models.IntegerField(blank=True, null=True)
    status = models.TextField()
    remarks = models.TextField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    createdby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='createdby', related_name='workflowrecords_createdby_set')
    
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='workflowrecords_updatedby_set')
    updateat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='workflowrecords_deletedby_set')
    deleteat = models.DateTimeField(blank=True, null=True)
    moduleid = models.ForeignKey('user_rbac.Modules', models.DO_NOTHING, db_column='moduleid', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'workflowrecords'
        
class WorkflowHistory(models.Model):
    workflowrecordid = models.ForeignKey(Workflowrecords, models.DO_NOTHING, db_column='workflowrecordid', related_name='history_logs')
    flowlevel = models.IntegerField()
    actionby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='actionby')
    action = models.CharField(max_length=50) 
    remarks = models.TextField(blank=True, null=True)
    createdat = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False  # Kyunke table SQL se bana rahe hain
        db_table = 'workflowhistory'        
        