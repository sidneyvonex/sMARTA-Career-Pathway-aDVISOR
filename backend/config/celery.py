from celery import Celery

app = Celery('cbc_guidance')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
