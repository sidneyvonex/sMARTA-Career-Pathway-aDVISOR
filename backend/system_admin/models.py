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
    ('school_admin_provisioned', 'School admin provisioned'),
    ('school_edited', 'School edited'),
    ('school_deactivated', 'School deactivated'),
    ('school_activated', 'School activated'),
    ('counselor_added', 'Counselor added to school'),
    ('counselor_removed', 'Counselor removed from school'),
    ('counselor_assigned', 'Counselor assigned to student'),
    ('students_bulk_imported', 'Students bulk imported'),
    ('grade_verified', 'Grade verified'),
    ('grade_verification_removed', 'Grade verification removed'),
    ('school_marks_imported', 'School marks imported'),
    ('grade_definition_snapshot_rewritten', 'Grade definition snapshot rewritten'),
    ('school_membership_approved', 'School membership approved'),
    ('school_membership_rejected', 'School membership rejected'),
    (
        'framework_combination_status_changed',
        'Framework combination status changed',
    ),
    ('parent_link_approved', 'Parent link approved'),
    ('parent_link_revoked', 'Parent link revoked'),
    (
        'provisional_combination_changed',
        'Provisional combination changed',
    ),
    ('plan_review_status_changed', 'Plan review status changed'),
    ('report_downloaded', 'Report downloaded'),
    ('school_offerings_changed', 'School offerings changed'),
]

TARGET_TYPE_CHOICES = [
    ('user', 'User'),
    ('school', 'School'),
    ('assignment', 'Assignment'),
    ('grade', 'Grade'),
    ('combination', 'Combination'),
    ('parent_link', 'Parent link'),
    ('choice', 'Choice'),
    ('plan', 'Plan'),
    ('report', 'Report'),
    ('offering', 'Offering'),
    ('period', 'Academic period'),
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
