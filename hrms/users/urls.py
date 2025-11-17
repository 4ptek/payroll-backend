from django.urls import path
from .views import CustomRefreshView, ForgotPasswordView, LoginView,LogoutView, ResetPasswordView, UserListView, UserDetailView, UserRoleListView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    #--- AUTH
    path('auth/login', LoginView.as_view(), name='jwt_login'),
    path('auth/refresh', CustomRefreshView.as_view(), name='custom_token_refresh'),
    path('auth/forgot-password', ForgotPasswordView.as_view(), name='forgot_password'),
    path('auth/reset-password', ResetPasswordView.as_view(), name='reset_password'),
    path('auth/logout', LogoutView.as_view(), name='logout'),

    #--- USER MANAGEMENT
    path('', UserListView.as_view(), name='user-list-create'),
    path('<int:pk>', UserDetailView.as_view(), name='user-detail'),
    
    #-- USER ROLES
    path('role/', UserRoleListView.as_view(), name='user-role-list-create'),
]
