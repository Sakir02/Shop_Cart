#!/bin/bash

echo "Installing project dependencies..."
pip install -r requirements.txt

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Loading initial product data if needed..."
python manage.py shell -c "from main.models import Product; exit(0) if Product.objects.count() == 0 else exit(1)" 2>&1 && \
    python manage.py loaddata initial_data.json --ignorenonexistent || \
    echo "Products already exist in database, skipping data load..."

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear