"""
Script to start Celery worker for InfoSubvenciones ingestion.

This script provides an easy way to start the Celery worker with proper configuration.

Usage:
    # Start worker for all queues
    python scripts/start_celery_worker.py

    # Start worker for specific queue
    python scripts/start_celery_worker.py --queue fetcher

    # Or use celery command directly:
    celery -A config.celery_app worker --loglevel=info -Q fetcher,processor,embedder

Queues:
    - fetcher: Fetches data from InfoSubvenciones API
    - processor: Processes PDFs (Week 2)
    - embedder: Generates embeddings (Week 2-3)
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def start_worker(queue: str = None, loglevel: str = 'info'):
    """Start Celery worker."""
    from config.celery_app import app

    # Build worker arguments
    argv = [
        'worker',
        f'--loglevel={loglevel}',
    ]

    if queue:
        argv.append(f'-Q')
        argv.append(queue)
    else:
        # Default: all queues
        argv.append('-Q')
        argv.append('fetcher,processor,embedder')

    print("=" * 70)
    print("Starting Celery Worker")
    print("=" * 70)
    print(f"Broker: {app.conf.broker_url}")
    print(f"Queues: {queue if queue else 'fetcher,processor,embedder'}")
    print(f"Log level: {loglevel}")
    print("=" * 70)
    print("\nPress Ctrl+C to stop the worker\n")

    # Start worker
    app.worker_main(argv)


def main():
    parser = argparse.ArgumentParser(description='Start Celery worker')
    parser.add_argument('--queue', '-Q', type=str, help='Queue name (default: all queues)')
    parser.add_argument('--loglevel', '-l', type=str, default='info',
                        choices=['debug', 'info', 'warning', 'error'],
                        help='Log level (default: info)')

    args = parser.parse_args()

    try:
        start_worker(args.queue, args.loglevel)
    except KeyboardInterrupt:
        print("\n\nWorker stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
