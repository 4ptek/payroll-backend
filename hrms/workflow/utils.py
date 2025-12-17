from django.utils import timezone
from .models import Workflows, Workflowrecords
from django.apps import apps

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
            print(f"✅ Employee {record_id} is now Active!")

        elif module_id == 12:
            OffboardingModel = apps.get_model('employee', 'EmployeeOffboarding')
            offboarding = OffboardingModel.objects.get(id=record_id)
            
            EmployeeModel = apps.get_model('employee', 'Employees')
            employee = EmployeeModel.objects.get(id=offboarding.employee.id)
            
            if action == 'Approved':
                employee.isactive = False
                employee.save(update_fields=['isactive'])
                
                offboarding.status = 'Completed'
                offboarding.completed_at = timezone.now()
                offboarding.save(update_fields=['status', 'completed_at'])
                
                print(f"✅ EmployeeOffboarding {record_id} completed. Employee {employee.id} deactivated.")
            elif action == 'Rejected':
                offboarding.status = 'Rejected'
                offboarding.save(update_fields=['status'])
                print(f"❌ EmployeeOffboarding {record_id} rejected.")

    except Exception as e:
        print(f"❌ Error updating original record: {str(e)}")        