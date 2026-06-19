from django.conf import settings
from django.db import models


ACTION_CHOICES = [
    ('user_registered', 'User registered'),
    ('email_verified', 'Email verified'),
    ('password_reset', 'Password reset'),
    ('account_deactivated', 'Account deactivated'),
    ('account_activated', 'Account activated'),
    ('invite_sent', 'Invite sent'),
    ('invite_accepted', 'Invite accepted'),
    ('school_created', 'School created'),
    ('school_edited', 'School edited'),
    ('school_deactivated', 'School deactivated'),
    ('school_activated', 'School activated'),
    ('counselor_added', 'Counselor added to school'),
    ('counselor_removed', 'Counselor removed from school'),
    ('counselor_assigned', 'Counselor assigned to student'),
]

TARGET_TYPE_CHOICES = [
    ('user', 'User'),
    ('school', 'School'),
    ('assignment', 'Assignment'),
]


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_actions',
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=20, choices=TARGET_TYPE_CHOICES)
    target_id = models.PositiveIntegerField()
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['actor', 'created_at']),
            models.Index(fields=['target_type', 'target_id']),
        ]

    def __str__(self):
        return f'{self.action} by {self.actor_id} at {self.created_at}'
