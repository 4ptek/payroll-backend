from django.utils import timezone
from .models import Workflows, Workflowrecords
from django.apps import apps
from rest_framework.pagination import PageNumberPagination
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings
from users.models import Users
from .models import Workflowlevel
from django.utils.html import strip_tags

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

    if not record_id or not module_id or not organization_id or not initiator_employee:
        return {
            "success": False,
            "message": "Missing required workflow parameters."
        }

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
        wf_record = Workflowrecords.objects.create(
            workflowid=workflow,
            recordid=record_id,
            moduleid=module_id,
            initiatorid=initiator_employee,
            currentlevel=1,
            status='Pending',
            remarks='',
            createdby=user,
            updatedby=user,
            deletedby=user,
            createdat=timezone.now(),
            isactive=True,
            isdelete=False
        )
        
        try:
            level_1_def = Workflowlevel.objects.filter(
                workflowid=workflow,
                flowlevel=1,
                isactive=True,
                isdelete=False
            ).first()

            if level_1_def and level_1_def.approverid:
                module_name = getattr(module_id, 'modulename', 'Request')
                
                send_approval_notification(
                    approver_user_id=level_1_def.approverid_id, 
                    record_id=wf_record.id,
                    module_name=module_name
                )
        except Exception as email_error:
            print(f"Email Trigger Failed: {email_error}")

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
                        leave_type=leave_request.leave_type
                    )

                    days_to_deduct = leave_request.day_count 

                    if balance.total_allocated is not None:
                        balance.total_allocated = balance.total_allocated - Decimal(days_to_deduct)
                        balance.used = balance.used + Decimal(days_to_deduct)
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

        elif module_id == 8:
            PayrollModel = apps.get_model('payroll', 'Payroll')
            payroll = PayrollModel.objects.get(id=record_id)
            
            if action == 'Approved':
                payroll.status = 'PROCESSED'
            elif action == 'Rejected':
                payroll.status = 'REJECTED'
            
            payroll.save(update_fields=['status'])
            print(f"Payroll {record_id} status updated to {payroll.status}.")
        
        elif module_id == 63:
            BookingsModel = apps.get_model('meetingroom','Bookings')
            booking = BookingsModel.objects.get(booking_id=record_id)
            
            if action == 'Approved':
                booking.status = 'APPROVED'
            elif action == 'Rejected':
                booking.status = 'REJECTED'
            
            booking.save(update_fields=['status'])
            print(f"Booking {record_id} status updated to {booking.status}.")
            
    except Exception as e:
        print(f"Error updating original record: {str(e)}")    
                
def send_approval_notification(approver_user_id, record_id, module_name, approval_url = None):
    """
    approval_url: Woh link jahan user click kar ke approve karega (e.g., http://yoursite.com/approve/123)
    """
    try:
        approver = Users.objects.get(id=approver_user_id)
        
        approval_url = "http://116.90.108.83:8087/approvals/requestDetails/" + str(record_id)
        
        if approver.email:
            subject = f"Action Required: Approval Needed for {module_name}"
            
            html_message = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                        <h2 style="color: #2c3e50;">Approval Request</h2>
                        <p>Hello <strong>{approver.username}</strong>,</p>
                        
                        <p>A new request has been generated in the <strong>{module_name}</strong> system and is awaiting your review.</p>
                        
                        <p style="margin: 20px 0;">
                            <a href="{approval_url}" 
                               style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                               View & Approve Request
                            </a>
                        </p>
                        
                        <p style="font-size: 12px; color: #777;">
                            Reference ID: #{record_id} <br>
                            If the button doesn't work, please copy this link: {approval_url}
                        </p>
                    </div>
                </body>
            </html>
            """
            
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message, # Plain text version
                settings.EMAIL_HOST_USER,
                [approver.email],
                html_message=html_message, # HTML version
                fail_silently=True,
            )
            print(f"HTML Email sent to {approver.email}")
            
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        
def send_custom_html_mail(user, subject, title, message_body, link_url, button_text, color_theme="#007bff"):
    """
    Ek reusable function jo HTML email bhejta hai.
    color_theme: Blue (#007bff) for Action, Green (#28a745) for Success, Red (#dc3545) for Reject.
    """
    if not user.email:
        print(f"User {user.username} has no email.")
        return

    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: {color_theme};">{title}</h2>
                <p>Hello <strong>{user.username}</strong>,</p>
                
                <p>{message_body}</p>
                
                <p style="margin: 25px 0;">
                    <a href="{link_url}" 
                       style="background-color: {color_theme}; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                       {button_text}
                    </a>
                </p>
                
                <p style="font-size: 12px; color: #777;">
                    If the button doesn't work, verify via this link: <br> {link_url}
                </p>
            </div>
        </body>
    </html>
    """
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.EMAIL_HOST_USER,
        [user.email],
        html_message=html_message,
        fail_silently=True,
    )
    print(f"Email sent to {user.email}")