from rest_framework import generics
from django.utils import timezone
from .models import LeavePeriods, LeaveTypes
from .serializers import LeavePeriodSerializer, LeaveTypeSerializer
from .utils import StandardPagination, custom_response
from rest_framework import status
from .serializers import LeaveBalanceSerializer, LeaveRequestSerializer, StandardResultsSetPagination
from .models import LeaveBalances, LeaveRequests
from workflow.utils import initiate_workflow
from django_filters.rest_framework import DjangoFilterBackend
from user_rbac.models import Modules

class LeavePeriodListCreateView(generics.ListCreateAPIView):
    queryset = LeavePeriods.objects.all().order_by('-id') 
    serializer_class = LeavePeriodSerializer
    pagination_class = StandardPagination
    
    def get_queryset(self):
        user_org_id = self.request.auth.get('org_id')
        return LeavePeriods.objects.filter(organization_id=user_org_id).order_by('-id')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            
            pagination_data = {
                "total_records": self.paginator.page.paginator.count,
                "total_pages": self.paginator.page.paginator.num_pages,
                "current_page": self.paginator.page.number,
                "next": self.paginator.get_next_link(),
                "previous": self.paginator.get_previous_link()
            }
            
            return custom_response(
                data=serializer.data, 
                message="Leave periods fetched successfully", 
                status=status.HTTP_200_OK,
                pagination=pagination_data
            )

        serializer = self.get_serializer(queryset, many=True)
        return custom_response(
            data=serializer.data, 
            message="Leave periods fetched successfully", 
            status=status.HTTP_200_OK
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return custom_response(
            data=serializer.data, 
            message="Leave period created successfully", 
            status=status.HTTP_201_CREATED
        )

    def perform_create(self, serializer):
        user_org_id = self.request.auth.get('org_id')
        
        # Fallback if token is missing it
        if not user_org_id:
            user_org_id = getattr(self.request.user, 'organizationid', None)

        serializer.save(
            organization_id=user_org_id, 
            created_by=self.request.user, 
            created_at=timezone.now()
        )

class LeaveTypeListCreateView(generics.ListCreateAPIView):
    # Fallback queryset (get_queryset handles the real logic)
    queryset = LeaveTypes.objects.all().order_by('-id')
    serializer_class = LeaveTypeSerializer
    pagination_class = StandardPagination

    # --- 1. Filter: Get Leave Types for User's Organization Only ---
    def get_queryset(self):
        user_org_id = self.request.auth.get('org_id')
        return LeaveTypes.objects.filter(organization_id=user_org_id).order_by('-id')

    # --- 2. Customize GET Response ---
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            pagination_data = {
                "total_records": self.paginator.page.paginator.count,
                "total_pages": self.paginator.page.paginator.num_pages,
                "current_page": self.paginator.page.number,
                "next": self.paginator.get_next_link(),
                "previous": self.paginator.get_previous_link()
            }
            return custom_response(
                data=serializer.data, 
                message="Leave types fetched successfully", 
                status=status.HTTP_200_OK,
                pagination=pagination_data
            )

        serializer = self.get_serializer(queryset, many=True)
        return custom_response(
            data=serializer.data, 
            message="Leave types fetched successfully", 
            status=status.HTTP_200_OK
        )

    # --- 3. Customize POST Response ---
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return custom_response(
            data=serializer.data, 
            message="Leave type created successfully", 
            status=status.HTTP_201_CREATED
        )

    # --- 4. Save: Auto-assign Organization ID and User ---
    def perform_create(self, serializer):
        user_org_id = self.request.auth.get('org_id')
        
        # Fallback if token is missing it
        if not user_org_id:
            user_org_id = getattr(self.request.user, 'organizationid', None)

        serializer.save(
            organization_id=user_org_id, 
            created_by=self.request.user, 
            created_at=timezone.now()
        )
        
class LeaveBalanceListView(generics.ListAPIView):
    queryset = LeaveBalances.objects.all().order_by('-id')
    serializer_class = LeaveBalanceSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    
    filterset_fields = ['employee']
        
class LeaveRequestListCreateView(generics.ListCreateAPIView):
    queryset = LeaveRequests.objects.all().order_by('-id')
    serializer_class = LeaveRequestSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    
    # Enable filtering by employee
    filterset_fields = ['employee']

    def create(self, request, *args, **kwargs):
        # 1. Deserialize and Validate Data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 2. Save the Leave Request (Status default usually 'Pending')
        # We assign created_by to the logged-in user
        leave_request = serializer.save(
            created_by=request.user,
            created_at=timezone.now(),
            status="PENDING" 
        )

        # ---------------------------------------------------
        # 3. WORKFLOW INTEGRATION
        # ---------------------------------------------------
        
        # NOTE: You need to pass the Module ID for "Leave" either from 
        # the frontend or hardcode it here if it's constant.
        module = Modules.objects.filter(
            modulename__iexact='LeaveRequest',
            isactive=True, 
            isdelete=False
        ).first()

        if not module:
            # Agar module nahi mila to error return karein
            return Response({
                "message": "LeaveRequest module configuration not found.",
                "data": serializer.data
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Assuming organization_id is attached to the logged-in user or passed in body
        # Modify this line based on how you store organization info
        organization_id = self.request.auth.get('org_id')
        # organization_id = getattr(request.user, 'organization_id', request.data.get('organization_id'))

        # Call your existing function
        workflow_response = initiate_workflow(
            record_id=leave_request.id,
            module_id=module,
            organization_id=organization_id,
            initiator_employee=leave_request.employee, # The employee applying
            user=request.user
        )

        # 4. Construct Final Response
        response_data = {
            "data": serializer.data,
            "workflow_status": workflow_response
        }

        if workflow_response['success']:
             return custom_response(
                data=response_data, 
                message="Leave Request Created successfully", 
                status=status.HTTP_201_CREATED
            )
        else:
            return custom_response(
                data=response_data, 
                message="Leave Request saved, but workflow failed to start.", 
                status=status.HTTP_200_OK
            )