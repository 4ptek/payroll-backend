# users/authentication.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from users.models import Users

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_id = validated_token['user_id']
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            raise AuthenticationFailed("User not found", code="user_not_found")
        
        if not user.isactive:
            raise AuthenticationFailed("User is inactive", code="user_inactive")

        if user.isdelete:
            raise AuthenticationFailed("User account is deleted", code="user_deleted")
        
        user.is_authenticated = True 
        return user