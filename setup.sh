#!/bin/bash

set -e  # Exit on any error

echo "🚀 Starting setup for Budget System..."

# Check if .env exists, if not create from example
if [ ! -f .env ]; then
    echo "📝 Creating .env file from env.example..."
    cp env.example .env
    echo "✅ .env file created!"
else
    echo "✅ .env file already exists"
fi

# Create logs directory if it doesn't exist
if [ ! -d logs ]; then
    echo "📁 Creating logs directory..."
    mkdir -p logs
    echo "✅ Logs directory created!"
fi

# Check if virtual environment exists
if [ ! -d venv ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created!"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed!"

# Start Docker containers
echo "🐳 Starting Docker containers..."
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

# Run Django migrations
echo "🗄️ Running Django migrations..."
python manage.py migrate
echo "✅ Migrations completed!"

# Create superuser if it doesn't exist
echo "👤 Creating superuser (admin/admin123)..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created successfully!')
else:
    print('Superuser already exists!')
"

echo "✅ Setup completed successfully!"
echo ""
echo "🎉 Your Budget System is ready!"
echo "📊 Admin panel: http://localhost:8000/admin"
echo "👤 Username: admin"
echo "🔑 Password: admin123"
echo ""
echo "🚀 Run './run_all.sh' to start all services" 