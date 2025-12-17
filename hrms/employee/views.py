from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Employees, EmployeeOffboarding
from .serializers import EmployeeSerializer, EmployeeOffboardingSerializer
from django.utils import timezone
from workflow.utils import initiate_workflow
from user_rbac.models import Modules 
from Helpers.ResponseHandler import custom_response
from django.db.models import Q
from department.models import Departments
from employee.utils import StandardResultsSetPagination

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

class EmployeeOffboardingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EmployeeOffboardingSerializer(data=request.data)

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

        offboarding = serializer.save(
            requested_by=request.user,
            status='PENDING'
        )

        try:
            module = Modules.objects.filter(
                modulename__iexact='OFFBOARDING',
                isactive=True,
                isdelete=False
            ).first()

            if not module:
                return custom_response(
                    data=None,
                    message="Offboarding module not found",
                    status=status.HTTP_400_BAD_REQUEST
                )

            wf_response = initiate_workflow(
                record_id=offboarding.id,
                module_id=module,
                organization_id=request.user.organizationid,
                initiator_employee=initiator,  # FK instance ✅
                user=request.user
            )

            if not wf_response["success"]:
                return custom_response(
                    data=None,
                    message=wf_response["message"],
                    status=status.HTTP_400_BAD_REQUEST
                )

            offboarding.status = 'IN_PROGRESS'
            offboarding.save(update_fields=['status'])

        except Exception as e:
            return custom_response(
                data=None,
                message=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return custom_response(
            data=EmployeeOffboardingSerializer(offboarding).data,
            message="Employee offboarding initiated successfully",
            status=status.HTTP_201_CREATED
        )


class EmployeeOffboardingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = EmployeeOffboarding.objects.filter(is_active=True)

        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        serializer = EmployeeOffboardingSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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