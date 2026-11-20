#!/bin/bash

# Export environment variables for cron to use
printenv | grep -v "no_proxy" >> /etc/environment

# Start cron daemon in the background
service cron start

# Collect static files
python manage.py collectstatic --noinput

python manage.py migrate --noinput

# Run the web server
daphne -b 0.0.0.0 -p 8000 crm.asgi:application
