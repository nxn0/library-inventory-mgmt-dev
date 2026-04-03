import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vp.settings')

app = Celery('vp')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Optional schedule for recurring jobs.
app.conf.beat_schedule = {
    'cleanup-expired-sessions-every-day': {
        'task': 'models.tasks.cleanup_expired_sessions',
        'schedule': 86400.0,  # 24 hours
    },
    'track-overdue-books-every-day': {
        'task': 'models.tasks.track_overdue_books',
        'schedule': 86400.0,  # 24 hours
    },
    'cleanup-expired-bans-every-day': {
        'task': 'models.tasks.cleanup_expired_bans',
        'schedule': 86400.0,  # 24 hours
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
