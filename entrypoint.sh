#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Running migrations..."
python manage.py migrate --no-input

echo "Collecting static files..."
python manage.py collectstatic --no-input

# Execute the CMD from the Dockerfile
exec "$@"
