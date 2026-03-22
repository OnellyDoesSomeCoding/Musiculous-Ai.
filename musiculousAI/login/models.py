from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model for future profile/auth extensions."""
