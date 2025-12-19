from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Employees, EmployeeOffboarding
from .serializers import EmployeeSerializer, EmployeeOffboardingSerializer, EmployeeOffboardingCreateSerializer
from django.utils import timezone
from workflow.utils import initiate_workflow
from user_rbac.models import Modules 
from Helpers.ResponseHandler import custom_response
from django.db.models import Q
from department.models import Departments
from employee.utils import StandardResultsSetPagination, dictfetchall
from django.db import transaction
from employee.models import EmployeeFinalSettlement
from django.db import connection
from django.conf import settings
from django.db.models import Count

class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Employees.objects.filter(isdelete=False).order_by('-id')

        org_id = request.query_params.get('organizationid')
        if org_id:
            queryset = queryset.filter(organizationid=org_id)

        dept_id = request.query_params.get('departmentid')
        if dept_id:
            queryset = queryset.filter(departmentid=dept_id)

        status_param = request.query_params.get('status')
        if status_param:
            is_active = status_param.lower() == 'true'
            queryset = queryset.filter(isactive=is_active)
            
        search_query = request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(firstname__icontains=search_query) | 
                Q(lastname__icontains=search_query) | 
                Q(cnic__icontains=search_query) | 
                Q(employeecode__icontains=search_query)
            )
        
        total_employees = queryset.count()
        active_employees = queryset.filter(isactive=True).count()
        inactive_employees = queryset.filter(isactive=False).count()
        
        if org_id:
            total_departments = Departments.objects.filter(organizationid=org_id, isdelete=False).count()
        else:
            total_departments = Departments.objects.filter(isdelete=False).count()

        paginator = StandardResultsSetPagination()
        result_page = paginator.paginate_queryset(queryset, request)
        
        serializer = EmployeeSerializer(result_page, many=True)

        response_data = {
            "counts": {
                "total_employees": total_employees,
                "active_employees": active_employees,
                "inactive_employees": inactive_employees,
                "total_departments": total_departments
            },
            "pagination": {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "total_pages": paginator.page.paginator.num_pages,
                "current_page": paginator.page.number
            },
            "results": serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = EmployeeSerializer(data=request.data)
        
        if serializer.is_valid():
            # 1. Employee Save
            employee_instance = serializer.save(
                createdby=request.user,
                createdat=timezone.now(),
                isactive=False,
                isdelete=False
            )
            try:
                module_id_val = 5
                try:
                    module_instance = Modules.objects.get(pk=module_id_val)
                except Modules.DoesNotExist:
                    raise Exception("Module not found")
                
                initiator = getattr(request.user, 'employeeid', None)
                
                if not initiator:
                    print("Error: Logged-in User k paas 'employeeid' nahi hai. Workflow Initiator NULL nahi ho sakta.")
                    

                # 3. Organization Check
                org_id = getattr(request.user, 'organizationid', None)
                print(f"Organization Check: {org_id}")

                # 4. Call Function & CAPTURE RESPONSE
                if initiator and org_id:
                    response = initiate_workflow(
                        record_id=employee_instance.id,
                        module_id=module_instance,
                        organization_id=org_id,
                        initiator_employee=initiator,
                        user=request.user
                    )
                else:
                    print("Skipped: Missing Initiator or Organization ID")

            except Exception as e:
                print(f"Exception in Workflow Block: {str(e)}")
            
            return custom_response(
                data=serializer.data,
                message="Employee created successfully",
                status=status.HTTP_201_CREATED
            )

        return custom_response(
            data=serializer.errors,
            message="Validation Error",
            status=status.HTTP_400_BAD_REQUEST
        )

class EmployeeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Employees.objects.get(pk=pk, isdelete=False)
        except Employees.DoesNotExist:
            return None

    def get(self, request, pk):
        employee = self.get_object(pk)
        if not employee:
            return Response({"detail": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = EmployeeSerializer(employee)
        return Response(serializer.data)

    def patch(self, request, pk):
        employee = self.get_object(pk)
        if not employee:
            return Response({"detail": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = EmployeeSerializer(employee, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(updatedby=request.user, updateat=timezone.now())
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        employee = self.get_object(pk)
        if not employee:
            return Response({"detail": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        employee.isdelete = True
        employee.deletedby = request.user
        employee.deleteat = timezone.now()
        employee.save()
        return Response({"detail": "Employee deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class EmployeeOffboardingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = EmployeeOffboardingCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return custom_response(
                data=serializer.errors,
                message="Validation Error",
                status=status.HTTP_400_BAD_REQUEST
            )

        initiator = getattr(request.user, 'employeeid', None)
        if not initiator:
            return custom_response(
                data=None,
                message="User not linked with employee",
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            settlement_data = serializer.validated_data.pop('settlement')

            offboarding = serializer.save(
                requested_by=request.user,
                status='PENDING'
            )
            
            existing_settlement = EmployeeFinalSettlement.objects.filter(
                    employee=offboarding.employee,
                    isdelete=False,
                    status__in=['DRAFT', 'IN_PROGRESS', 'APPROVED']
                ).exists()

            if existing_settlement:
                raise Exception("Final settlement already exists for this employee")

            settlement = EmployeeFinalSettlement.objects.create(
                offboarding=offboarding,
                employee=offboarding.employee,
                last_salary=settlement_data['last_salary'],
                leave_encashment=settlement_data.get('leave_encashment', 0),
                bonus=settlement_data.get('bonus', 0),
                other_earnings=settlement_data.get('other_earnings', 0),
                deductions=settlement_data.get('deductions', 0),
                remarks=settlement_data.get('remarks', ''),
                status='PENDING',
                createdby=request.user
            )

            module = Modules.objects.filter(modulename__iexact='OFFBOARDING', isactive=True, isdelete=False).first()
            if not module:
                raise Exception("Offboarding module not found")

            wf_response = initiate_workflow(
                record_id=offboarding.id,
                module_id=module,
                organization_id=request.user.organizationid,
                initiator_employee=initiator,
                user=request.user
            )

            if not wf_response.get("success"):
                raise Exception(wf_response.get("message"))

            offboarding.status = 'IN_PROGRESS'
            offboarding.save(update_fields=['status'])

            response_data = EmployeeOffboardingSerializer(offboarding).data
            
            earnings = (
                settlement.last_salary + 
                settlement.leave_encashment + 
                settlement.bonus + 
                settlement.other_earnings
            )
            calculated_net_payable = earnings - settlement.deductions

            response_data['settlement'] = {
                'id': settlement.id,
                'last_salary': settlement.last_salary,
                'bonus': settlement.bonus,
                'deductions': settlement.deductions,
                'leave_encashment': settlement.leave_encashment,
                'other_earnings': settlement.other_earnings,
                'net_payable': calculated_net_payable,
                'remarks': settlement.remarks,
            }

            return custom_response(
                data=response_data,
                message="Employee offboarding & final settlement initiated successfully",
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return custom_response(
                data=None,
                message=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EmployeeOffboardingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            offboarding = EmployeeOffboarding.objects.get(pk=pk)
        except EmployeeOffboarding.DoesNotExist:
            return Response(
                {"detail": "Offboarding not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EmployeeOffboardingSerializer(offboarding)
        return Response(serializer.data)
    
def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

class WorkflowChecklistView(APIView):
    
    def get(self, request, record_id, module_name):
        try:
            module_name = module_name.upper()
            
            # Default tables
            tbl_workflow_rec = 'workflowrecords'
            tbl_workflow = 'workflows'
            tbl_levels = 'workflowlevel'
            tbl_history = 'workflowhistory'
            tbl_employees = 'employees'
            tbl_users = 'users'
            tbl_departments = 'departments' 
            tbl_designations = 'designations'
            
            # --- Dynamic Logic ---
            if module_name == 'OFFBOARDING':
                target_app_table = 'employee_offboarding'
                target_fk_field = 'employee_id'
                # Offboarding mein Employee table alag se join hoti hai
                employee_join_logic = f"INNER JOIN {tbl_employees} emp ON app_record.{target_fk_field} = emp.id"
                
            elif module_name == 'ONBOARDING':
                # Onboarding mein 'record_id' hi 'employee_id' hai
                target_app_table = 'employees'
                # Employee table already main table hai, dubara join karne ki zaroorat nahi
                # Hum alias 'app_record' ko hi 'emp' maan lenge query mein
                employee_join_logic = "" 
                
            else:
                return Response({"message": "Module not supported"}, status=status.HTTP_400_BAD_REQUEST)

            # ---------------------------------------------------------
            # STEP 2: META QUERY (Fetch ONLY the Latest Record)
            # ---------------------------------------------------------
            # Note: Maine 'ORDER BY wr.createdat DESC LIMIT 1' add kiya hai
            # Taake agar multiple records hon to latest wala aaye.
            
            # Onboarding ke liye field selection adjust ki hai
            emp_alias = "app_record" if module_name == 'ONBOARDING' else "emp"

            meta_query = f"""
                SELECT 
                    wr.id as workflow_record_id,
                    wr.status as overall_status,
                    wr.createdat as initiated_at,
                    
                    -- Employee Details (Dynamic Alias)
                    {emp_alias}.firstname,
                    {emp_alias}.lastname,
                    {emp_alias}.employeecode,
                    {emp_alias}.picture,
                    {emp_alias}.designationid,
                    {emp_alias}.departmentid,
                    
                    wf.name as workflow_name,
                    wf.description as workflow_description
                    
                FROM {tbl_workflow_rec} wr
                INNER JOIN {tbl_workflow} wf ON wr.workflowid = wf.id
                INNER JOIN {target_app_table} app_record ON wr.recordid = app_record.id
                {employee_join_logic}
                
                WHERE wr.recordid = %s 
                -- Optional: AND wf.modulename ID check
                ORDER BY wr.createdat DESC 
                LIMIT 1
            """

            # ---------------------------------------------------------
            # STEP 3: CHECKLIST QUERY
            # ---------------------------------------------------------
            checklist_query = f"""
                SELECT 
                    wl.name as step_name,
                    wl.description as step_description,
                    wl.flowlevel as step_sequence,
                    wl.id as level_id,
                    wl.timelimit,
                    
                    wh.action as action_status,
                    wh.remarks as approver_remarks,
                    wh.createdat as action_date,
                    
                    -- LOGIC: Agar action le liya hai to Action User, warna Assigned User
                    COALESCE(action_user.username, assigned_user.username) as action_by_username,
                    
                    -- Employee Details Selection (Priority: History > Assigned)
                    COALESCE(history_emp.firstname, assigned_emp.firstname) as approver_firstname,
                    COALESCE(history_emp.lastname, assigned_emp.lastname) as approver_lastname,
                    
                    -- Designation & Department Selection
                    COALESCE(history_desig.title, assigned_desig.title) as approver_designation,
                    COALESCE(history_dept.name, assigned_dept.name) as approver_department,

                    CASE 
                        WHEN wh.id IS NOT NULL THEN wh.action 
                        ELSE 'Pending' 
                    END as display_status

                FROM {tbl_levels} wl
                INNER JOIN {tbl_workflow_rec} wr ON wr.workflowid = wl.workflowid
                
                -- 1. HISTORY JOIN (Jo action perform ho chuka hai)
                LEFT JOIN {tbl_history} wh ON wl.flowlevel = wh.flowlevel AND wh.workflowrecordid = wr.id
                LEFT JOIN {tbl_users} action_user ON wh.actionby = action_user.id
                LEFT JOIN {tbl_employees} history_emp ON action_user.employeeid = history_emp.id
                LEFT JOIN {tbl_departments} history_dept ON history_emp.departmentid = history_dept.id
                LEFT JOIN {tbl_designations} history_desig ON history_emp.designationid = history_desig.id
                
                LEFT JOIN users assigned_user 
                    ON wl.approverid = assigned_user.id

                LEFT JOIN employees assigned_emp 
                    ON assigned_user.employeeid = assigned_emp.id

                LEFT JOIN departments assigned_dept 
                    ON assigned_emp.departmentid = assigned_dept.id

                LEFT JOIN designations assigned_desig 
                    ON assigned_emp.designationid = assigned_desig.id
                
                WHERE wr.id = %s 
                AND wl.isactive = True
                ORDER BY wl.flowlevel ASC;
            """

            with connection.cursor() as cursor:
                # 1. Fetch Meta Data (Latest Record)
                cursor.execute(meta_query, [record_id])
                meta_data_list = dictfetchall(cursor)
                
                if not meta_data_list:
                    return Response({"message": "No workflow record found."}, status=status.HTTP_404_NOT_FOUND)
                
                header_info = meta_data_list[0]
                current_wr_id = header_info['workflow_record_id'] # Get the specific ID (e.g., 3)

                # 2. Fetch Checklist Data using the Workflow Record ID (not Record ID)
                # Isse ambiguity khatam ho jayegi
                cursor.execute(checklist_query, [current_wr_id])
                checklist_data = dictfetchall(cursor)

            response_data = {
                "record_info": {
                    "module": module_name,
                    "record_id": record_id,
                    "workflow_record_id": header_info.get('workflow_record_id'),
                    "current_status": header_info.get('overall_status'),
                    "initiated_at": header_info.get('initiated_at'),
                },
                "employee_details": {
                    "full_name": f"{header_info.get('firstname')} {header_info.get('lastname') or ''}".strip(),
                    "code": header_info.get('employeecode'),
                    "picture": header_info.get('picture'),
                    "designation_id": header_info.get('designationid'),
                    "department_id": header_info.get('departmentid'),
                },
                "workflow_details": {
                    "name": header_info.get('workflow_name'),
                    "description": header_info.get('workflow_description'),
                },
                "timeline": checklist_data
            }

            return Response({"status": "success", "data": response_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class EmployeeOffboardingListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        # 1. Base Queryset (Select related fixed for ...id fields)
        # Hum 'employee' ke andar departmentid, branchid, designationid, organizationid ko fetch karenge
        queryset = EmployeeOffboarding.objects.select_related(
            'employee', 
            'employee__departmentid',   # Fixed: department -> departmentid
            'employee__branchid',       # Fixed: branch -> branchid
            'employee__designationid',  # Fixed: designation -> designationid
            'employee__organizationid', # Added: organizationid for optimization
            'final_settlement'          # Added: final_settlement for optimization
        ).filter(is_active=True).order_by('-id') # Added order_by to fix pagination warning

        # 2. Filter by Organization ID
        org_id = request.query_params.get('organizationid')
        if org_id:
            # Fixed: employee__organizationid
            queryset = queryset.filter(employee__organizationid=org_id)
        
        # 3. Search Filter (Fixed field names: firstname, employeecode)
        search_query = request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(employee__firstname__icontains=search_query) |      # Fixed: first_name -> firstname
                Q(employee__lastname__icontains=search_query) |       # Fixed: last_name -> lastname
                Q(employee__employeecode__icontains=search_query) |   # Fixed: employee_code -> employeecode
                Q(employee__departmentid__name__icontains=search_query) # Fixed: department -> departmentid
            )

        # 4. Counts Calculation
        stats = queryset.aggregate(
            total=Count('id'),
            inprogress=Count('id', filter=Q(status='IN_PROGRESS')),
            approved=Count('id', filter=Q(status='Approved')),
            rejected=Count('id', filter=Q(status='Rejected')),
            completed=Count('id', filter=Q(status='Completed')),
        )

        # 5. Filter by Status
        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        # 6. Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = EmployeeOffboardingSerializer(page, many=True)
            return Response({
                'counts': {
                    'total': stats['total'] or 0,
                    'inprogress': stats['inprogress'] or 0,
                    'approved': stats['approved'] or 0,
                    'rejected': stats['rejected'] or 0,
                    'completed': stats['completed'] or 0,
                },
                'pagination': {
                    'count': paginator.page.paginator.count,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link(),
                    'total_pages': paginator.page.paginator.num_pages
                },
                'results': serializer.data
            }, status=status.HTTP_200_OK)

        serializer = EmployeeOffboardingSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)