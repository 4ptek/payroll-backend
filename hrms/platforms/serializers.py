from rest_framework import serializers
from .models import Platforms, EmployeeEmails, EmployeePlatformAccounts


class PlatformCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platforms
        fields = ['id', 'name', 'description', 'icon', 'isactive']
        read_only_fields = ['id']

    def create(self, validated_data):
        return Platforms.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PlatformListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platforms
        fields = ['id', 'name', 'description', 'icon', 'isactive', 'createdat']



class EmployeeEmailCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeEmails
        fields = ['id', 'employeeid', 'email', 'isprimary', 'isactive']
        read_only_fields = ['id']

    def validate(self, data):
        if data.get('isprimary'):
            org = self.context.get('org')
            employee = data.get('employeeid')
            already_primary = EmployeeEmails.objects.filter(
                employeeid=employee,
                isprimary=True,
                isactive=True,
                isdelete=False
            )
            if self.instance:
                already_primary = already_primary.exclude(id=self.instance.id)
            if already_primary.exists():
                raise serializers.ValidationError(
                    "Is employee ki already ek primary email set hai."
                )
        return data

    def create(self, validated_data):
        return EmployeeEmails.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class EmployeeEmailListSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    platform_count = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeEmails
        fields = [
            'id',
            'employeeid',
            'employee_name',
            'email',
            'isprimary',
            'isactive',
            'platform_count',
            'createdat',
        ]

    def get_employee_name(self, obj):
        emp = obj.employeeid
        if emp:
            return f"{emp.firstname or ''} {emp.lastname or ''}".strip()
        return None

    def get_platform_count(self, obj):
        # Kitne platforms pe ye email assign hai
        return obj.employeeplatformaccounts_set.filter(
            isactive=True, isdelete=False
        ).count()



class PlatformAccountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeePlatformAccounts
        fields = [
            'id',
            'employeeid',
            'platformid',
            'employeeemailid',
            'username',
            'notes',
            'isactive',
        ]
        read_only_fields = ['id']

    def validate(self, data):
        # Email employeeid se belong karti ho
        email_obj = data.get('employeeemailid')
        employee = data.get('employeeid')

        if email_obj and employee:
            if email_obj.employeeid_id != employee.id:
                raise serializers.ValidationError(
                    "Ye email is employee ki nahi hai."
                )

        return data

    def create(self, validated_data):
        return EmployeePlatformAccounts.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PlatformAccountListSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_code = serializers.SerializerMethodField()
    platform_name = serializers.SerializerMethodField()
    platform_icon = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = EmployeePlatformAccounts
        fields = [
            'id',
            'employeeid',
            'employee_name',
            'employee_code',
            'platformid',
            'platform_name',
            'platform_icon',
            'employeeemailid',
            'email',
            'username',
            'notes',
            'isactive',
            'createdat',
        ]

    def get_employee_name(self, obj):
        emp = obj.employeeid
        if emp:
            return f"{emp.firstname or ''} {emp.lastname or ''}".strip()
        return None

    def get_employee_code(self, obj):
        return obj.employeeid.employeecode if obj.employeeid else None

    def get_platform_name(self, obj):
        return obj.platformid.name if obj.platformid else None

    def get_platform_icon(self, obj):
        return obj.platformid.icon if obj.platformid else None

    def get_email(self, obj):
        return obj.employeeemailid.email if obj.employeeemailid else None


class EmployeeFullProfileSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    employee_name = serializers.CharField()
    employee_code = serializers.CharField()
    accounts = serializers.SerializerMethodField()

    def get_accounts(self, obj):
        return obj.get('accounts', [])