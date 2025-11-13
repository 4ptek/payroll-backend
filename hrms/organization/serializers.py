from rest_framework import serializers
from .models import Organizations
    
class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizations
        fields = [
            'id', 'name', 'code', 'email', 'phone', 'address', 'country',
            'currency', 'timezone', 'organizationlogo', 'createdby', 
            'isactive', 'isdelete', 'createdat', 'updatedby', 'updateat', 
            'deletedby', 'deleteat'
        ]
    
    def validate_email(self, value):
        if value and Organizations.objects.filter(email=value, isdelete=False).exists():
            raise serializers.ValidationError("This email is already used.")
        return value

    def validate_code(self, value):
        if Organizations.objects.filter(code=value, isdelete=False).exists():
            raise serializers.ValidationError("This code is already used.")
        return value
    
    def validate_phone(self, value):
        if value and Organizations.objects.filter(phone=value, isdelete=False).exists():
            raise serializers.ValidationError("This phone number is already used.")
        return value