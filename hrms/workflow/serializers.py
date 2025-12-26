from rest_framework import serializers
from .models import Workflows, Workflowlevel, Workflowrecords
from django.utils import timezone


class WorkflowLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflowlevel
        fields = [
            'flowlevel', 'approverid', 'autoapprove', 'timelimit', 
            'isfinallevel', 'isparallel', 'name', 'description', 'employeeid'
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
    
class WorkflowActionSerializer(serializers.Serializer):
    record_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=['Approved', 'Rejected'])
    remarks = serializers.CharField(required=False, allow_blank=True)