from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Employees
from .serializers import EmployeeSerializer
from django.utils import timezone
from workflow.utils import initiate_workflow
from user_rbac.models import Modules 
from workflow.utils import initiate_workflow
from Helpers.ResponseHandler import custom_response

class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employees = Employees.objects.filter(isdelete=False)
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EmployeeSerializer(data=request.data)
        
        if serializer.is_valid():
            # 1. Employee Save
            employee_instance = serializer.save(
                createdby=request.user,
                createdat=timezone.now(),
                isactive=True,
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
                    print("❌ Error: Logged-in User k paas 'employeeid' nahi hai. Workflow Initiator NULL nahi ho sakta.")
                    

                # 3. Organization Check
                org_id = getattr(request.user, 'organizationid', None)
                print(f"🏢 Organization Check: {org_id}")

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
                    print("❌ Skipped: Missing Initiator or Organization ID")

            except Exception as e:
                print(f"❌ Exception in Workflow Block: {str(e)}")
            
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
