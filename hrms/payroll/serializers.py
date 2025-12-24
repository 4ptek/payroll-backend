from rest_framework import serializers
from django.db import transaction
from decimal import Decimal
from datetime import date # Sirf type checking k liye
from .models import Payroll, PayrollDetails
from salary_structure.models import SalaryStructure
from employee.models import Employees
from attendance.models import Attendancedetail, Attendance
from django.db.models import Sum

class PayrollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payroll
        fields = ['id', 'organizationid', 'periodstart', 'periodend', 'status', 'createdat']
        read_only_fields = ['organizationid', 'status', 'createdat']

    def validate(self, data):        
        if data['periodstart'] > data['periodend']:
            raise serializers.ValidationError("End date must be after start date.")
        return data

    def create(self, validated_data):
        with transaction.atomic():
            
            # 1. Create Parent Payroll Record
            payroll_instance = Payroll.objects.create(**validated_data)
            start_date = validated_data['periodstart']
            end_date = validated_data['periodend']
            
            total_days_in_month = (end_date - start_date).days + 1
            org_id = validated_data['organizationid'].id

            # 2. Employees Fetch
            employees = Employees.objects.filter(
                organizationid=org_id, 
                isactive=True, 
                isdelete=False
            ).select_related('salary_structure').prefetch_related('salary_structure__salarycomponents_set')
        
            # 3. Attendance Fetch    
            attendance_batches = Attendance.objects.filter(
                organizationid=org_id,
                startdate=start_date, 
                enddate=end_date, 
                isactive=True,
                isdelete=False
            ).values_list('id', flat=True)
            print(f"Found Attendance Batch IDs: {list(attendance_batches)}")

            payroll_details_list = []

            for emp in employees:
                # --- Step A: Structure ---
                structure = emp.salary_structure
                if not structure:
                    structure = SalaryStructure.objects.filter(
                        base_salary=emp.basicsalary, 
                        is_active=True
                    ).first()
                
                if not structure:
                    continue 

                # --- Step B: Components ---
                base_salary = Decimal(structure.base_salary)
                total_allowances = Decimal(0)
                other_deductions = Decimal(0)

                for comp in structure.salarycomponents_set.all():
                    if comp.amount_type == 'percentage':
                        amount = (comp.value / 100) * base_salary
                    else:
                        amount = comp.value
                    
                    if comp.type == 'earning':
                        total_allowances += amount
                    elif comp.type == 'deduction':
                        other_deductions += amount

                gross_salary = base_salary + total_allowances

                # --- Step C: Attendance ---
                if attendance_batches:
                    attendance_qs = Attendancedetail.objects.filter(
                        employeeid=emp.id,
                        attendanceid__in=attendance_batches 
                    )
                else:
                    attendance_qs = Attendancedetail.objects.filter(
                        employeeid=emp.id,
                        attendancedate__range=[start_date, end_date]
                    )
                late_count = attendance_qs.filter(status__iexact='Late').count()
                absent_count = attendance_qs.filter(status__iexact='Absent').count()
                present_count = attendance_qs.filter(status__iexact='Present').count()
                
                penalty_absents = late_count // 3
                total_deductible_days = absent_count + penalty_absents
                payable_days = total_days_in_month - total_deductible_days

                # --- Step D: Net Salary ---
                per_day_salary = gross_salary / Decimal(total_days_in_month)
                absent_deduction_amount = per_day_salary * Decimal(total_deductible_days)
                total_final_deductions = other_deductions + absent_deduction_amount
                net_salary = gross_salary - total_final_deductions

                # --- Step E: Prepare Object ---
                payroll_details_list.append(PayrollDetails(
                    payroll=payroll_instance,
                    employee=emp,
                    basic_salary=base_salary,
                    total_working_days=total_days_in_month,
                    present_days=present_count, 
                    absent_days=absent_count,
                    late_days=late_count,
                    penalty_days=total_deductible_days,
                    payable_days=payable_days,
                    gross_salary=round(gross_salary, 2),
                    total_allowances=round(total_allowances, 2),
                    total_deductions=round(total_final_deductions, 2),
                    net_salary=round(net_salary, 2),
                    created_at=date.today()
                ))

            # Bulk Save
            PayrollDetails.objects.bulk_create(payroll_details_list)

            return payroll_instance
        
class PayrollRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_code = serializers.CharField(source='employee.employeecode')
    department = serializers.CharField(source='employee.departmentid.name', default='-')
    designation = serializers.CharField(source='employee.designationid.title', default='-')

    class Meta:
        model = PayrollDetails
        fields = [
            'id', 
            'employee_name', 'employee_code', 'department', 'designation',
            'basic_salary', 'total_allowances', 
            'gross_salary', 'total_deductions', 'net_salary',
            'payable_days', 'absent_days'
        ]

    def get_employee_name(self, obj):
        return f"{obj.employee.firstname} {obj.employee.lastname or ''}".strip()

class PayrollRetrieveSerializer(serializers.ModelSerializer):
    total_employees = serializers.SerializerMethodField()
    total_gross = serializers.SerializerMethodField()
    total_deductions = serializers.SerializerMethodField()
    total_net = serializers.SerializerMethodField()
    
    # Table Data
    records = serializers.SerializerMethodField()

    class Meta:
        model = Payroll
        fields = [
            'id', 'periodstart', 'periodend', 'status',
            'total_employees', 'total_gross', 'total_deductions', 'total_net',
            'records'
        ]

    def get_stats(self, obj):
        if not hasattr(self, '_stats'):
            self._stats = obj.details.aggregate(
                count=Sum('id'),
                gross=Sum('gross_salary'),
                deductions=Sum('total_deductions'),
                net=Sum('net_salary')
            )
        return self._stats

    def get_total_employees(self, obj):
        return obj.payrolldetails_set.count()

    def get_total_gross(self, obj):
        return obj.payrolldetails_set.aggregate(val=Sum('gross_salary'))['val'] or 0

    def get_total_deductions(self, obj):
        return obj.payrolldetails_set.aggregate(val=Sum('total_deductions'))['val'] or 0

    def get_total_net(self, obj):
        return obj.payrolldetails_set.aggregate(val=Sum('net_salary'))['val'] or 0

    def get_records(self, obj):
        details = obj.payrolldetails_set.select_related(
            'employee', 
            'employee__departmentid', 
            'employee__designationid'
        ).all()
        
        return PayrollRecordSerializer(details, many=True).data