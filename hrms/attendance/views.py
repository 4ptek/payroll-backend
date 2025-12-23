from django.shortcuts import render
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from .models import Attendancepolicies, Attendance, Attendancedetail
from .serializers import AttendancePolicySerializer, AttendanceSerializer, AttendanceDetailSerializer, FileUploadSerializer, AttendanceDetailReportSerializer
from rest_framework.views import APIView
from Helpers.ResponseHandler import custom_response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.parsers import MultiPartParser, FormParser
import pandas as pd
from .utils import calculate_attendance_status, custom_response_upload
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Count, Sum, Q, F
from employee.models import Employees 
from datetime import datetime, time, date
from rest_framework.views import APIView
from rest_framework import status
from leaves.models import LeaveRequests
from datetime import timedelta

class AttendancePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100 

class AttendancePolicyListCreateView(generics.ListCreateAPIView):
    serializer_class = AttendancePolicySerializer
    pagination_class = AttendancePagination

    def get_queryset(self):
        """
        Filters policies by organizationid, shift times, source, and active status.
        """
        queryset = Attendancepolicies.objects.all()
        
        org_id = self.request.query_params.get('organizationid')
        if org_id is not None:
            queryset = queryset.filter(organizationid=org_id)

        # --- New Filters ---
        
        # 1. Filter by Shift Start (e.g., ?shiftstart=09:00:00)
        shift_start = self.request.query_params.get('shiftstart')
        if shift_start is not None:
            queryset = queryset.filter(shiftstart=shift_start)

        # 2. Filter by Shift End (e.g., ?shiftend=18:00:00)
        shift_end = self.request.query_params.get('shiftend')
        if shift_end is not None:
            queryset = queryset.filter(shiftend=shift_end)

        # 3. Filter by Attendance Source (e.g., ?attendancesource=Biometric)
        attendance_source = self.request.query_params.get('attendancesource')
        if attendance_source is not None:
            queryset = queryset.filter(attendancesource__icontains=attendance_source)

        # 4. Filter by Is Active (e.g., ?isactive=true)
        is_active = self.request.query_params.get('isactive')
        if is_active is not None:
            # Convert string 'true'/'false' from URL to Python Boolean
            if is_active.lower() == 'true':
                queryset = queryset.filter(isactive=True)
            elif is_active.lower() == 'false':
                queryset = queryset.filter(isactive=False)
            
        return queryset.order_by('-id') # Best practice: order by ID for consistent pagination
    
class AttendanceListCreateView(generics.ListCreateAPIView):
    serializer_class = AttendanceSerializer
    pagination_class = AttendancePagination  # 2. Attach Pagination here

    def get_queryset(self):
        """
        Supports filtering by:
        - organizationid
        - attendancepolicyid
        - startdate (Exact match)
        - enddate (Exact match)
        - status (Exact match, e.g., 'Open', 'Closed')
        """
        queryset = Attendance.objects.all().order_by('-id')
        
        # 1. Filter by Organization ID
        org_id = self.request.query_params.get('organizationid')
        if org_id:
            queryset = queryset.filter(organizationid_id=org_id)
            
        # 2. Filter by Attendance Policy ID
        policy_id = self.request.query_params.get('attendancepolicyid')
        if policy_id:
            queryset = queryset.filter(attendancepolicyid_id=policy_id)

        # 3. Filter by Start Date
        start_date = self.request.query_params.get('startdate')
        if start_date:
            queryset = queryset.filter(startdate=start_date)

        # 4. Filter by End Date
        end_date = self.request.query_params.get('enddate')
        if end_date:
            queryset = queryset.filter(enddate=end_date)

        # 5. Filter by Status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status__iexact=status)

        return queryset
    
