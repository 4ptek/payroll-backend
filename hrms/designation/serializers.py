from rest_framework import serializers
from .models import Designations  # Aapka Designation Model

class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designations
        fields = ['id', 'title', 'organizationid']
        extra_kwargs = {
            'organizationid': {'read_only': True} 
        }