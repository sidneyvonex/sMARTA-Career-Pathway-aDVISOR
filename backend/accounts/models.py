from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
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
    school = models.ForeignKey(
        'School', on_delete=models.SET_NULL, null=True, blank=True, related_name='staff'
    )
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
    VERIFICATION_UNVERIFIED = 'unverified'
    VERIFICATION_VERIFIED = 'verified'
    VERIFICATION_DEMONSTRATION = 'demonstration'
    VERIFICATION_STATUS_CHOICES = [
        (VERIFICATION_UNVERIFIED, 'Unverified'),
        (VERIFICATION_VERIFIED, 'Verified'),
        (VERIFICATION_DEMONSTRATION, 'Demonstration'),
    ]

    name = models.CharField(max_length=200)
    county = models.CharField(max_length=20, choices=COUNTY_CHOICES)
    school_code = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
    )
    source_record_id = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
    )
    sub_county = models.CharField(max_length=100, blank=True, default='')
    gender = models.CharField(max_length=20, blank=True, default='')
    cluster = models.CharField(max_length=10, blank=True, default='')
    accommodation_type = models.CharField(max_length=30, blank=True, default='')
    institution_type = models.CharField(max_length=30, blank=True, default='')
    school_category = models.CharField(max_length=30, blank=True, default='')
    logo_url = models.URLField(max_length=500, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default=VERIFICATION_UNVERIFIED,
    )
    source_url = models.URLField(max_length=500, blank=True, default='')
    source_checked_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        identifier = self.school_code or self.source_record_id or 'unidentified'
        return f"{self.name} ({identifier})"


class StudentProfile(models.Model):
    MODE_CHOICES = [('self_guided', 'Self-Guided'), ('school_linked', 'School-Linked')]
    GRADE_CHOICES = [
        (9, 'Grade 9'),
        (10, 'Grade 10'),
        (11, 'Grade 11'),
        (12, 'Grade 12'),
    ]
    SCHOOL_MEMBERSHIP_STATUS_CHOICES = [
        ('not_applicable', 'Not Applicable'),
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('rejected', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)
    school_membership_status = models.CharField(
        max_length=20,
        choices=SCHOOL_MEMBERSHIP_STATUS_CHOICES,
        default='not_applicable',
    )
    grade = models.IntegerField(choices=GRADE_CHOICES)
    bio = models.TextField(blank=True, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    career_interests = models.TextField(blank=True, default='')
    photo_url = models.URLField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - Grade {self.grade}"


class StudentSchoolMembership(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_REJECTED = 'rejected'
    STATUS_ENDED = 'ended'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Approval'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_ENDED, 'Ended'),
    ]

    student_profile = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='school_memberships',
    )
    school = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name='student_memberships',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    active_identity_key = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        editable=False,
    )
    pending_identity_key = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        editable=False,
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='decided_student_school_memberships',
    )

    class Meta:
        ordering = ['-requested_at', '-pk']
        constraints = [
            models.UniqueConstraint(
                fields=['active_identity_key'],
                name='accounts_membership_active_uniq',
            ),
            models.UniqueConstraint(
                fields=['pending_identity_key'],
                name='accounts_membership_pending_uniq',
            ),
            models.CheckConstraint(
                check=(
                    models.Q(
                        status='active',
                        active_identity_key=models.F('student_profile_id'),
                    )
                    | (
                        ~models.Q(status='active')
                        & models.Q(active_identity_key__isnull=True)
                    )
                ),
                name='accounts_membership_active_key_ck',
            ),
            models.CheckConstraint(
                check=(
                    models.Q(
                        status='pending',
                        pending_identity_key=models.F('student_profile_id'),
                    )
                    | (
                        ~models.Q(status='pending')
                        & models.Q(pending_identity_key__isnull=True)
                    )
                ),
                name='accounts_membership_pending_key_ck',
            ),
        ]

    def __str__(self):
        return (
            f'{self.student_profile.user.email} — '
            f'{self.school.name} ({self.status})'
        )

    def save(self, *args, **kwargs):
        self.active_identity_key = (
            self.student_profile_id
            if self.status == self.STATUS_ACTIVE
            else None
        )
        self.pending_identity_key = (
            self.student_profile_id
            if self.status == self.STATUS_PENDING
            else None
        )
        if kwargs.get('update_fields') is not None:
            kwargs['update_fields'] = set(kwargs['update_fields']) | {
                'active_identity_key',
                'pending_identity_key',
            }
        return super().save(*args, **kwargs)

    def activate(self, *, decided_by):
        now = timezone.now()
        self.status = self.STATUS_ACTIVE
        self.decided_by = decided_by
        self.decided_at = now
        self.started_at = now
        self.ended_at = None
        self.save(
            update_fields=[
                'status',
                'decided_by',
                'decided_at',
                'started_at',
                'ended_at',
            ]
        )

    def reject(self, *, decided_by):
        self.status = self.STATUS_REJECTED
        self.decided_by = decided_by
        self.decided_at = timezone.now()
        self.save(update_fields=['status', 'decided_by', 'decided_at'])

    def end(self):
        self.status = self.STATUS_ENDED
        self.ended_at = timezone.now()
        self.save(update_fields=['status', 'ended_at'])
