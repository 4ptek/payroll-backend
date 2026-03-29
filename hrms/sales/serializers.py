from rest_framework import serializers
from decimal import Decimal
from .models import (
    SalesTeams,
    SalesTeamMembers,
    SalesCommissionStructures,
    SalesCommissionTiers,
    SalesTargets,
    SalesEntries,
    SalesMonthlyReports,
)

def calculate_commission(commission_structure, total_sales):
    if not commission_structure:
        return Decimal('0.00')

    ctype = commission_structure.commissiontype

    if ctype == 'PERCENTAGE':
        rate = commission_structure.commissionvalue or Decimal('0')
        return round((rate / 100) * total_sales, 2)

    elif ctype == 'FIXED':
        return round(commission_structure.commissionvalue or Decimal('0'), 2)

    elif ctype == 'TIERED':
        tiers = commission_structure.salescommissiontiers_set.order_by('minamount')
        for tier in tiers:
            min_a = tier.minamount
            max_a = tier.maxamount  # None means unlimited (last tier)
            if total_sales >= min_a and (max_a is None or total_sales <= max_a):
                if tier.commissionpercentage:
                    return round((tier.commissionpercentage / 100) * total_sales, 2)
                elif tier.commissionfixed:
                    return round(tier.commissionfixed, 2)
        return Decimal('0.00')

    return Decimal('0.00')


# 1. SALES TEAMS
class SalesTeamMemberNestedSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_code = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()

    class Meta:
        model = SalesTeamMembers
        fields = [
            'id',
            'employeeid',
            'employee_name',
            'employee_code',
            'designation',
            'joiningdate',
            'leavingdate',
            'isactive',
        ]

    def get_employee_name(self, obj):
        emp = obj.employeeid
        if emp:
            return f"{emp.firstname or ''} {emp.lastname or ''}".strip()
        return None

    def get_employee_code(self, obj):
        return obj.employeeid.employeecode if obj.employeeid else None

    def get_designation(self, obj):
        if obj.employeeid and obj.employeeid.designationid:
            return obj.employeeid.designationid.title
        return None


class SalesTeamCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesTeams
        fields = [
            'id',
            'name',
            'description',
            'departmentid',
            'teamleaderid',
            'isactive',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        return SalesTeams.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class SalesTeamListSerializer(serializers.ModelSerializer):
    department_name = serializers.SerializerMethodField()
    team_leader_name = serializers.SerializerMethodField()
    total_members = serializers.SerializerMethodField()

    class Meta:
        model = SalesTeams
        fields = [
            'id',
            'name',
            'description',
            'department_name',
            'team_leader_name',
            'total_members',
            'isactive',
            'createdat',
        ]

    def get_department_name(self, obj):
        return obj.departmentid.name if obj.departmentid else None

    def get_team_leader_name(self, obj):
        if obj.teamleaderid:
            emp = obj.teamleaderid
            return f"{emp.firstname or ''} {emp.lastname or ''}".strip()
        return None

    def get_total_members(self, obj):
        return obj.salesteammembers_set.filter(isactive=True, isdelete=False).count()


class SalesTeamDetailSerializer(serializers.ModelSerializer):
    department_name = serializers.SerializerMethodField()
    team_leader_name = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()

    class Meta:
        model = SalesTeams
        fields = [
            'id',
            'name',
            'description',
            'departmentid',
            'department_name',
            'teamleaderid',
            'team_leader_name',
            'isactive',
            'createdat',
            'members',
        ]

    def get_department_name(self, obj):
        return obj.departmentid.name if obj.departmentid else None

    def get_team_leader_name(self, obj):
        if obj.teamleaderid:
            emp = obj.teamleaderid
            return f"{emp.firstname or ''} {emp.lastname or ''}".strip()
        return None

    def get_members(self, obj):
        members = obj.salesteammembers_set.filter(isactive=True, isdelete=False)
        return SalesTeamMemberNestedSerializer(members, many=True).data


# 2. SALES TEAM MEMBERS
class SalesTeamMemberAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesTeamMembers
        fields = [
            'id',
            'employeeid',
            'joiningdate',
        ]
        read_only_fields = ['id']

    def validate_employeeid(self, value):
        team = self.context.get('team')
        if team:
            already_exists = SalesTeamMembers.objects.filter(
                teamid=team,
                employeeid=value,
                isactive=True,
                isdelete=False
            ).exists()
            if already_exists:
                raise serializers.ValidationError(
                    "this employee is already a member of the team."
                )
        return value

    def create(self, validated_data):
        return SalesTeamMembers.objects.create(**validated_data)


class SalesTeamMemberRemoveSerializer(serializers.Serializer):
    employeeid = serializers.IntegerField()


# 3. COMMISSION STRUCTURES
class SalesCommissionTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesCommissionTiers
        fields = [
            'id',
            'minamount',
            'maxamount',
            'commissionpercentage',
            'commissionfixed',
        ]
        read_only_fields = ['id']


class CommissionStructureCreateSerializer(serializers.ModelSerializer):
    tiers = SalesCommissionTierSerializer(
        many=True,
        source='salescommissiontiers_set',
        required=False
    )

    class Meta:
        model = SalesCommissionStructures
        fields = [
            'id',
            'name',
            'applylevel',        
            'teamid',
            'employeeid',
            'commissiontype',    
            'commissionvalue',   
            'tiers',             
            'effectivefrom',
            'effectiveto',
            'isactive',
        ]
        read_only_fields = ['id']

    def validate(self, data):
        applylevel = data.get('applylevel')
        commissiontype = data.get('commissiontype')
        tiers = data.get('salescommissiontiers_set', [])

        # applylevel validation
        if applylevel == 'TEAM' and not data.get('teamid'):
            raise serializers.ValidationError(
                "applylevel 'TEAM' hai to teamid zaroori hai."
            )
        if applylevel == 'INDIVIDUAL' and not data.get('employeeid'):
            raise serializers.ValidationError(
                "applylevel 'INDIVIDUAL' hai to employeeid zaroori hai."
            )

        # commissiontype validation
        if commissiontype in ['PERCENTAGE', 'FIXED']:
            if not data.get('commissionvalue'):
                raise serializers.ValidationError(
                    f"commissiontype '{commissiontype}' ke liye commissionvalue zaroori hai."
                )
        if commissiontype == 'TIERED' and not tiers:
            raise serializers.ValidationError(
                "commissiontype 'TIERED' ke liye kam az kam ek tier zaroori hai."
            )

        return data

    def create(self, validated_data):
        tiers_data = validated_data.pop('salescommissiontiers_set', [])
        structure = SalesCommissionStructures.objects.create(**validated_data)

        for tier in tiers_data:
            SalesCommissionTiers.objects.create(
                commissionstructureid=structure,
                **tier
            )

        return structure


class CommissionStructureListSerializer(serializers.ModelSerializer):
    tiers = SalesCommissionTierSerializer(
        many=True,
        source='salescommissiontiers_set',
        read_only=True
    )
    team_name = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = SalesCommissionStructures
        fields = [
            'id',
            'name',
            'applylevel',
            'teamid',
            'team_name',
            'employeeid',
            'employee_name',
            'commissiontype',
            'commissionvalue',
            'tiers',
            'effectivefrom',
            'effectiveto',
            'isactive',
        ]

    def get_team_name(self, obj):
        return obj.teamid.name if obj.teamid else None

    def get_employee_name(self, obj):
        if obj.employeeid:
            emp = obj.employeeid
            return f"{emp.firstname or ''} {emp.lastname or ''}".strip()
        return None


# 4. SALES TARGETS
class SalesTargetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesTargets
        fields = [
            'id',
            'targetlevel',
            'teamid',
            'employeeid',
            'targetmonth',
            'targetyear',
            'targetamount',
            'description',
            'isactive',
        ]
        read_only_fields = ['id']

    def validate(self, data):
        targetlevel = data.get('targetlevel')

        if targetlevel == 'TEAM' and not data.get('teamid'):
            raise serializers.ValidationError(
                "targetlevel 'TEAM' hai to teamid zaroori hai."
            )
        if targetlevel == 'INDIVIDUAL' and not data.get('employeeid'):
            raise serializers.ValidationError(
                "targetlevel 'INDIVIDUAL' hai to employeeid zaroori hai."
            )

        month = data.get('targetmonth')
        if month and not (1 <= month <= 12):
            raise serializers.ValidationError("targetmonth 1 se 12 ke beech hona chahiye.")

        return data

    def create(self, validated_data):
        return SalesTargets.objects.create(**validated_data)


class SalesTargetListSerializer(serializers.ModelSerializer):
    team_name = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    month_name = serializers.SerializerMethodField()

    class Meta:
        model = SalesTargets
        fields = [
            'id',
            'targetlevel',
            'teamid',
            'team_name',
            'employeeid',
            'employee_name',
            'targetmonth',
            'month_name',
            'targetyear',
            'targetamount',
            'description',
            'isactive',
        ]

    def get_team_name(self, obj):
        return obj.teamid.name if obj.teamid else None

    def get_employee_name(self, obj):
        if obj.employeeid:
            emp = obj.employeeid
            return f"{emp.firstname or ''} {emp.lastname or ''}".strip()
        return None

    def get_month_name(self, obj):
        months = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        return months.get(obj.targetmonth, '')


# 5. SALES ENTRIES (Daily)
class SalesEntryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesEntries
        fields = [
            'id',
            'teamid',
            'saledate',
            'saletype',
            'description',
            'quantity',
            'unitprice',
            'totalamount',
            'remarks',
        ]
        read_only_fields = ['id']

    def validate(self, data):
        quantity = data.get('quantity')
        unitprice = data.get('unitprice')
        totalamount = data.get('totalamount')

        
        if quantity and unitprice:
            expected = round(Decimal(str(quantity)) * unitprice, 2)
            if totalamount and abs(totalamount - expected) > Decimal('0.01'):
                raise serializers.ValidationError(
                    f"totalamount ({totalamount}) quantity x unitprice ({expected}) se match nahi karta."
                )

        return data

    def create(self, validated_data):
        return SalesEntries.objects.create(**validated_data)


class SalesEntryListSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_code = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()

    class Meta:
        model = SalesEntries
        fields = [
            'id',
            'employeeid',
            'employee_name',
            'employee_code',
            'teamid',
            'team_name',
            'saledate',
            'saletype',
            'description',
            'quantity',
            'unitprice',
            'totalamount',
            'remarks',
            'isverified',
            'verifiedat',
            'createdat',
        ]

    def get_employee_name(self, obj):
        emp = obj.employeeid
        if emp:
            return f"{emp.firstname or ''} {emp.lastname or ''}".strip()
        return None

    def get_employee_code(self, obj):
        return obj.employeeid.employeecode if obj.employeeid else None

    def get_team_name(self, obj):
        return obj.teamid.name if obj.teamid else None


class SalesEntryVerifySerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesEntries
        fields = ['isverified']

    def update(self, instance, validated_data):
        instance.isverified = validated_data.get('isverified', instance.isverified)
        instance.save()
        return instance


# 6. SALES MONTHLY REPORT
class SalesReportGenerateSerializer(serializers.Serializer):
    reportmonth = serializers.IntegerField(min_value=1, max_value=12)
    reportyear = serializers.IntegerField(min_value=2000, max_value=2100)
    teamid = serializers.IntegerField(required=False, allow_null=True)
    employeeid = serializers.IntegerField(required=False, allow_null=True)


class SalesMonthlyReportSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_code = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()
    month_name = serializers.SerializerMethodField()
    commission_structure_name = serializers.SerializerMethodField()

    # Calculated display fields
    individual_achievement_pct = serializers.SerializerMethodField()
    team_achievement_pct = serializers.SerializerMethodField()

    class Meta:
        model = SalesMonthlyReports
        fields = [
            'id',
            'employeeid',
            'employee_name',
            'employee_code',
            'teamid',
            'team_name',
            'reportmonth',
            'month_name',
            'reportyear',
            'individualtarget',
            'teamtarget',
            'totalindividualsales',
            'totalteamsales',
            'individual_achievement_pct',
            'team_achievement_pct',
            'basicsalary',
            'commissionearned',
            'totalpayout',
            'commission_structure_name',
            'isgeneratedmanually',
            'generatedat',
        ]

    def get_employee_name(self, obj):
        emp = obj.employeeid
        if emp:
            return f"{emp.firstname or ''} {emp.lastname or ''}".strip()
        return None

    def get_employee_code(self, obj):
        return obj.employeeid.employeecode if obj.employeeid else None

    def get_team_name(self, obj):
        return obj.teamid.name if obj.teamid else None

    def get_month_name(self, obj):
        months = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        return months.get(obj.reportmonth, '')

    def get_commission_structure_name(self, obj):
        return obj.commissionstructureid.name if obj.commissionstructureid else None

    def get_individual_achievement_pct(self, obj):
        if obj.individualtarget and obj.individualtarget > 0:
            return round(
                (obj.totalindividualsales or Decimal('0')) / obj.individualtarget * 100, 2
            )
        return None

    def get_team_achievement_pct(self, obj):
        if obj.teamtarget and obj.teamtarget > 0:
            return round(
                (obj.totalteamsales or Decimal('0')) / obj.teamtarget * 100, 2
            )
        return None