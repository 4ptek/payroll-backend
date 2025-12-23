from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import SalaryStructureSerializer
from .models import SalaryStructure, SalaryComponents


class SalaryStructureCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SalaryStructureSerializer(data=request.data)

        if serializer.is_valid():
            try:
                org_instance = getattr(request.user, 'organizationid', None)

                if not org_instance:
                    return Response({
                        "message": "User is not associated with any Organization.",
                        "status": status.HTTP_403_FORBIDDEN
                    }, status=status.HTTP_403_FORBIDDEN)
                    
                serializer.save(org=org_instance)

                return Response({
                    "data": serializer.data,
                    "message": "Salary Structure created successfully",
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



class SalaryStructureListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        org_id = getattr(self.request.user, 'organizationid', None)
        if not org_id:
            return SalaryStructure.objects.none()
        
        return SalaryStructure.objects.filter(org=org_id).prefetch_related('salarycomponents_set').order_by('-id')

    def get(self, request):
        try:
            queryset = self.get_queryset()

            serializer = SalaryStructureSerializer(queryset, many=True)

            return Response({
                "data": serializer.data,
                "message": "Salary Structures fetched successfully",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)