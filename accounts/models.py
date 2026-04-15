from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

# 🔥 Custom User Manager
class AccountManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user
    

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)


# 🔥 Custom User Model
class Account(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(max_length=100, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    phone_number = models.CharField(max_length=50, blank=True)
    

    # 🔐 Roles
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('instructor', 'Instructor'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    # 🔄 Meta fields
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    # 🔑 Permissions
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # 🔥 Required settings
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # 🔗 Manager
    objects = AccountManager()

    def __str__(self):
        return self.email
    

class UserToken(models.Model):

    TOKEN_TYPE_CHOICES = (
        ('reset_password', 'Reset Password'),
        ('email_verification', 'Email Verification'),
    )

    user = models.ForeignKey('Account', on_delete=models.CASCADE,related_name="tokens")
    token = models.CharField(max_length=255)
    token_type = models.CharField(max_length=50, choices=TOKEN_TYPE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user.email} - {self.token_type}"