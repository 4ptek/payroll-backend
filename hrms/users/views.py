from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.backends import TokenBackend
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from organization.serializers import OrganizationSerializer
from employee.serializers import EmployeeSerializer
from users.serializers import UserRoleSerializer, UsersSerializer
from .models import Userroles, Users
from .utils import check_password, make_password
from Helpers.ResponseHandler import custom_response

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return custom_response(
                data=None,
                message="Email and password required",
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Step 1: User existence check
            user = Users.objects.get(email=email, isactive=True, isdelete=False)
        except Users.DoesNotExist:
            return custom_response(
                data=None,
                message="Invalid credentials",
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Step 2: Employee active status check (New Validation)
        if user.employeeid:
            if not user.employeeid.isactive:
                return custom_response(
                    data=None, 
                    message="Your employee account is inactive. Please contact HR.",
                    status=status.HTTP_403_FORBIDDEN
                )

        # Step 3: Password check
        if not check_password(password, user.userpassword):
            return custom_response(
                data=None,
                message="Invalid credentials",
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Update last login
        user.lastlogin = timezone.now()
        user.save(update_fields=["lastlogin"])
        
        # ... baki ka code same rahega ...
        org_data = None
        if user.organizationid:
            org_data = OrganizationSerializer(user.organizationid).data

        emp_data = None
        if user.employeeid:
            emp_data = EmployeeSerializer(user.employeeid).data

        # Create JWT tokens
        refresh = RefreshToken.for_user(user)
        org_id = user.organizationid.id if user.organizationid else None
        emp_id = user.employeeid_id if user.employeeid else None
        
        refresh["org_id"] = org_id
        refresh["employee_id"] = emp_id
        refresh.access_token["org_id"] = org_id
        refresh.access_token["employee_id"] = emp_id

        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "organization_details": org_data,
            "employee_details": emp_data
        }

        return custom_response(
            data=data,
            message="Login successful",
            status=status.HTTP_200_OK
        )

class CustomRefreshView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return custom_response(
                message="Refresh token required",
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            algorithm = getattr(settings, "SIMPLE_JWT", {}).get("ALGORITHM", "HS256")
            backend = TokenBackend(algorithm=algorithm)

            decoded_data = backend.decode(refresh_token, verify=False)
            user_id = decoded_data.get("user_id")

            user = Users.objects.filter(
                id=user_id, isactive=True, isdelete=False
            ).first()
            if not user:
                return custom_response(
                    message="User not found or inactive",
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Generate new access token
            token = RefreshToken(refresh_token)
            new_access = token.access_token

            return custom_response(
                data={"access": str(new_access)},
                message="Token refreshed successfully",
                status=status.HTTP_200_OK
            )

        except (TokenError, InvalidToken):
            return custom_response(
                message="Invalid or expired refresh token",
                status=status.HTTP_401_UNAUTHORIZED
            )

class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return custom_response(
                message="Email required",
                status=status.HTTP_400_BAD_REQUEST
            )

        user = Users.objects.filter(email=email, isactive=True, isdelete=False).first()
        if not user:
            return custom_response(
                message="User not found",
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate reset token
        refresh = RefreshToken.for_user(user)
        reset_token = str(refresh.access_token)

        # Build reset URL
        reset_url = f"http://localhost:8001/resetPassword/{reset_token}"

        # Send email
        send_mail(
            subject="Password Reset Request",
            message=f"Hi {user.username},\n\nClick the link to reset your password:\n{reset_url}\n\nIgnore if you didn't request this.",
            from_email=None,
            recipient_list=[user.email],
        )

        return custom_response(
            message="Password reset link sent to your email",
            status=status.HTTP_200_OK
        )

class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not token or not new_password:
            return custom_response(
                data=None,
                message="Token and new password required",
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            backend = TokenBackend(algorithm="HS256", signing_key=settings.SECRET_KEY)
            decoded = backend.decode(token, verify=True)
            user_id = decoded.get("user_id")
        except (TokenError, InvalidToken):
            return custom_response(
                data=None,
                message="Invalid or expired token",
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = Users.objects.filter(id=user_id, isdelete=False).first()
        if not user:
            return custom_response(
                data=None,
                message="User not found",
                status=status.HTTP_404_NOT_FOUND
            )

        user.userpassword = make_password(new_password)
        user.lastlogin = timezone.now()
        user.isactive = True  # Activate user upon password reset
        user.save()

        return custom_response(
            data=None,
            message="Password reset successful",
            status=status.HTTP_200_OK
        )

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        return custom_response(
            message="Logout successful",
            status=status.HTTP_200_OK
        )

class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = Users.objects.filter(isactive=True, isdelete=False)
        serializer = UsersSerializer(users, many=True)
        return custom_response(
            data=serializer.data,
            message="Users fetched successfully",
            status=status.HTTP_200_OK
        )
    
    def post(self, request):
        serializer = UsersSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            reset_token = str(refresh.access_token)
            activation_url = f"http://localhost:8001/set-password/{reset_token}"
            try:
                send_mail(
                    subject="Welcome! Set Your Password",
                    message=f"Hi {user.username},\n\nYour account has been created by Admin.\nClick the link below to set your password:\n{activation_url}\n\nThis link is valid for a limited time.",
                    from_email=None,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                email_status = "Email sent successfully."
            except Exception as e:
                email_status = f"User created but failed to send email: {str(e)}"

            return custom_response(
                data=serializer.data,
                message=f"User created successfully. {email_status}",
                status=status.HTTP_201_CREATED
            )
        
        return custom_response(
            data=serializer.errors,
            message="Validation Error",
            status=status.HTTP_400_BAD_REQUEST
        )

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Users.objects.get(pk=pk, isdelete=False)
        except Users.DoesNotExist:
            return None

    def get(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return custom_response(
                message="User not found",
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = UsersSerializer(user)
        return custom_response(
            data=serializer.data,
            message="User details fetched successfully",
            status=status.HTTP_200_OK
        )

    def patch(self, request, pk):  
        user = self.get_object(pk)
        if not user:
            return custom_response(
                message="User not found",
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = UsersSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            user.updatedby = request.user
            user.updateat = timezone.now()
            serializer.save()
            return custom_response(
                data=serializer.data,
                message="User updated successfully",
                status=status.HTTP_200_OK
            )
        return custom_response(
            data=serializer.errors,
            message="Validation Error",
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return custom_response(
                message="User not found",
                status=status.HTTP_404_NOT_FOUND
            )
        user.isdelete = True  # soft delete
        user.deletedby = request.user
        user.deleteat = timezone.now()
        user.save()
        return custom_response(
            message="User deleted successfully",
            status=status.HTTP_200_OK 
        )
    
class UserRoleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        roles = Userroles.objects.filter(isactive=True, isdelete=False)
        serializer = UserRoleSerializer(roles, many=True)
        return custom_response(
            data=serializer.data,
            message="Roles fetched successfully",
            status=status.HTTP_200_OK
        )
    
    def post(self, request):
        serializer = UserRoleSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return custom_response(
                data=serializer.data,
                message="Role created successfully",
                status=status.HTTP_201_CREATED
            )
        return custom_response(
            data=serializer.errors,
            message="Validation Error",
            status=status.HTTP_400_BAD_REQUEST
        )
        
class UserRoleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Userroles.objects.get(pk=pk, isdelete=False)
        except Userroles.DoesNotExist:
            return None

    def get(self, request, pk):
        role = self.get_object(pk)
        if not role:
            return custom_response(
                message="Role not found",
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = UserRoleSerializer(role)
        return custom_response(
            data=serializer.data,
            message="Role details fetched successfully",
            status=status.HTTP_200_OK
        )
    
    def patch(self, request, pk):  
        role = self.get_object(pk)
        if not role:
            return custom_response(
                message="Role not found",
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = UserRoleSerializer(role, data=request.data, partial=True)
        if serializer.is_valid():
            role.updatedby = request.user
            role.updateat = timezone.now()
            serializer.save()
            return custom_response(
                data=serializer.data,
                message="Role updated successfully",
                status=status.HTTP_200_OK
            )
        return custom_response(
            data=serializer.errors,
            message="Validation Error",
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        try:
            role = Userroles.objects.get(pk=pk)
            role.delete() 
            return custom_response(
                message="Role deleted successfully",
                status=status.HTTP_200_OK
            )
        except Userroles.DoesNotExist:
            return custom_response(
                message="Role not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return custom_response(
                message=str(e),
                status=status.HTTP_400_BAD_REQUEST
            )