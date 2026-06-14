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


class School(models.Model):
    name = models.CharField(max_length=200)
    county = models.CharField(max_length=20, choices=COUNTY_CHOICES)
    school_code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.school_code})"


class StudentProfile(models.Model):
    MODE_CHOICES = [('self_guided', 'Self-Guided'), ('school_linked', 'School-Linked')]
    GRADE_CHOICES = [(9, 'Grade 9'), (10, 'Grade 10')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)
    grade = models.IntegerField(choices=GRADE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - Grade {self.grade}"
