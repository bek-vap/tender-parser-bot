#!/bin/bash

# Start Celery worker and beat for Tender Intelligence Platform
echo "Starting Celery worker and beat..."

# Kill any existing Celery processes
pkill -f "celery worker" 2>/dev/null
pkill -f "celery beat" 2>/dev/null

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A app.workers.celery_app worker --loglevel=info --detach

# Start Celery beat in background
echo "Starting Celery beat..."
celery -A app.workers.celery_app beat --loglevel=info --detach

echo "Celery worker and beat started successfully!"
echo "Check logs with: celery -A app.workers.celery_app events"