class ProcessAttendanceView(APIView):
    def post(self, request, pk):
        """
        Process an attendance cycle.
        """
        attendance = get_object_or_404(Attendance, pk=pk)

        # Check if already processed
        if attendance.status == 'Processed':
             # Error case ke liye standard response ya custom error structure use karein
             return custom_response_upload(
                 data=None,
                 message="This attendance cycle is already processed.", # Typo fixed here
                 http_status=status.HTTP_400_BAD_REQUEST,
                 status_str="error" # Explicitly saying this is an error
             )

        # Update fields
        attendance.status = 'Processed'
        attendance.processedat = timezone.now()
        
        user_id = request.data.get('processedby')
        if user_id:
            attendance.processedby_id = user_id
        
        attendance.save()
        
        # Prepare response data
        data = {
            "id": attendance.id,
            "status": attendance.status,
            "processedat": attendance.processedat,
            "processedby": attendance.processedby_id
        }

        return custom_response_upload(
            data=data, 
            message="Attendance processed successfully.", 
            http_status=status.HTTP_200_OK
        )
 
class AttendanceBulkUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        # 1. Validate Request Data
        serializer = FileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return custom_response_upload(None, "Invalid data", status.HTTP_400_BAD_REQUEST, status_str="error")

        file = request.FILES['file']
        attendance_id = request.data['attendanceid']
        calculation_mode = request.data.get('calculation_mode', 'auto')
        
        # --- VALIDATION 2: STATUS CHECK (Processed/Closed) ---
        try:
            attendance_instance = Attendance.objects.get(id=attendance_id)
            if attendance_instance.status in ['Processed', 'Closed']:
                return custom_response_upload(
                    data=None, 
                    message=f"Cannot modify attendance. Status is '{attendance_instance.status}'.", 
                    http_status=status.HTTP_400_BAD_REQUEST, 
                    status_str="error"
                )

            policy_instance = attendance_instance.attendancepolicyid
            org_id = attendance_instance.organizationid_id 

            if calculation_mode == 'auto' and not policy_instance:
                 return custom_response_upload(None, "Attendance Policy is missing.", status.HTTP_400_BAD_REQUEST, status_str="error")

        except Attendance.DoesNotExist:
             return custom_response_upload(None, "Invalid Attendance ID", status.HTTP_400_BAD_REQUEST, status_str="error")


        # 2. Read File into DataFrame
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
            else:
                return custom_response_upload(None, "Invalid file format.", status.HTTP_400_BAD_REQUEST, status_str="error")
            
            df = df.where(pd.notnull(df), None)
        except Exception as e:
            return custom_response_upload(None, f"Error reading file: {str(e)}", status.HTTP_400_BAD_REQUEST, status_str="error")

        # 3. Create Employee Mapping (Optimized Lookup)
        employees_qs = Employees.objects.filter(organizationid=org_id, isactive=True).values('employeecode', 'id')
        employee_map = {str(emp['employeecode']).strip(): emp['id'] for emp in employees_qs if emp['employeecode']}

        # ============================================================
        # [NEW PART] OPTIMIZED LEAVE FETCHING LOGIC
        # ============================================================
        leave_map = {}
        
        # Extract all valid dates from file to determine range
        temp_dates = pd.to_datetime(df['Date'], errors='coerce').dropna().dt.date
        
        if not temp_dates.empty:
            min_date = temp_dates.min()
            max_date = temp_dates.max()
            emp_ids_in_file = list(employee_map.values())

            # Fetch Approved Leaves within the file's date range
            # Note: Using 'iexact' for case-insensitive 'approved' check
            leaves_qs = LeaveRequests.objects.filter(
                employee_id__in=emp_ids_in_file,
                status__iexact='APPROVED', 
                start_date__lte=max_date,
                end_date__gte=min_date
            ).values('employee_id', 'start_date', 'end_date')

            # Expand date ranges into individual dates for fast lookup
            for leave in leaves_qs:
                curr_date = leave['start_date']
                end_date = leave['end_date']
                emp_id = leave['employee_id']
                
                while curr_date <= end_date:
                    if min_date <= curr_date <= max_date:
                        leave_map[(emp_id, curr_date)] = 'Leave'
                    curr_date += timedelta(days=1)
        # ============================================================


        # --- VALIDATION 1 PREP: FETCH EXISTING RECORDS ---
        existing_records_qs = Attendancedetail.objects.filter(attendanceid=attendance_instance)
        existing_map = {
            (rec.employeeid_id, rec.attendancedate): rec 
            for rec in existing_records_qs
        }

        records_to_create = [] 
        records_to_update = [] 
        errors = []

        # Helper
        def safe_combine_datetime(date_obj, time_input):
            if not time_input: return None
            try:
                if isinstance(time_input, time): return datetime.combine(date_obj, time_input)
                if isinstance(time_input, str): return pd.to_datetime(f"{date_obj} {time_input}")
                if isinstance(time_input, (datetime, pd.Timestamp)): return time_input
            except: return None
            return None

        # 4. Processing Loop
        try:
            for index, row in df.iterrows():
                # A. Validate Employee
                raw_code = row.get('EmployeeCode')
                if not raw_code: continue 

                emp_code_str = str(raw_code).strip()
                employee_db_id = employee_map.get(emp_code_str)

                if not employee_db_id:
                    errors.append(f"Row {index+2}: Code '{raw_code}' not found.")
                    continue

                # B. Parse Date
                try:
                    attendance_date = pd.to_datetime(row['Date']).date()
                except:
                    errors.append(f"Row {index+2}: Invalid Date.")
                    continue

                # C. Combine Time
                checkin_dt = safe_combine_datetime(attendance_date, row.get('CheckIn'))
                checkout_dt = safe_combine_datetime(attendance_date, row.get('CheckOut'))

                # D. Calculation
                final_status = 'Present'
                final_hours = 0.0

                if calculation_mode == 'manual':
                    final_status = row.get('Status', 'Present')
                    try: final_hours = float(row.get('TotalHours', 0.0))
                    except: final_hours = 0.0
                else: 
                    final_status, final_hours = calculate_attendance_status(checkin_dt, checkout_dt, policy_instance)

                # ============================================================
                # [NEW PART] OVERRIDE STATUS IF LEAVE EXISTS
                # ============================================================
                if (employee_db_id, attendance_date) in leave_map:
                    final_status = 'Leave'
                    # Optional: Reset hours if on leave
                    # final_hours = 0.0 
                # ============================================================

                # --- UPDATE vs CREATE LOGIC ---
                existing_record = existing_map.get((employee_db_id, attendance_date))

                if existing_record:
                    # UPDATE EXISTING
                    existing_record.checkin = checkin_dt
                    existing_record.checkout = checkout_dt
                    existing_record.totalhours = final_hours
                    existing_record.status = final_status
                    existing_record.remarks = row.get('Remarks', '')
                    existing_record.updatedby_id = request.user.id if request.user.id else 1
                    existing_record.updateat = timezone.now()
                    
                    records_to_update.append(existing_record)
                else:
                    # CREATE NEW
                    obj = Attendancedetail(
                        attendanceid=attendance_instance,
                        employeeid_id=employee_db_id,
                        attendancedate=attendance_date,
                        checkin=checkin_dt,
                        checkout=checkout_dt,
                        totalhours=final_hours,
                        status=final_status,
                        remarks=row.get('Remarks', ''),
                        createdby_id=request.user.id if request.user.id else 1,
                        isactive=True
                    )
                    records_to_create.append(obj)
            
            # 5. Database Commit
            if records_to_update:
                Attendancedetail.objects.bulk_update(
                    records_to_update, 
                    fields=['checkin', 'checkout', 'totalhours', 'status', 'remarks', 'updatedby', 'updateat']
                )

            if records_to_create:
                Attendancedetail.objects.bulk_create(records_to_create)

            # Response Logic
            msg_prefix = ""
            if len(records_to_update) > 0:
                msg_prefix = f"Updated {len(records_to_update)} existing records & "

            if errors:
                return custom_response_upload(
                    data={"created": len(records_to_create), "updated": len(records_to_update), "errors": errors}, 
                    message=f"{msg_prefix}Created {len(records_to_create)} records. Some errors occurred.", 
                    http_status=status.HTTP_206_PARTIAL_CONTENT,
                    status_str="warning"
                )
            
            return custom_response_upload(
                data={"created": len(records_to_create), "updated": len(records_to_update)}, 
                message=f"{msg_prefix}Created {len(records_to_create)} records successfully.", 
                http_status=status.HTTP_201_CREATED,
                status_str="success"
            )

        except Exception as e:
            return custom_response_upload(None, f"System Error: {str(e)}", status.HTTP_400_BAD_REQUEST, status_str="error")
                
