from django.shortcuts import render
from .serializers import WorkflowsSerializer, WorkflowsGetSerializer, WorkflowActionSerializer
from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from .models import Workflows, Workflowlevel, Workflowrecords, WorkflowHistory
from .serializers import WorkflowsSerializer
from Helpers.ResponseHandler import custom_response
from django.utils import timezone
from .utils import update_original_record_status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db import connection
from .utils import dictfetchall, StandardResultsSetPagination 

class WorkflowListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        workflows = Workflows.objects.filter(isdelete=False).order_by('-id')

        org_id = request.query_params.get('organizationid')
        module_id = request.query_params.get('moduleid')
        is_active_param = request.query_params.get('isactive')

        if org_id:
            workflows = workflows.filter(organizationid=org_id)

        if module_id:
            workflows = workflows.filter(moduleid=module_id)

        if is_active_param is not None:
            if is_active_param.lower() == 'true':
                workflows = workflows.filter(isactive=True)
            elif is_active_param.lower() == 'false':
                workflows = workflows.filter(isactive=False)
        else:
            workflows = workflows.filter(isactive=True)

        paginator = PageNumberPagination()
        paginator.page_size = 10
        
        if request.query_params.get('page_size'):
            paginator.page_size = int(request.query_params.get('page_size'))

        result_page = paginator.paginate_queryset(workflows, request)

        serializer = WorkflowsGetSerializer(result_page, many=True)

        pagination_data = {
            "count": paginator.page.paginator.count,
            "total_pages": paginator.page.paginator.num_pages,
            "current_page": paginator.page.number,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link()
        }
        
        return custom_response(
            data=serializer.data,
            pagination=pagination_data,
            message="Workflows fetched successfully",
            status=status.HTTP_200_OK
        )
        
class WorkflowDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            workflow = Workflows.objects.get(pk=pk, isactive=True, isdelete=False)
        except Workflows.DoesNotExist:
            return custom_response(
                message="Workflow not found",
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = WorkflowsGetSerializer(workflow)
        
        return custom_response(
            data=serializer.data,
            message="Workflow details fetched successfully",
            status=status.HTTP_200_OK
        )        

class WorkflowCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WorkflowsSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            
            serializer.save(
                createdby=request.user,
                updatedby=request.user,
                deletedby=request.user,
                createdat=timezone.now(),
                isactive=True,
                isdelete=False
            )

            return custom_response(
                data=serializer.data,
                message="Workflow created successfully",
                status=status.HTTP_201_CREATED
            )
        
        return custom_response(
            data=serializer.errors,
            message="Validation Error",
            status=status.HTTP_400_BAD_REQUEST
        )
        
class WorkflowActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WorkflowActionSerializer(data=request.data)

        if not serializer.is_valid():
            return custom_response(
                data=serializer.errors,
                message="Invalid Data",
                status=status.HTTP_400_BAD_REQUEST
            )

        record_id = serializer.validated_data['record_id']
        action = serializer.validated_data['action']
        remarks = serializer.validated_data.get('remarks', '')
        user = request.user

        try:
            record = Workflowrecords.objects.get(
                id=record_id,
                isactive=True,
                isdelete=False
            )
        except Workflowrecords.DoesNotExist:
            return custom_response(
                data=None,
                message="Workflow Record not found",
                status=status.HTTP_404_NOT_FOUND
            )

        if record.status != 'Pending':
            return custom_response(
                data=None,
                message=f"This request is already {record.status}",
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            current_level_def = Workflowlevel.objects.get(
                workflowid=record.workflowid,
                flowlevel=record.currentlevel,
                isactive=True,
                isdelete=False
            )
        except Workflowlevel.DoesNotExist:
            return custom_response(
                data=None,
                message=f"Workflow Level {record.currentlevel} definition missing",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        print("Logged in user ID:", request.user.id)
        print("Workflow Level Approver ID:", current_level_def.approverid_id)

        approver_id = current_level_def.approverid_id

        if approver_id and approver_id != request.user.id:
            return custom_response(
                data=None,
                message="You are not authorized to approve this level.",
                status=status.HTTP_403_FORBIDDEN
            )

        WorkflowHistory.objects.create(
            workflowrecordid=record,
            flowlevel=record.currentlevel,
            actionby=user,
            action=action,
            remarks=remarks
        )

        if action == 'Rejected':
            record.status = 'Rejected'
            record.remarks = remarks
            record.updatedby = user
            record.updateat = timezone.now()
            record.save()

            update_original_record_status(
                module_id=record.moduleid.id,
                record_id=record.recordid,
                action='Rejected'
            )

            return custom_response(
                data=None,
                message="Request Rejected Successfully",
                status=status.HTTP_200_OK
            )

        if action == 'Approved':

            if current_level_def.isfinallevel:
                record.status = 'Approved'
                record.completed_at = timezone.now()
                record.updatedby = user
                record.updateat = timezone.now()
                record.save()

                update_original_record_status(
                    module_id=record.moduleid.id,
                    record_id=record.recordid,
                    action='Approved'
                )

                return custom_response(
                    data=None,
                    message="Workflow Completed & Approved",
                    status=status.HTTP_200_OK
                )

            # Move to next level
            record.currentlevel += 1
            record.remarks = f"Pending Level {record.currentlevel} Approval"
            record.updatedby = user
            record.updateat = timezone.now()
            record.save()

            return custom_response(
                data=None,
                message=f"Approved. Moved to Level {record.currentlevel}",
                status=status.HTTP_200_OK
            )

class ApproverPendingRequestsView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        try:
            user_id = request.user.id
            filter_wr_id = request.query_params.get('workflow_record_id')
            
            tbl_wr = 'workflowrecords'
            tbl_wl = 'workflowlevel'
            tbl_wf = 'workflows'
            tbl_modules = 'modules'
            tbl_emp = 'employees'
            tbl_wh = 'workflowhistory'
            
            # 1. Base Query (WITHOUT ORDER BY)
            query = f"""
                SELECT 
                    wr.id as workflow_record_id,
                    wr.recordid as record_id,
                    wr.createdat as initiated_at,
                    wh.remarks as my_remarks,
                    wh.action as my_action,
                    
                    wf.name as workflow_name,
                    mod.modulename as module_name,
                    
                    wl.name as step_name,
                    wr.currentlevel as record_current_level,
                    
                    initiator_emp.firstname as initiator_name,
                    initiator_emp.employeecode as initiator_code

                FROM {tbl_wh} wh  
            
                INNER JOIN {tbl_wr} wr ON wh.workflowrecordid = wr.id
                INNER JOIN {tbl_wf} wf ON wr.workflowid = wf.id
                LEFT JOIN {tbl_modules} mod ON wf.moduleid = mod.id
                LEFT JOIN {tbl_wl} wl ON wr.workflowid = wl.workflowid AND wl.approverid = wh.actionby
                LEFT JOIN {tbl_emp} initiator_emp ON wr.initiatorid = initiator_emp.id
                
                WHERE wh.actionby = %s
                AND wr.isactive = True
            """
            
            sql_params = [user_id]

            # 2. Add Dynamic Filter (BEFORE ORDER BY)
            if filter_wr_id:
                query += " AND wr.id = %s"
                sql_params.append(filter_wr_id)
            
            # 3. Add Order By (AT THE VERY END)
            query += " ORDER BY wh.createdat DESC"

            # Execute
            with connection.cursor() as cursor:
                cursor.execute(query, sql_params)
                pending_requests_list = dictfetchall(cursor)

            # --- Pagination & Details Logic (Same as before) ---
            paginator = self.pagination_class()
            paginated_records = paginator.paginate_queryset(pending_requests_list, request, view=self)

            final_data = []
            
            for item in paginated_records:
                module_name = str(item.get('module_name')).upper()
                record_id = item.get('record_id')
                
                detail_data = {}
                
                if module_name == 'OFFBOARDING':
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT 
                                off.offboarding_type, 
                                off.last_working_day,
                                emp.firstname,
                                emp.lastname,
                                emp.employeecode,
                                emp.picture
                            FROM employee_offboarding off
                            INNER JOIN employees emp ON off.employee_id = emp.id
                            WHERE off.id = %s
                        """, [record_id])
                        res = dictfetchall(cursor)
                        if res:
                            row = res[0]
                            detail_data = {
                                "title": f"Offboarding Request - {row['firstname']} {row['lastname']}",
                                "employee_name": f"{row['firstname']} {row['lastname']}",
                                "employee_code": row['employeecode'],
                                "employee_picture": row['picture'],
                                "meta_info": f"Type: {row['offboarding_type']} | LWD: {row['last_working_day']}"
                            }

                elif module_name == 'ONBOARDING':
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT 
                                emp.firstname,
                                emp.lastname,
                                emp.employeecode,
                                emp.dateofappointment,
                                emp.designationid,
                                emp.departmentid
                            FROM employees emp
                            WHERE emp.id = %s
                        """, [record_id])
                        res = dictfetchall(cursor)
                        if res:
                            row = res[0]
                            detail_data = {
                                "title": f"New Hiring - {row['firstname']} {row['lastname']}",
                                "employee_name": f"{row['firstname']} {row['lastname']}",
                                "employee_code": "N/A (New)",
                                "meta_info": f"Joining: {row['dateofappointment']}"
                            }

                else:
                    detail_data = {
                        "title": f"{module_name} Request #{record_id}",
                        "meta_info": "No specific details available."
                    }
                
                item['details'] = detail_data
                final_data.append(item)

            return paginator.get_paginated_response(final_data)

        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)