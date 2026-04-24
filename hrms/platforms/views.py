from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from .models import Platforms, EmployeeEmails, EmployeePlatformAccounts
from .serializers import (
    PlatformCreateSerializer,
    PlatformListSerializer,
    EmployeeEmailCreateSerializer,
    EmployeeEmailListSerializer,
    PlatformAccountCreateSerializer,
    PlatformAccountListSerializer,
)


def get_org(request):
    return getattr(request.user, 'organizationid', None)

class PlatformCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PlatformCreateSerializer(data=request.data)

        if serializer.is_valid():
            try:
                org = get_org(request)
                if not org:
                    return Response({
                        "message": "User is not associated with any Organization.",
                        "status": status.HTTP_403_FORBIDDEN
                    }, status=status.HTTP_403_FORBIDDEN)

                serializer.save(
                    organizationid=org,
                    createdby=request.user,
                    createdat=timezone.now(),
                    isactive=True,
                    isdelete=False,
                )

                return Response({
                    "data": serializer.data,
                    "message": "Platform created successfully.",
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


class PlatformListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            platforms = Platforms.objects.filter(
                organizationid=org,
                isdelete=False
            ).order_by('name')

            serializer = PlatformListSerializer(platforms, many=True)

            return Response({
                "data": serializer.data,
                "message": "Platforms fetched successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlatformDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_platform(self, platform_id, org):
        try:
            return Platforms.objects.get(id=platform_id, organizationid=org, isdelete=False)
        except Platforms.DoesNotExist:
            return None

    def get(self, request, platform_id):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            platform = self.get_platform(platform_id, org)
            if not platform:
                return Response({
                    "message": "Platform not found.",
                    "status": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = PlatformListSerializer(platform)
            return Response({
                "data": serializer.data,
                "message": "Platform fetched successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, platform_id):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            platform = self.get_platform(platform_id, org)
            if not platform:
                return Response({
                    "message": "Platform not found.",
                    "status": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = PlatformCreateSerializer(platform, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(
                    updatedby=request.user,
                    updateat=timezone.now()
                )
                return Response({
                    "data": serializer.data,
                    "message": "Platform updated successfully.",
                    "status": status.HTTP_200_OK
                }, status=status.HTTP_200_OK)

            return Response({
                "data": serializer.errors,
                "message": "Validation Error",
                "status": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, platform_id):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            platform = self.get_platform(platform_id, org)
            if not platform:
                return Response({
                    "message": "Platform not found.",
                    "status": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            platform.isdelete = True
            platform.isactive = False
            platform.deletedby = request.user
            platform.deleteat = timezone.now()
            platform.save()

            return Response({
                "message": "Platform deleted successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeEmailCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = EmployeeEmailCreateSerializer(
            data=request.data,
            context={'org': get_org(request)}
        )

        if serializer.is_valid():
            try:
                org = get_org(request)
                if not org:
                    return Response({
                        "message": "User is not associated with any Organization.",
                        "status": status.HTTP_403_FORBIDDEN
                    }, status=status.HTTP_403_FORBIDDEN)

                serializer.save(
                    organizationid=org,
                    createdby=request.user,
                    createdat=timezone.now(),
                    isactive=True,
                    isdelete=False,
                )

                return Response({
                    "data": serializer.data,
                    "message": "Employee email added successfully.",
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


class EmployeeEmailListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            emails = EmployeeEmails.objects.filter(
                organizationid=org,
                isdelete=False
            )

            emp_id = request.query_params.get('employee')
            if emp_id:
                emails = emails.filter(employeeid=emp_id)

            serializer = EmployeeEmailListSerializer(emails, many=True)

            return Response({
                "data": serializer.data,
                "message": "Employee emails fetched successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeEmailDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_email(self, email_id, org):
        try:
            return EmployeeEmails.objects.get(id=email_id, organizationid=org, isdelete=False)
        except EmployeeEmails.DoesNotExist:
            return None

    def get(self, request, email_id):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            email_obj = self.get_email(email_id, org)
            if not email_obj:
                return Response({
                    "message": "Email not found.",
                    "status": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = EmployeeEmailListSerializer(email_obj)
            return Response({
                "data": serializer.data,
                "message": "Email fetched successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, email_id):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            email_obj = self.get_email(email_id, org)
            if not email_obj:
                return Response({
                    "message": "Email not found.",
                    "status": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = EmployeeEmailCreateSerializer(
                email_obj,
                data=request.data,
                partial=True,
                context={'org': org}
            )
            if serializer.is_valid():
                serializer.save(
                    updatedby=request.user,
                    updateat=timezone.now()
                )
                return Response({
                    "data": serializer.data,
                    "message": "Email updated successfully.",
                    "status": status.HTTP_200_OK
                }, status=status.HTTP_200_OK)

            return Response({
                "data": serializer.errors,
                "message": "Validation Error",
                "status": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, email_id):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            email_obj = self.get_email(email_id, org)
            if not email_obj:
                return Response({
                    "message": "Email not found.",
                    "status": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            # Check: koi active platform assignment to nahi
            active_accounts = EmployeePlatformAccounts.objects.filter(
                employeeemailid=email_obj,
                isactive=True,
                isdelete=False
            ).count()

            if active_accounts > 0:
                return Response({
                    "message": f"Ye email {active_accounts} platform(s) pe assign hai. Pehle unhe remove karo.",
                    "status": status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)

            email_obj.isdelete = True
            email_obj.isactive = False
            email_obj.deletedby = request.user
            email_obj.deleteat = timezone.now()
            email_obj.save()

            return Response({
                "message": "Email deleted successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlatformAccountCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PlatformAccountCreateSerializer(data=request.data)

        if serializer.is_valid():
            try:
                org = get_org(request)
                if not org:
                    return Response({
                        "message": "User is not associated with any Organization.",
                        "status": status.HTTP_403_FORBIDDEN
                    }, status=status.HTTP_403_FORBIDDEN)

                serializer.save(
                    organizationid=org,
                    createdby=request.user,
                    createdat=timezone.now(),
                    isactive=True,
                    isdelete=False,
                )

                return Response({
                    "data": serializer.data,
                    "message": "Platform account assigned successfully.",
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


class PlatformAccountListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            accounts = EmployeePlatformAccounts.objects.filter(
                organizationid=org,
                isdelete=False
            ).select_related('employeeid', 'platformid', 'employeeemailid')

            emp_id      = request.query_params.get('employee')
            platform_id = request.query_params.get('platform')

            if emp_id:
                accounts = accounts.filter(employeeid=emp_id)
            if platform_id:
                accounts = accounts.filter(platformid=platform_id)

            serializer = PlatformAccountListSerializer(accounts, many=True)

            return Response({
                "data": serializer.data,
                "message": "Platform accounts fetched successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlatformAccountDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_account(self, account_id, org):
        try:
            return EmployeePlatformAccounts.objects.get(
                id=account_id, organizationid=org, isdelete=False
            )
        except EmployeePlatformAccounts.DoesNotExist:
            return None

    def get(self, request, account_id):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            account = self.get_account(account_id, org)
            if not account:
                return Response({
                    "message": "Account not found.",
                    "status": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = PlatformAccountListSerializer(account)
            return Response({
                "data": serializer.data,
                "message": "Account fetched successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, account_id):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            account = self.get_account(account_id, org)
            if not account:
                return Response({
                    "message": "Account not found.",
                    "status": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = PlatformAccountCreateSerializer(
                account, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save(
                    updatedby=request.user,
                    updateat=timezone.now()
                )
                return Response({
                    "data": serializer.data,
                    "message": "Account updated successfully.",
                    "status": status.HTTP_200_OK
                }, status=status.HTTP_200_OK)

            return Response({
                "data": serializer.errors,
                "message": "Validation Error",
                "status": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, account_id):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            account = self.get_account(account_id, org)
            if not account:
                return Response({
                    "message": "Account not found.",
                    "status": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            account.isdelete = True
            account.isactive = False
            account.deletedby = request.user
            account.deleteat = timezone.now()
            account.save()

            return Response({
                "message": "Account removed successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeePlatformProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, employee_id):
        try:
            org = get_org(request)
            if not org:
                return Response({
                    "message": "User is not associated with any Organization.",
                    "status": status.HTTP_403_FORBIDDEN
                }, status=status.HTTP_403_FORBIDDEN)

            accounts = EmployeePlatformAccounts.objects.filter(
                employeeid=employee_id,
                organizationid=org,
                isdelete=False
            ).select_related('platformid', 'employeeemailid', 'employeeid')

            if not accounts.exists():
                return Response({
                    "data": [],
                    "message": "Is employee ke koi platform accounts nahi hain.",
                    "status": status.HTTP_200_OK
                }, status=status.HTTP_200_OK)

            # Group by platform
            grouped = {}
            employee_info = None

            for acc in accounts:
                emp = acc.employeeid
                if not employee_info:
                    employee_info = {
                        "employee_id": emp.id,
                        "employee_name": f"{emp.firstname or ''} {emp.lastname or ''}".strip(),
                        "employee_code": emp.employeecode,
                    }

                platform_id = acc.platformid.id
                if platform_id not in grouped:
                    grouped[platform_id] = {
                        "platform_id": platform_id,
                        "platform_name": acc.platformid.name,
                        "platform_icon": acc.platformid.icon,
                        "accounts": []
                    }

                grouped[platform_id]["accounts"].append({
                    "account_id": acc.id,
                    "email": acc.employeeemailid.email if acc.employeeemailid else None,
                    "username": acc.username,
                    "notes": acc.notes,
                    "isactive": acc.isactive,
                })

            return Response({
                "data": {
                    **employee_info,
                    "platforms": list(grouped.values())
                },
                "message": "Employee platform profile fetched successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)