from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Count
from django.utils import timezone

# Import your models
from employee.models import Employees, EmployeeOffboarding
from department.models import Departments
from branches.models import Branches
from attendance.models import Attendancedetail
from leaves.models import LeaveRequests, LeaveBalances
from workflow.models import Workflowrecords

class OrgAdminDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        start_of_month = today.replace(day=1)

        total_employees = Employees.objects.filter(isactive=True, isdelete=False).count()
        new_joiners = Employees.objects.filter(
            dateofappointment__gte=start_of_month, isactive=True
        ).count()

        active_branches = Branches.objects.filter(isactive=True).count()
        active_depts = Departments.objects.filter(isactive=True).count()

        present_count = Attendancedetail.objects.filter(attendancedate=today).count()
        absent_count = total_employees - present_count

        data = {
            "dashboard_type": "ORG_ADMIN",
            "headcount": {
                "total": total_employees,
                "new_this_month": new_joiners
            },
            "structure": {
                "branches": active_branches,
                "departments": active_depts
            },
            "today_activity": {
                "present": present_count,
                "absent": max(0, absent_count),
                "date": today.strftime("%Y-%m-%d")
            }
        }
        return Response(data)

class HRAdminDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()

        pending_leaves = LeaveRequests.objects.filter(status__iexact='PENDING').count()
        pending_workflows = Workflowrecords.objects.filter(status__iexact='PENDING').count()

        active_exits = EmployeeOffboarding.objects.filter(
            status__in=['PENDING', 'IN_PROGRESS'], is_active=True
        ).count()
        
        late_count = Attendancedetail.objects.filter(
            attendancedate=today, status__icontains='LATE'
        ).count()

        data = {
            "dashboard_type": "HR_ADMIN",
            "action_required": {
                "leave_requests": pending_leaves,
                "workflow_approvals": pending_workflows
            },
            "hr_monitoring": {
                "employees_exiting": active_exits,
                "late_today": late_count
            }
        }
        return Response(data)

class EmployeeDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        emp_id = None

        # DEBUG PRINTS (Console check karein)
        print("Auth Type:", type(request.auth))
        print("Auth Data:", request.auth)

        # --- STEP 1: TOKEN SE ID NIKALNA (Best Method) ---
        # SimpleJWT mein request.auth dictionary ki tarah behave karta hai, par dict hota nahi.
        # Isliye hum seedha .get() try karenge.
        
        if request.auth:
            try:
                # Agar request.auth object hai (SimpleJWT):
                if hasattr(request.auth, 'get'): 
                    emp_id = request.auth.get('employee_id')
                
                # Agar request.auth dictionary hai (Standard JWT):
                elif isinstance(request.auth, dict):
                    emp_id = request.auth.get('employee_id')
                    
                print(f"Token se mila Employee ID: {emp_id}")
            except Exception as e:
                print(f"Token Error: {e}")

        # --- STEP 2: AGAR TOKEN FAIL HO JAYE (Fallback) ---
        if not emp_id:
            # Agar User model ke sath Employee ka OneToOne relation hai:
            if hasattr(request.user, 'employee_details'):
                 emp_id = request.user.employee_details.id
            
            # Agar User model mein 'employee_id' field hai:
            elif hasattr(request.user, 'employee_id'):
                 emp_id = request.user.employee_id

        # --- FINAL CHECK ---
        if not emp_id:
            return Response(
                {"error": "Could not find Employee ID in Token or User record"}, 
                status=404
            )

        # --- DATABASE QUERY ---
        try:
            current_emp = Employees.objects.get(id=emp_id)
        except Employees.DoesNotExist:
            return Response(
                {"error": f"Employee record with ID {emp_id} not found in DB"}, 
                status=404
            )

        # --- DASHBOARD LOGIC (Same as before) ---
        today = timezone.now().date()

        # 1. Leaves
        balances = LeaveBalances.objects.filter(employee=current_emp).values(
            'leave_type__name', 'total_allocated', 'used'
        )
        formatted_balances = []
        for b in balances:
            remaining = (b['total_allocated'] or 0) - (b['used'] or 0)
            formatted_balances.append({
                "type": b['leave_type__name'],
                "remaining": remaining
            })

        # 2. Attendance
        today_attendance = Attendancedetail.objects.filter(
            employeeid=current_emp, attendancedate=today
        ).first()

        status_today = "Absent"
        check_in_time = "-"
        if today_attendance:
            status_today = today_attendance.status or "Present"
            if today_attendance.checkin:
                check_in_time = today_attendance.checkin.strftime("%H:%M")

        # 3. Workflow
        last_workflow = Workflowrecords.objects.filter(
            initiatorid=current_emp
        ).order_by('-createdat').first()

        recent_req = "No recent requests"
        req_status = "-"
        if last_workflow:
            recent_req = f"Request #{last_workflow.recordid}"
            req_status = last_workflow.status

        data = {
            "dashboard_type": "EMPLOYEE",
            "profile": {
                "name": f"{current_emp.firstname} {current_emp.lastname or ''}",
                "designation": current_emp.designationid.title if current_emp.designationid else "N/A"
            },
            "leaves": formatted_balances,
            "today": {
                "status": status_today,
                "check_in": check_in_time
            },
            "latest_activity": {
                "request": recent_req,
                "status": req_status
            }
        }
        return Response(data)