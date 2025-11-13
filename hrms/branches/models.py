# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Branches(models.Model):
    organizationid = models.ForeignKey('organization.Organizations', models.DO_NOTHING, db_column='organizationid')
    name = models.TextField()
    address = models.TextField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    createdby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='createdby', blank=True, null=True)
    isactive = models.BooleanField(blank=True, null=True)
    isdelete = models.BooleanField(blank=True, null=True)
    createdat = models.DateTimeField(blank=True, null=True)
    updatedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='updatedby', related_name='branches_updatedby_set', blank=True, null=True)
    updateat = models.DateTimeField(blank=True, null=True)
    deletedby = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='deletedby', related_name='branches_deletedby_set', blank=True, null=True)
    deleteat = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'branches'
