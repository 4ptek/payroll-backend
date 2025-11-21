from rest_framework import serializers

class AssignPermissionSerializer(serializers.Serializer):
    role_id = serializers.IntegerField()
    module_id = serializers.IntegerField()
    is_enable = serializers.BooleanField()
    organization_id = serializers.IntegerField(required=True)