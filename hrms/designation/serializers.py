from rest_framework import serializers
from .models import Designations  # Aapka Designation Model

class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designations
        fields = ['id', 'title', 'organizationid']
        extra_kwargs = {
            'organizationid': {'read_only': True} 
        }
        
class DesignationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designations
        fields = '__all__'
        read_only_fields = (
            'createdby', 'createdat', 'updatedby', 
            'updateat', 'deletedby', 'deleteat', 'isdelete'
        )

class DesignationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designations
        fields = ['title', 'grade', 'isactive'] 