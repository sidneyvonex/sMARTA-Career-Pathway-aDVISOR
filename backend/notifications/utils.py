from .models import Notification


def create_notification(user, type_code, message):
    """Create a single in-app notification for a user. Returns the created instance."""
    return Notification.objects.create(user=user, type=type_code, message=message)
