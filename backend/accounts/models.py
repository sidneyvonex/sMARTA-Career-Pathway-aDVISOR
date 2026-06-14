from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import CustomUserManager

COUNTY_CHOICES = [
    ('kiambu', 'Kiambu'),
    ('muranga', "Murang'a"),
    ('nyeri', 'Nyeri'),
    ('kirinyaga', 'Kirinyaga'),
    ('nyandarua', 'Nyandarua'),
]

ROLE_CHOICES = [
    ('student', 'Student'),
    ('counselor', 'Counselor'),
    ('school_admin', 'School Admin'),
    ('parent', 'Parent'),
    ('system_admin', 'System Admin'),
]


class User(AbstractUser):
    username = None
    date_joined = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    county = models.CharField(max_length=20, choices=COUNTY_CHOICES, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email
