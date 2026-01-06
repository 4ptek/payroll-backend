from rest_framework import serializers
from .models import Workflows, Workflowlevel, Workflowrecords
from django.utils import timezone
from employee.serializers import EmployeeSerializer
from users.models import Users

class WorkflowApproverSerializer(serializers.ModelSerializer):
    employee_details = EmployeeSerializer(source='employeeid', read_only=True)

    class Meta:
        model = Users
        fields = ['id', 'username', 'email', 'employee_details']

class WorkflowLevelSerializer(serializers.ModelSerializer):
    approver_details = WorkflowApproverSerializer(source='approverid', read_only=True)
    id = serializers.IntegerField(required=False)
    class Meta:
        model = Workflowlevel
        fields = [
            'id','flowlevel', 'approverid', 'autoapprove', 'timelimit', 
            'isfinallevel', 'isparallel', 'name', 'description', 'employeeid','approverid','approver_details', 'isactive', 'isdelete'
        ]
        
class WorkflowsGetSerializer(serializers.ModelSerializer):
    levels = WorkflowLevelSerializer(source='workflowlevel_set', many=True, read_only=True)
    
    class Meta:
        model = Workflows
        fields = [
            'id', 'organizationid', 'name', 'description', 'moduleid', 
            'isactive', 'createdat', 'levels'
        ]

class WorkflowsSerializer(serializers.ModelSerializer):
    levels = WorkflowLevelSerializer(many=True, write_only=True)

    class Meta:
        model = Workflows
        fields = [
            'id', 'organizationid', 'name', 'description', 'moduleid', 
            'isactive', 'levels'
        ]

    def validate(self, data):
        organization = data.get('organizationid')
        module = data.get('moduleid')

        if organization and module:
            qs = Workflows.objects.filter(
                organizationid=organization, 
                moduleid=module, 
                isdelete=False
            )

            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError({
                    "moduleid": "A workflow already exists for this Module in this Organization."
                })

        return data

    def create(self, validated_data):
        levels_data = validated_data.pop('levels')
        
        workflow = Workflows.objects.create(**validated_data)

        request = self.context.get('request')
        user = request.user if request else None
        
        for level_data in levels_data:
            Workflowlevel.objects.create(
                workflowid=workflow,
                createdby=user,
                updatedby=user,
                deletedby=user,
                createdat=timezone.now(),
                isactive=True,
                isdelete=False,
                **level_data
            )

        return workflow
    
    def update(self, instance, validated_data):
        levels_data = validated_data.pop('levels', [])

        # 1. Handle Workflow
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.moduleid = validated_data.get('moduleid', instance.moduleid)
        instance.isactive = validated_data.get('isactive', instance.isactive)
        
        request = self.context.get('request')
        user = request.user if request else None
        
        instance.updatedby = user
        instance.updateat = timezone.now()
        instance.save()

        # 2. Handle Levels
        for level_data in levels_data:
            level_id = level_data.get('id')

            if level_id:
                # --- CASE: DELETE 
                if len(level_data) == 1:
                    Workflowlevel.objects.filter(id=level_id, workflowid=instance).update(
                        isdelete=True,
                        isactive=False,
                        deletedby=user,
                        deleteat=timezone.now()
                    )
                
                # --- CASE: UPDATE 
                else:
                    try:
                        level_instance = Workflowlevel.objects.get(id=level_id, workflowid=instance)
                        
                        level_instance.flowlevel = level_data.get('flowlevel', level_instance.flowlevel)
                        level_instance.approverid = level_data.get('approverid', level_instance.approverid)
                        level_instance.employeeid = level_data.get('employeeid', level_instance.employeeid)
                        level_instance.autoapprove = level_data.get('autoapprove', level_instance.autoapprove)
                        level_instance.timelimit = level_data.get('timelimit', level_instance.timelimit)
                        level_instance.isfinallevel = level_data.get('isfinallevel', level_instance.isfinallevel)
                        level_instance.isparallel = level_data.get('isparallel', level_instance.isparallel)
                        level_instance.name = level_data.get('name', level_instance.name)
                        level_instance.description = level_data.get('description', level_instance.description)
                        
                        level_instance.updatedby = user
                        level_instance.updateat = timezone.now()
                        level_instance.save()
                        
                    except Workflowlevel.DoesNotExist:
                        pass 

            # --- CASE: CREATE
            else:
                Workflowlevel.objects.create(
                    workflowid=instance,
                    createdby=user,
                    updatedby=user,
                    deletedby=user,
                    createdat=timezone.now(),
                    isactive=True,
                    isdelete=False,
                    **level_data
                )

        return instance
    
class WorkflowActionSerializer(serializers.Serializer):
    record_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=['Approved', 'Rejected'])
    remarks = serializers.CharField(required=False, allow_blank=True)