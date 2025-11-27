from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.backends import TokenBackend
from django.conf import settings
from users.serializers import UserRoleSerializer, UsersSerializer
from .models import Userroles, Users
from django.utils import timezone
from django.core.mail import send_mail
from rest_framework import permissions
from .utils import check_password, make_password
from .models import Users
from rest_framework.permissions import IsAuthenticated


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"detail": "Email and password required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = Users.objects.get(email=email, isactive=True, isdelete=False)
        except Users.DoesNotExist:
            return Response(
                {"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Use your custom bcrypt check
        if not check_password(password, user.userpassword):
            return Response(
                {"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Update last login
        user.lastlogin = timezone.now()
        user.save(update_fields=["lastlogin"])

        # Create JWT tokens
        refresh = RefreshToken.for_user(user)
        org_id = user.organizationid.id if user.organizationid else None
        refresh["org_id"] = org_id
        refresh.access_token["org_id"] = org_id

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
            }
        )


class CustomRefreshView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST
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
                return Response(
                    {"detail": "User not found or inactive"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Generate new access token
            token = RefreshToken(refresh_token)
            new_access = token.access_token

            return Response({"access": str(new_access)}, status=status.HTTP_200_OK)

        except (TokenError, InvalidToken):
            return Response(
                {"detail": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"detail": "Email required"}, status=status.HTTP_400_BAD_REQUEST
            )

        user = Users.objects.filter(email=email, isactive=True, isdelete=False).first()
        if not user:
            return Response(
                {"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Generate reset token
        refresh = RefreshToken.for_user(user)
        reset_token = str(refresh.access_token)

        # Build reset URL
        reset_url = f"http://localhost:8001/reset-password?token={reset_token}"

        # Send email
        send_mail(
            subject="Password Reset Request",
            message=f"Hi {user.username},\n\nClick the link to reset your password:\n{reset_url}\n\nIgnore if you didn't request this.",
            from_email=None,
            recipient_list=[user.email],
        )

        return Response(
            {"detail": "Password reset link sent to your email"},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not token or not new_password:
            return Response(
                {"detail": "Token and new password required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            backend = TokenBackend(algorithm="HS256", signing_key=settings.SECRET_KEY)
            decoded = backend.decode(token, verify=True)
            user_id = decoded.get("user_id")
        except (TokenError, InvalidToken):
            return Response(
                {"detail": "Invalid or expired token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = Users.objects.filter(id=user_id, isactive=True, isdelete=False).first()
        if not user:
            return Response(
                {"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        user.userpassword = make_password(new_password)
        user.lastlogin = timezone.now()
        user.save(update_fields=["userpassword", "lastlogin"])

        return Response(
            {"detail": "Password reset successful"}, status=status.HTTP_200_OK
        )

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        return Response({"detail": "Logout successful"}, status=status.HTTP_200_OK)

class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = Users.objects.filter(isactive=True, isdelete=False)
        serializer = UsersSerializer(users, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = UsersSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
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
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = UsersSerializer(user)
        return Response(serializer.data)

    def patch(self, request, pk):  
        user = self.get_object(pk)
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = UsersSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            user.updatedby = request.user
            user.updateat = timezone.now()
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        user.isdelete = True  # soft delete
        user.deletedby = request.user
        user.deleteat = timezone.now()
        user.save()
        return Response({"detail": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
class UserRoleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        roles = Userroles.objects.filter(isactive=True, isdelete=False)
        serializer = UserRoleSerializer(roles, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = UserRoleSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
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
            return Response({"detail": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserRoleSerializer(role)
        return Response(serializer.data)
    
    def patch(self, request, pk):  
        role = self.get_object(pk)
        if not role:
            return Response({"detail": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserRoleSerializer(role, data=request.data, partial=True)
        if serializer.is_valid():
            role.updatedby = request.user
            role.updateat = timezone.now()
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            role = Userroles.objects.get(pk=pk)
            role.delete() 
            return Response({"message": "Role deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Userroles.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)