from rest_framework import serializers
from user_rbac.models import Modules

class AssignPermissionSerializer(serializers.Serializer):
    role_id = serializers.IntegerField()
    module_id = serializers.IntegerField()
    is_enable = serializers.BooleanField()
    organization_id = serializers.IntegerField(required=True)
    
    
class ModuleSerializer(serializers.ModelSerializer):
    createdby_name = serializers.ReadOnlyField(source='createdby.name') 
    
    class Meta:
        model = Modules
        fields = '__all__' 