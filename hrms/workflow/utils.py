from django.utils import timezone
from .models import Workflows, Workflowrecords
from django.apps import apps
from rest_framework.pagination import PageNumberPagination
from decimal import Decimal

def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

def initiate_workflow(record_id, module_id, organization_id, initiator_employee, user):

    # 1️⃣ Validate mandatory inputs
    if not record_id or not module_id or not organization_id or not initiator_employee:
        return {
            "success": False,
            "message": "Missing required workflow parameters."
        }

    # 2️⃣ Get Active Workflow
    workflow = Workflows.objects.filter(
        organizationid=organization_id,
        moduleid=module_id,
        isactive=True,
        isdelete=False
    ).first()

    if not workflow:
        return {
            "success": False,
            "message": "No active workflow configured for this module."
        }

    # 3️⃣ Prevent duplicate workflow record
    if Workflowrecords.objects.filter(
        workflowid=workflow,
        recordid=record_id,
        isactive=True,
        isdelete=False
    ).exists():
        return {
            "success": False,
            "message": "Workflow already initiated for this record."
        }

    try:
        # 4️⃣ Create workflow record
        wf_record = Workflowrecords.objects.create(
            workflowid=workflow,
            recordid=record_id,
            moduleid=module_id,
            initiatorid=initiator_employee,

            currentlevel= 1,
            status='Pending',
            remarks='Workflow Initiated',

            createdby=user,
            updatedby=user,
            deletedby=user,
            createdat=timezone.now(),

            isactive=True,
            isdelete=False
        )

        return {
            "success": True,
            "message": "Workflow initiated successfully.",
            "data": {
                "workflow_record_id": wf_record.id,
                "current_level": wf_record.currentlevel
            }
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Workflow initiation failed: {str(e)}"
        }
        
def update_original_record_status(module_id, record_id, action):
    """
    Jab Workflow Finalize ho jaye, to yeh function Original Table (Employee/Leave) 
    ka status update karega.
    """
    try:
        if module_id == 5:
            EmployeeModel = apps.get_model('employee', 'Employees')
            record = EmployeeModel.objects.get(id=record_id)
            
            if action == 'Approved':
                record.isactive = True
            elif action == 'Rejected':
                record.isactive = False
            
            record.save()
            print(f"Employee {record_id} is now Active!")

        elif module_id == 12:
            OffboardingModel = apps.get_model('employee', 'EmployeeOffboarding')
            offboarding = OffboardingModel.objects.get(id=record_id)
            
            EmployeeModel = apps.get_model('employee', 'Employees')
            employee = EmployeeModel.objects.get(id=offboarding.employee.id)

            SettlementModel = apps.get_model('employee', 'EmployeeFinalSettlement')
            
            settlement = SettlementModel.objects.filter(offboarding=offboarding).first()
            
            if action == 'Approved':
                employee.isactive = False
                employee.save(update_fields=['isactive'])
                
                offboarding.status = 'Completed'
                offboarding.completed_at = timezone.now()
                offboarding.save(update_fields=['status', 'completed_at'])

                if settlement:
                    settlement.status = 'APPROVED'
                    settlement.save(update_fields=['status'])
                
                print(f"Offboarding {record_id} completed. Settlement Approved. Employee deactivated.")

            elif action == 'Rejected':
                offboarding.status = 'Rejected'
                offboarding.save(update_fields=['status'])

                if settlement:
                    settlement.status = 'REJECTED'
                    settlement.save(update_fields=['status'])

                print(f"Offboarding {record_id} rejected. Settlement Rejected.")
        
        elif module_id == 62:
            LeaveRequestsModel = apps.get_model('leaves', 'LeaveRequests')
            leave_request = LeaveRequestsModel.objects.get(id=record_id)
            
            if action == 'Approved':
                leave_request.status = 'APPROVED'
                try:
                    LeaveBalancesModel = apps.get_model('leaves', 'LeaveBalances')
                    
                    balance = LeaveBalancesModel.objects.get(
                        employee=leave_request.employee,
                        leave_type=leave_request.leave_type,
                        leave_period=leave_request.leave_period
                    )

                    days_to_deduct = leave_request.number_of_days 

                    if balance.total_allocated is not None:
                        balance.total_allocated = balance.total_allocated - Decimal(days_to_deduct)
                        balance.save()
                        print(f"Balance updated. Remaining allocated: {balance.total_allocated}")
                    
                except LeaveBalancesModel.DoesNotExist:
                    print(f"Leave Balance record not found for Employee ID: {leave_request.employee.id}")
                except Exception as e:
                    print(f"Error updating balance: {str(e)}")
                
            elif action == 'Rejected':
                leave_request.status = 'REJECTED'
            
            leave_request.save(update_fields=['status'])
            print(f"Leave Request {record_id} status updated to {leave_request.status}.")

    except Exception as e:
        print(f"Error updating original record: {str(e)}")        