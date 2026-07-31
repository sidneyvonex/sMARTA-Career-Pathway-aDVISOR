from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import StudentProfile, School


class CounselorAssignment(models.Model):
    counselor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_assignments'
    )
    student_profile = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name='counselor_assignments'
    )
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name='counselor_assignments'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student_profile'],
                condition=models.Q(is_active=True),
                name='unique_active_assignment_per_student',
            )
        ]
        ordering = ['-assigned_at']

    def __str__(self):
        return f'{self.counselor.email} → {self.student_profile}'


class CounselorNote(models.Model):
    counselor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='counselor_notes_written'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='counselor_notes_received'
    )
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    visible_to_parent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Note by {self.counselor.email} for {self.student.email}'


class CounselorIntervention(models.Model):
    CATEGORY_ASSESSMENT = 'assessment'
    CATEGORY_ACADEMIC_EVIDENCE = 'academic_evidence'
    CATEGORY_COMBINATION = 'combination'
    CATEGORY_PLAN = 'plan'
    CATEGORY_FOLLOW_UP = 'follow_up'
    CATEGORY_OTHER = 'other'
    CATEGORY_CHOICES = [
        (CATEGORY_ASSESSMENT, 'Interest assessment'),
        (CATEGORY_ACADEMIC_EVIDENCE, 'Academic evidence'),
        (CATEGORY_COMBINATION, 'Subject combination'),
        (CATEGORY_PLAN, 'Learner plan'),
        (CATEGORY_FOLLOW_UP, 'Follow-up'),
        (CATEGORY_OTHER, 'Other'),
    ]

    STATUS_OPEN = 'open'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    counselor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='counselor_interventions_written',
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='counselor_interventions_received',
    )
    category = models.CharField(max_length=24, choices=CATEGORY_CHOICES)
    action_agreed = models.TextField(max_length=2000)
    follow_up_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN,
    )
    learner_visible = models.BooleanField(default=True)
    parent_visible = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['status', 'follow_up_date', '-updated_at']
        indexes = [
            models.Index(
                fields=['counselor', 'status', 'follow_up_date'],
                name='counselor_follow_up_idx',
            ),
            models.Index(
                fields=['student', 'learner_visible'],
                name='student_visible_action_idx',
            ),
        ]

    def save(self, *args, **kwargs):
        if self.status == self.STATUS_COMPLETED:
            if self.completed_at is None:
                self.completed_at = timezone.now()
        else:
            self.completed_at = None

        update_fields = kwargs.get('update_fields')
        if update_fields is not None:
            kwargs['update_fields'] = set(update_fields) | {'completed_at'}
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f'{self.get_category_display()} for {self.student.email} '
            f'({self.status})'
        )
