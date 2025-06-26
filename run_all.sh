#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Check if Redis is running
echo "Checking if Redis is running..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running!"
    echo "Please start Redis first:"
    echo "  Mac: brew services start redis"
    echo "  Ubuntu: sudo service redis-server start"
    echo "  Docker: docker run -d -p 6379:6379 redis:alpine"
    echo ""
    echo "Or install Redis if you don't have it yet:"
    echo "  Mac: brew install redis"
    echo "  Ubuntu: sudo apt-get install redis-server"
    exit 1
fi

echo "✅ Redis is running!"

# Start Django server
echo "🚀 Starting Django..."
python manage.py runserver 0.0.0.0:8000
DJANGO_PID=$!

# Start Celery worker
echo "🔧 Starting Celery Worker..."
celery -A budget_system worker -l info &
CELERY_WORKER_PID=$!

# Start Celery beat
echo "⏰ Starting Celery Beat..."
celery -A budget_system beat -l info &
CELERY_BEAT_PID=$!

echo "✅ All services started!"
echo "🌐 Django: http://localhost:8000"
echo "🔧 Celery Worker: PID $CELERY_WORKER_PID"
echo "⏰ Celery Beat: PID $CELERY_BEAT_PID"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for the processes
wait $DJANGO_PID $CELERY_WORKER_PID $CELERY_BEAT_PID 