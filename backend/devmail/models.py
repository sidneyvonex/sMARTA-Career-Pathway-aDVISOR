from django.db import models


class CapturedEmail(models.Model):
    """A single outgoing email captured for the local dev mailbox.

    Only written by DevMailBackend under development settings. This table
    does not exist in production (the app is not installed there).
    """

    to_email = models.CharField(max_length=500)
    from_email = models.CharField(max_length=255)
    subject = models.CharField(max_length=500)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} -> {self.to_email}'
