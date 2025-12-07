from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from .models import Profile


class EmailOrUsernameModelBackend(ModelBackend):
    """Authentication backend which allows users to authenticate using either
    their username or their email address.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get('username') or kwargs.get('email')

        if username is None or password is None:
            return None

        # Try to fetch by username first, then by email (case-insensitive).
        # Use .first() to avoid MultipleObjectsReturned if duplicate emails exist.
        user = UserModel.objects.filter(username=username).first() or UserModel.objects.filter(email__iexact=username).order_by('id').first()
        
        if user is None:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
