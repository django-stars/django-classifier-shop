#!/bin/sh

while ! nc -z elasticsearch 9200; do sleep 3s; done

if [ ! -f .initial_lock ]; then
    python manage.py loaddata fixtures/initial.json
    python manage.py rebuild_index
    touch .initial_lock
fi

python manage.py runserver 0.0.0.0:8000
