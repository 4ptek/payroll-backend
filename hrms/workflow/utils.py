from django.utils import timezone
from .models import Workflows, Workflowrecords
from django.apps import apps

def initiate_workflow(record_id, module_id, organization_id, initiator_employee, user):
    workflow = Workflows.objects.filter(
        organizationid=organization_id,
        moduleid=module_id,
        isactive=True,
        isdelete=False
    ).first()

    if not workflow:
        return {
            "success": False, 
            "message": "No active workflow found for this module."
        }

    try:
        wf_record = Workflowrecords.objects.create(
            workflowid=workflow,
            recordid=record_id,
            moduleid=module_id,
            initiatorid=initiator_employee,
            
            currentlevel=1,
            status='Pending',
            remarks='Workflow Initiated',
            
            createdby=user,
            updatedby=user,
            deletedby=user,
            
            isactive=True,
            isdelete=False,
            createdat=timezone.now()
        )
        
        return {
            "success": True, 
            "message": "Workflow initiated successfully.",
            "data": wf_record
        }
        
    except Exception as e:
        return {
            "success": False, 
            "message": str(e)
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

        elif module_id == 2:
            LeaveModel = apps.get_model('leaves', 'LeaveRequest')
            record = LeaveModel.objects.get(id=record_id)
            
            if action == 'Approved':
                record.status = 'Approved'
            elif action == 'Rejected':
                record.status = 'Rejected'
            
            record.save()

    except Exception as e:
        print(f"❌ Error updating original record: {str(e)}")        