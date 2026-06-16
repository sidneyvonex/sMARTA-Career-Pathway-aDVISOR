from django.conf import settings
from django.db import models

TYPE_CHOICES = [
    ('assessment_submitted', 'Assessment Submitted'),
    ('counselor_note', 'Counselor Note'),
    ('parent_linked', 'Parent Linked'),
    ('counselor_assigned', 'Counselor Assigned'),
]


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'read'], name='notifications_user_read_idx'),
            models.Index(fields=['user', '-created_at'], name='notifications_user_created_idx'),
        ]

    def __str__(self):
        return f"[{self.type}] {self.user.email} — {'read' if self.read else 'unread'}"
