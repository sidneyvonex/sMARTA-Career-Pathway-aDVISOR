from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ParentStudentLink(models.Model):
    RELATIONSHIP_MOTHER = 'mother'
    RELATIONSHIP_FATHER = 'father'
    RELATIONSHIP_GUARDIAN = 'guardian'
    RELATIONSHIP_RELATIVE = 'relative'
    RELATIONSHIP_OTHER = 'other'
    RELATIONSHIP_CHOICES = [
        (RELATIONSHIP_MOTHER, 'Mother'),
        (RELATIONSHIP_FATHER, 'Father'),
        (RELATIONSHIP_GUARDIAN, 'Guardian'),
        (RELATIONSHIP_RELATIVE, 'Other relative'),
        (RELATIONSHIP_OTHER, 'Other'),
    ]

    STATUS_INVITED = 'invited'
    STATUS_PENDING = 'pending_learner'
    STATUS_ACTIVE = 'active'
    STATUS_REVOKED = 'revoked'
    STATUS_CHOICES = [
        (STATUS_INVITED, 'Invited'),
        (STATUS_PENDING, 'Pending learner approval'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_REVOKED, 'Revoked'),
    ]

    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='linked_children',
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='linked_parents',
    )
    claimed_relationship = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_CHOICES,
        default=RELATIONSHIP_GUARDIAN,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    learner_approved_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('parent', 'student')
        ordering = ['-created_at']

    def clean(self):
        if self.parent_id and self.parent.role != 'parent':
            raise ValidationError({'parent': 'Must have the parent role.'})
        if self.student_id and self.student.role != 'student':
            raise ValidationError({'student': 'Must have the student role.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        p = f'{self.parent.first_name} {self.parent.last_name}'.strip()
        s = f'{self.student.first_name} {self.student.last_name}'.strip()
        return f'{p} → {s}'
