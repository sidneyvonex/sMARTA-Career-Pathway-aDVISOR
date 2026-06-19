import logging

logger = logging.getLogger(__name__)


def log_action(*, actor, action, target_type, target_id, details=None, request=None):
    from .models import AuditLog

    ip = None
    if request:
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        ip = forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')

    try:
        AuditLog.objects.create(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details or {},
            ip_address=ip,
        )
    except Exception:
        logger.exception('Failed to create audit log entry: action=%s target=%s/%s', action, target_type, target_id)
