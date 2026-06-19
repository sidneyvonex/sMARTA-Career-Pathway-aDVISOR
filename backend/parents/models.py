from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ParentStudentLink(models.Model):
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
