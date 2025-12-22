from rest_framework import generics
from django.utils import timezone
from .models import LeavePeriods, LeaveTypes
from .serializers import LeavePeriodSerializer, LeaveTypeSerializer
from .utils import StandardPagination, custom_response
from rest_framework import status

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


# --- Leave Types (Annual, Sick, etc) ---
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