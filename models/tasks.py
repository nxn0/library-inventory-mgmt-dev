"""
Celery tasks for background operations.
Handles cleanup of expired sessions and overdue book tracking.
"""
from celery import shared_task
from django.utils import timezone
from .user_utils import OverdueTracker


@shared_task
def cleanup_expired_sessions():
    """
    Delete expired anonymous user sessions (inactive for 30 days).
    Run hourly or daily based on Celery beat schedule.
    """
    count = OverdueTracker.cleanup_expired_sessions()
    return f"Cleaned up {count} expired sessions"


@shared_task
def track_overdue_books():
    """
    Track overdue books and move old ones to the unencrypted database.
    Run daily or weekly based on Celery beat schedule.
    """
    OverdueTracker.check_overdue_transactions()
    return "Overdue books tracked and updated"


@shared_task
def cleanup_expired_bans():
    """
    Remove expired temporary bans.
    Run daily based on Celery beat schedule.
    """
    count = OverdueTracker.cleanup_expired_bans()
    return f"Cleaned up {count} expired bans"
