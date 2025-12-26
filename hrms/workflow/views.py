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
from payroll.models import Payroll
from payroll.serializers import PayrollRetrieveSerializer


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

class ApproverAllRequestsView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        try:
            user_id = request.user.id
            workflow_record_id = request.query_params.get('workflow_record_id')

            # =========================
            # 🔹 BASE UNION QUERY
            # =========================
            final_query = """
                SELECT *
                FROM (
                    -- PENDING
                    SELECT
                        wr.id AS workflow_record_id,
                        wr.recordid,
                        wr.createdat AS initiated_at,
                        wr.remarks as remarks,
                        wl.description AS current_level_description,
                        NULL::timestamptz AS action_at,
                        'PENDING' AS my_status,
                        wf.name AS workflow_name,
                        mod.modulename AS module_name,
                        emp.firstname AS initiator_firstname,
                        emp.lastname AS initiator_lastname,
                        emp.employeecode AS initiator_code,
                        wr.createdat AS sort_date
                    FROM workflowrecords wr
                    INNER JOIN workflowlevel wl
                        ON wl.workflowid = wr.workflowid
                        AND wl.flowlevel = wr.currentlevel
                    INNER JOIN workflows wf ON wf.id = wr.workflowid
                    LEFT JOIN modules mod ON wf.moduleid = mod.id
                    LEFT JOIN employees emp ON wr.initiatorid = emp.id
                    WHERE wl.approverid = %s
                      AND wr.status = 'Pending'
                      AND wr.isactive = true
                      AND wr.isdelete = false
                      AND NOT EXISTS (
                          SELECT 1
                          FROM workflowhistory wh
                          WHERE wh.workflowrecordid = wr.id
                            AND wh.flowlevel = wl.flowlevel
                            AND wh.actionby = %s
                      )

                    UNION ALL

                    -- APPROVED / REJECTED
                    SELECT
                        wr.id AS workflow_record_id,
                        wr.recordid,
                        wr.createdat AS initiated_at,
                        wr.remarks as remarks,
                        wl.description AS current_level_description,
                        wh.createdat AS action_at,
                        UPPER(wh.action) AS my_status,
                        wf.name AS workflow_name,
                        mod.modulename AS module_name,
                        emp.firstname AS initiator_firstname,
                        emp.lastname AS initiator_lastname,
                        emp.employeecode AS initiator_code,
                        wh.createdat AS sort_date
                    FROM workflowhistory wh
                    INNER JOIN workflowrecords wr ON wr.id = wh.workflowrecordid
                    INNER JOIN workflows wf ON wf.id = wr.workflowid
                    INNER JOIN workflowlevel wl ON wl.workflowid = wr.workflowid AND wl.flowlevel = wh.flowlevel
                    LEFT JOIN modules mod ON wf.moduleid = mod.id
                    LEFT JOIN employees emp ON wr.initiatorid = emp.id
                    WHERE wh.actionby = %s
                      AND wh.action IN ('Approved', 'Rejected')
                      AND wr.isactive = true
                      AND wr.isdelete = false
                ) t
            """

            params = [user_id, user_id, user_id]

            # =========================
            # 🔹 APPLY RECORD ID FILTER OUTSIDE UNION
            # =========================
            if workflow_record_id:
                final_query += " WHERE t.workflow_record_id = %s"
                params.append(workflow_record_id)

            # =========================
            # 🔹 ORDER BY SORT_DATE DESC
            # =========================
            final_query += " ORDER BY t.sort_date DESC"

            with connection.cursor() as cursor:
                cursor.execute(final_query, params)
                records = dictfetchall(cursor)

            # =========================
            # 🔹 MODULE-SPECIFIC DETAILS
            # =========================
            final_data = []

            for item in records:
                module_name = (item.get('module_name') or '').upper()
                record_id = item.get('recordid')
                details = {}

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
                            r = res[0]
                            details = {
                                "title": f"Offboarding - {r['firstname']} {r['lastname']}",
                                "employee_name": f"{r['firstname']} {r['lastname']}",
                                "employee_code": r['employeecode'],
                                "employee_picture": r['picture'],
                                "meta_info": f"Type: {r['offboarding_type']} | LWD: {r['last_working_day']}"
                            }

                elif module_name == 'ONBOARDING':
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT firstname, lastname, dateofappointment, employeecode
                            FROM employees
                            WHERE id = %s
                        """, [record_id])
                        res = dictfetchall(cursor)
                        if res:
                            r = res[0]
                            details = {
                                "title": f"Onboarding - {r['firstname']} {r['lastname']}",
                                "employee_name": f"{r['firstname']} {r['lastname']}",
                                "employee_code": r['employeecode'] or "N/A",
                                "meta_info": f"Joining Date: {r['dateofappointment']}"
                            }
                
                elif module_name == 'Payroll Processing' or module_name == 'PAYROLL PROCESSING':
                    try:
                        payroll_instance = Payroll.objects.get(id=record_id)
                        serializer = PayrollRetrieveSerializer(payroll_instance)            
                        details = serializer.data
                        p_start = str(payroll_instance.periodstart)
                        p_end = str(payroll_instance.periodend)
                        details['title'] = f"Payroll Processing ({p_start} to {p_end})"
                        details['meta_info'] = f"Status: {payroll_instance.status} | Net: {details.get('total_net', 0)}"
                        
                    except Payroll.DoesNotExist:
                        details = {
                            "title": f"Payroll Request #{record_id}",
                            "meta_info": "Record not found"
                        }
                    except Exception as e:
                         details = {
                            "title": f"Payroll Request #{record_id}",
                            "meta_info": f"Error: {str(e)}"
                        }
                elif module_name == 'LEAVEREQUEST':
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                SELECT 
                                    lt.name as leave_name,
                                    lt.default_days,
                                    lb.total_allocated,
                                    lb.used,
                                    lr.start_date,
                                    lr.end_date,
                                    emp.firstname,
                                    emp.lastname,
                                    emp.employeecode
                                FROM leave_requests lr
                                INNER JOIN employees emp ON lr.employee_id = emp.id
                                LEFT JOIN leave_types lt ON lr.leave_type_id = lt.id
                                LEFT JOIN leave_balances lb ON lb.leave_type_id = lt.id AND lb.employee_id = lr.employee_id
                                WHERE lr.id = %s
                            """, [record_id])
                            
                            res = dictfetchall(cursor)
                            if res:
                                r = res[0]
                                # Format dates nicely
                                s_date = r['start_date'].strftime('%Y-%m-%d') if r.get('start_date') else 'N/A'
                                e_date = r['end_date'].strftime('%Y-%m-%d') if r.get('end_date') else 'N/A'
                                
                                details = {
                                    "title": f"Leave Request - {r['firstname']} {r['lastname']}",
                                    "employee_name": f"{r['firstname']} {r['lastname']}",
                                    "employee_code": r['employeecode'], 
                                    "leave_type": r['leave_name'],
                                    "total_allocated": r['total_allocated'],
                                    "used": r['used'],
                                    "default_days": r['default_days'],
                                    "start_date": s_date,
                                    "end_date": e_date,
                                    # Now using the actual leave name fetched from the JOIN
                                    "meta_info": f"Type: {r['leave_name']} | From: {s_date} To: {e_date}"
                                }
                    except Exception as e:
                        details = {
                            "title": f"Leave Request #{record_id}",
                            "meta_info": f"Error: {str(e)}"
                        }
                else:
                    details = {
                        "title": f"{module_name} Request #{record_id}",
                        "meta_info": "No additional details available."
                    }

                item["details"] = details
                final_data.append(item)

            # =========================
            # 🔹 PAGINATION
            # =========================
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(final_data, request, view=self)
            return paginator.get_paginated_response(page)

        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
