from django.utils import timezone
from .models import Workflows, Workflowrecords

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