# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class SalaryStructure(models.Model):
    org = models.ForeignKey('organization.Organizations', models.DO_NOTHING, blank=True, null=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'salary_structure'


class SalaryComponents(models.Model):
    org = models.ForeignKey('organization.Organizations', models.DO_NOTHING)
    salary_struc = models.ForeignKey(SalaryStructure, models.DO_NOTHING)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20)
    amount_type = models.CharField(max_length=20)
    value = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'salary_components'
