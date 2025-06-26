"""
Celery configuration for budget_system project.
"""

import os
from celery import Celery
from typing import Any

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budget_system.settings')

app: Celery = Celery('budget_system')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)  # type: ignore[misc]
def debug_task(self: Any) -> str:
    """Debug task to test Celery configuration."""
    print(f'Request: {self.request!r}')
    return 'Celery is working!' 