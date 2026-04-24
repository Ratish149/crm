#!/bin/bash

# Export environment variables for cron to use
printenv | grep -v "no_proxy" >> /etc/environment

# Start cron daemon in the background
service cron start

# Collect static files
python manage.py collectstatic --noinput

# Run the web server
gunicorn crm.wsgi:application --bind 0.0.0.0:8000
