#!/bin/bash

set -e  # Exit on any error

echo "🚀 Starting Budget System..."

# Check if .env exists, if not run setup
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "🔧 Running setup first..."
    chmod +x setup.sh
    ./setup.sh
fi

# Activate the virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if Docker containers are running
echo "🐳 Checking Docker containers..."
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Docker containers are not running!"
    echo "🔧 Starting Docker containers..."
    docker-compose up -d
    
    # Wait for PostgreSQL to be ready
    echo "⏳ Waiting for PostgreSQL to be ready..."
    until docker-compose exec -T postgres pg_isready -U budget_user -d budget_system; do
        echo "Waiting for PostgreSQL..."
        sleep 2
    done
    echo "✅ PostgreSQL is ready!"
    
    # Wait for Redis to be ready
    echo "⏳ Waiting for Redis to be ready..."
    until docker-compose exec -T redis redis-cli ping; do
        echo "Waiting for Redis..."
        sleep 2
    done
    echo "✅ Redis is ready!"
    
    # Run migrations to ensure database is up to date
    echo "🗄️ Running migrations..."
    python manage.py migrate
    echo "✅ Migrations completed!"
else
    echo "✅ Docker containers are running!"
fi

# Check if Redis is accessible from Django
echo "🔍 Checking Redis connection..."
if ! python -c "import redis; redis.Redis(host='localhost', port=6379, db=0).ping()" 2>/dev/null; then
    echo "❌ Redis is not accessible from Django!"
    echo "Please check if Redis is running and accessible on localhost:6379"
    exit 1
fi

echo "✅ Redis is accessible!"

# Start Django server
echo "🚀 Starting Django..."
python manage.py runserver 0.0.0.0:8000 &
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
echo "📊 Admin: http://localhost:8000/admin (admin/admin123)"
echo "🔧 Celery Worker: PID $CELERY_WORKER_PID"
echo "⏰ Celery Beat: PID $CELERY_BEAT_PID"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $DJANGO_PID $CELERY_WORKER_PID $CELERY_BEAT_PID 2>/dev/null || true
    echo "✅ All services stopped!"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Wait for the processes
wait $DJANGO_PID $CELERY_WORKER_PID $CELERY_BEAT_PID 