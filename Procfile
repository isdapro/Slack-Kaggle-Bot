web: gunicorn slackkaggle.wsgi --log-file -
main_worker: celery -A slackkaggle worker --beat --loglevel=info
