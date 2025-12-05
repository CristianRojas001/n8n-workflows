"""
Celery Configuration for InfoSubvenciones Ingestion Pipeline

This module configures Celery with 3 queues:
- fetcher: For API data fetching tasks
- processor: For PDF processing tasks (Week 2)
- embedder: For embedding generation tasks (Week 2-3)

Redis is used as the message broker and result backend.
"""

from celery import Celery
from kombu import Queue
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Redis URL from environment (default for local development)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
app = Celery(
    'infosubvenciones_ingestion',
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Celery configuration
app.conf.update(
    # Task routing - define which tasks go to which queue
    task_routes={
        'tasks.fetcher.*': {'queue': 'fetcher'},
        'tasks.processor.*': {'queue': 'processor'},
        'tasks.embedder.*': {'queue': 'embedder'},
    },

    # Define queues
    task_queues=(
        Queue('fetcher', routing_key='fetcher'),
        Queue('processor', routing_key='processor'),
        Queue('embedder', routing_key='embedder'),
    ),

    # Task execution settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Madrid',  # Spain timezone for InfoSubvenciones
    enable_utc=True,

    # Task result settings
    result_expires=3600,  # Results expire after 1 hour

    # Worker settings
    worker_prefetch_multiplier=4,  # Number of tasks to prefetch
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (prevent memory leaks)

    # Retry settings
    task_acks_late=True,  # Acknowledge task after execution (not before)
    task_reject_on_worker_lost=True,  # Reject task if worker dies

    # Rate limiting
    task_default_rate_limit='100/m',  # Max 100 tasks per minute (API friendly)

    # Task time limits
    task_soft_time_limit=300,  # Soft timeout: 5 minutes
    task_time_limit=600,  # Hard timeout: 10 minutes

    # Logging
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

# Auto-discover tasks in the tasks/ directory
app.autodiscover_tasks(['tasks'])

# Task base configuration
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working"""
    print(f'Request: {self.request!r}')


if __name__ == '__main__':
    app.start()
