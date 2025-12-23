from rest_framework import serializers
from decimal import Decimal
from .models import SalaryStructure, SalaryComponents

class SalaryComponentSerializer(serializers.ModelSerializer):
    calculated_amount = serializers.SerializerMethodField()
    class Meta:
        model = SalaryComponents
        fields = ['name', 'type', 'amount_type', 'value', 'calculated_amount']
        
    def get_calculated_amount(self, obj):
        base_salary = obj.salary_struc.base_salary
        
        if obj.amount_type == 'percentage':
            return round((obj.value / 100) * base_salary, 2)
        else:
            return obj.value

class SalaryStructureSerializer(serializers.ModelSerializer):
    components = SalaryComponentSerializer(many=True,source='salarycomponents_set',required=False)
    
    gross_salary = serializers.SerializerMethodField()
    total_deductions = serializers.SerializerMethodField()
    net_salary = serializers.SerializerMethodField()

    class Meta:
        model = SalaryStructure
        fields = ['id', 'title', 'base_salary', 'is_active', 'gross_salary', 'total_deductions', 'net_salary', 'components']
    
    def calculate_values(self, obj):
        base = obj.base_salary or Decimal(0)
        total_earnings = Decimal(0)
        total_deductions = Decimal(0)

        for component in obj.salarycomponents_set.all():
            
            if component.amount_type == 'percentage':
                amount = (component.value / 100) * base
            else:
                amount = component.value
            
            if component.type == 'earning':
                total_earnings += amount
            elif component.type == 'deduction':
                total_deductions += amount

        gross = base + total_earnings
        net = gross - total_deductions
        
        return {
            "gross": round(gross, 2),
            "deductions": round(total_deductions, 2),
            "net": round(net, 2)
        }

    def get_gross_salary(self, obj):
        return self.calculate_values(obj)["gross"]

    def get_total_deductions(self, obj):
        return self.calculate_values(obj)["deductions"]

    def get_net_salary(self, obj):
        return self.calculate_values(obj)["net"]

    def create(self, validated_data):
        components_data = validated_data.pop('salarycomponents_set', []) 
        structure = SalaryStructure.objects.create(**validated_data)

        for component_data in components_data:
            SalaryComponents.objects.create(
                salary_struc=structure,
                org=structure.org,
                **component_data
            )
            
        return structure