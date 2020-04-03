web: gunicorn slackkaggle.wsgi --log-file -
worker: python manage.py celery worker --loglevel=info
beat: python manage.py celery beat --loglevel=info
