# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models



class Modules(models.Model):
    modulename = models.CharField(max_length=550, blank=True, null=True)
    createdby = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='createdby', blank=True, null=True)
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', blank=True, null=True)
    updateat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='modules_deletedby_set', blank=True, null=True)
    deleteat = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'modules'

class Relationmodule(models.Model):
    parentmoduleid = models.ForeignKey('user_rbac.Modules', models.DO_NOTHING, db_column='parentmoduleid', blank=True, null=True)
    childmoduleid = models.ForeignKey('user_rbac.Modules', models.DO_NOTHING, db_column='childmoduleid', related_name='relationmodule_childmoduleid_set', blank=True, null=True)
    createdby = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='createdby', blank=True, null=True)
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', blank=True, null=True)
    updateat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='relationmodule_deletedby_set', blank=True, null=True)
    deleteat = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'relationmodule'

class Rolespermission(models.Model):
    relationid = models.ForeignKey('user_rbac.Relationmodule', models.DO_NOTHING, db_column='relationid', blank=True, null=True)
    roleid = models.ForeignKey('users.Userroles', models.DO_NOTHING, db_column='roleid', blank=True, null=True)
    createdby = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='createdby', blank=True, null=True)
    isenable = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', blank=True, null=True)
    updateat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='rolespermission_deletedby_set', blank=True, null=True)
    deleteat = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rolespermission'
