from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import PayrollSerializer, PayrollRetrieveSerializer
from .models import Payroll
from django.utils import timezone
from workflow.utils import initiate_workflow
from user_rbac.models import Modules 


class CreatePayrollView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PayrollSerializer(data=request.data)

        if serializer.is_valid():
            try:
                org_instance = getattr(request.user, 'organizationid', None)
                if not org_instance:
                    return Response({
                        "message": "User is not associated with any Organization.",
                        "status": status.HTTP_403_FORBIDDEN
                    }, status=status.HTTP_403_FORBIDDEN)
                    
                status_instance = 'pending'
                createdat = timezone.now()
                    
                serializer.save(organizationid=org_instance, status=status_instance, createdat=createdat)

                return Response({
                    "data": serializer.data,
                    "message": "Payroll generated successfully for all employees.",
                    "status": status.HTTP_201_CREATED
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({
                    "message": f"Error: {str(e)}",
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "data": serializer.errors,
            "message": "Validation Error",
            "status": status.HTTP_400_BAD_REQUEST
        }, status=status.HTTP_400_BAD_REQUEST)
        
class PayrollDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            org_instance = getattr(request.user, 'organizationid', None)

            if not org_instance:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)
                
            payroll_instance = Payroll.objects.get(id=id, organizationid=org_instance)
            
            serializer = PayrollRetrieveSerializer(payroll_instance)

            # 4. Success Response
            return Response({
                "message": "Payroll fetched successfully",
                "data": serializer.data,
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Payroll.DoesNotExist:
            return Response({
                "message": "Payroll record not found.",
                "status": status.HTTP_404_NOT_FOUND
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class PayrollProcessView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, id):
        try:
            org_instance = getattr(request.user, 'organizationid', None)
            initiator = getattr(request.user, 'employeeid', None)
            module_id_val = 8
            try:
                payroll_instance = Payroll.objects.get(id=id, organizationid=org_instance)
                payroll_instance.status = 'processing'
                payroll_instance.processedby = request.user
                payroll_instance.processedat = timezone.now()
                payroll_instance.save()
                
            except Payroll.DoesNotExist:
                raise Exception("Payroll record not found")
            
            try:
                module_instance = Modules.objects.get(pk=module_id_val)
            except Modules.DoesNotExist:
                raise Exception("Module not found")
        
            if initiator and org_instance:
                response = initiate_workflow(
                    record_id=id,
                    module_id=module_instance,
                    organization_id=org_instance,
                    initiator_employee=initiator,
                    user=request.user
                )
            else:
                print("Skipped: Missing Initiator or Organization ID")
            
        except Exception as e:
                print(f"Exception in Workflow Block: {str(e)}")
        
        return Response(response, status=status.HTTP_200_OK)