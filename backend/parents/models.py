from django.conf import settings
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

    def __str__(self):
        p = f'{self.parent.first_name} {self.parent.last_name}'.strip()
        s = f'{self.student.first_name} {self.student.last_name}'.strip()
        return f'{p} → {s}'
