from django.core.mail.backends.base import BaseEmailBackend

from .models import CapturedEmail


class DevMailBackend(BaseEmailBackend):
    """Persist outgoing email into CapturedEmail for the local dev mailbox.

    Wired as EMAIL_BACKEND under development settings only. Every send_mail()
    call flows through send_messages(), so all email types are captured with
    no changes to the sending code.
    """

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        count = 0
        for message in email_messages:
            try:
                CapturedEmail.objects.create(
                    to_email=', '.join(message.to),
                    from_email=message.from_email,
                    subject=message.subject,
                    body=message.body,
                )
                count += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return count