class AttendanceDashboardView(APIView):
    """
    Unified API for Attendance Reporting with Constant Stats.
    
    Query Params:
    - type: 'daily' or 'summary' (Required)
    - organizationid: (Required)
    - date: (Required if type='daily') YYYY-MM-DD
    - month: (Required if type='summary') YYYY-MM
    """

    def get(self, request, *args, **kwargs):
        report_type = request.query_params.get('type')
        org_id = request.query_params.get('organizationid')
        
        if not org_id:
            return custom_response(None, "Organization ID is required.", status.HTTP_400_BAD_REQUEST, "error")

        # --- 1. DAILY REPORT (Logs + Stats) ---
        if report_type == 'daily':
            target_date = request.query_params.get('date', str(date.today()))
            return self.get_daily_report(org_id, target_date)

        # --- 2. MONTHLY SUMMARY (Payroll View + Stats) ---
        elif report_type == 'summary':
            month_str = request.query_params.get('month') # e.g. "2025-01"
            if not month_str:
                return custom_response(None, "Month (YYYY-MM) is required for summary.", status.HTTP_400_BAD_REQUEST, "error")
            return self.get_monthly_report(org_id, month_str)

        else:
            return custom_response(None, "Invalid 'type'. Use 'daily' or 'summary'.", status.HTTP_400_BAD_REQUEST, "error")

    # ================= HELPERS =================

    def calculate_stats(self, queryset, total_employees_count):
        """
        Common function to calculate stats from ANY queryset (Daily or Monthly).
        """
        stats = queryset.aggregate(
            present=Count('id', filter=Q(status__iexact='Present')),
            absent=Count('id', filter=Q(status__iexact='Absent')),
            leave=Count('id', filter=Q(status__icontains='Leave')),
            half_day=Count('id', filter=Q(status__iexact='Half Day')),
            late=Count('id', filter=Q(status__iexact='Late')),
        )
        
        # Overtime Count (Records jahan totalhours > 8 or 9)
        # Note: Aap chaho tu yahan Policy k hisab se dynamic laga sakte ho
        ot_count = queryset.filter(totalhours__gt=9).count()

        # Attendance Rate Calculation
        # Rate = (Present + Late + Half Day)
        present_count = stats['present'] + stats['late'] + stats['half_day']
        
        # Agar daily hai tu total_employees use karein, agar monthly hai tu records count use karein
        # Best approach: (Total Present Records / Total Records Scanned) * 100
        total_records = queryset.count()
        rate = (present_count / total_records * 100) if total_records > 0 else 0

        return {
            "present": stats['present'],
            "absent": stats['absent'],
            "leave": stats['leave'],
            "half_day": stats['half_day'],
            "late": stats['late'],
            "overtime_count": ot_count,
            "attendance_rate": round(rate, 2),
            "total_active_employees": total_employees_count # Sirf reference k liye
        }

    def get_daily_report(self, org_id, target_date):
        """
        Returns: { "stats": {...}, "report": [Daily Logs] }
        """
        # 1. Total Active Employees
        total_emps = Employees.objects.filter(organizationid=org_id, isactive=True).count()

        # 2. Queryset (Daily)
        records = Attendancedetail.objects.filter(
            employeeid__organizationid=org_id,
            attendancedate=target_date
        ).select_related('employeeid', 'employeeid__departmentid', 'employeeid__designationid').order_by('employeeid__firstname')

        # 3. Calculate Stats
        stats_data = self.calculate_stats(records, total_emps)

        # 4. Serialize Report Data
        serializer = AttendanceDetailReportSerializer(records, many=True)

        response_data = {
            "date": target_date,
            "stats": stats_data,   # <--- Constant Header
            "report": serializer.data  # <--- List View
        }
        return custom_response(response_data, f"Daily report for {target_date}.", status.HTTP_200_OK)

    def get_monthly_report(self, org_id, month_str):
        """
        Returns: { "stats": {...}, "report": [Employee Wise Summary] }
        """
        try:
            year, month = map(int, month_str.split('-'))
        except:
            return custom_response(None, "Invalid Month format.", status.HTTP_400_BAD_REQUEST, "error")

        total_emps = Employees.objects.filter(organizationid=org_id, isactive=True).count()

        # 1. Queryset (Monthly)
        records = Attendancedetail.objects.filter(
            employeeid__organizationid=org_id,
            attendancedate__year=year,
            attendancedate__month=month
        ).select_related('employeeid', 'attendanceid__attendancepolicyid')

        # 2. Calculate Stats (Aggregate for the whole month)
        # Yeh stats pure mahine ka total batayenge (Total Presents in Month, Total Absents in Month)
        stats_data = self.calculate_stats(records, total_emps)

        # 3. Build Employee-wise Summary (List)
        summary_map = {}

        for rec in records:
            emp_id = rec.employeeid_id
            
            if emp_id not in summary_map:
                summary_map[emp_id] = {
                    "employee": {
                        "id": emp_id,
                        "name": f"{rec.employeeid.firstname} {rec.employeeid.lastname or ''}",
                        "code": rec.employeeid.employeecode,
                        "picture": rec.employeeid.picture,
                        "department": rec.employeeid.departmentid.name if rec.employeeid.departmentid else "-"
                    },
                    "present": 0, "absent": 0, "leave": 0, "half_day": 0, "late": 0,
                    "overtime_hrs": 0.0,
                    "rate": 0.0
                }

            # Counters
            s_lower = rec.status.lower() if rec.status else ""
            if 'present' in s_lower: summary_map[emp_id]['present'] += 1
            elif 'absent' in s_lower: summary_map[emp_id]['absent'] += 1
            elif 'leave' in s_lower: summary_map[emp_id]['leave'] += 1
            elif 'half' in s_lower: summary_map[emp_id]['half_day'] += 1
            elif 'late' in s_lower: summary_map[emp_id]['late'] += 1

            # OT Calculation (Policy based)
            policy = rec.attendanceid.attendancepolicyid if rec.attendanceid else None
            limit = float(policy.workinghoursperday) if policy else 8.0
            worked = float(rec.totalhours) if rec.totalhours else 0.0
            
            if worked > limit:
                summary_map[emp_id]['overtime_hrs'] += (worked - limit)

        # Final List Format
        report_list = []
        for emp_id, data in summary_map.items():
            # Employee Rate Calculation
            total_days_worked = data['present'] + data['late'] + data['half_day']
            # Note: Rate calculation can be complex (divide by 30 or divide by working days). 
            # Here keeping it simple: Total Present Days / 30 * 100
            data['rate'] = round((total_days_worked / 30) * 100, 2)
            data['overtime_hrs'] = round(data['overtime_hrs'], 2)
            report_list.append(data)

        response_data = {
            "month": month_str,
            "stats": stats_data,   # <--- Constant Header (Monthly Aggregate)
            "report": report_list  # <--- Summary View
        }
        return custom_response(response_data, f"Monthly summary for {month_str}.", status.HTTP_200_OK)