from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Placeholder custom user model.

    Fleshed out in Task 2; exists here only so AUTH_USER_MODEL = "users.User"
    (set in Task 1) resolves and `manage.py check` can pass.
    """

    pass
