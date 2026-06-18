from django.db import models
from django.conf import settings
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
