web: gunicorn app.routes:app

worker: celery -A app.tasks worker --loglevel=info