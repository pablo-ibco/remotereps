# Budget Management System (Django + Celery + PostgreSQL/Redis)

## Overview
A comprehensive backend system for ad agencies to manage daily/monthly budgets, campaign control, and dayparting. Built with Django, Celery, PostgreSQL, and Redis. The system automatically tracks ad spend, enforces budget rules, resets budgets, and respects campaign schedules.

For usage instructions, please refer to [USAGE.md](./USAGE.md)

---

## Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Data Models](#data-models)
- [Admin Panel Usage](#admin-panel-usage)
- [Management Commands](#management-commands)
- [Celery Tasks & Health Check](#celery-tasks--health-check)
- [Static Typing & Testing](#static-typing--testing)
- [Daily & Monthly Workflow](#daily--monthly-workflow)
- [Assumptions & Simplifications](#assumptions--simplifications)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Delivery Checklist](#delivery-checklist)
- [Pseudo-code](#pseudo-code)
- [REST API Usage Examples](#rest-api-usage-examples)
- [Running All Tests](#running-all-tests)

---

## Features
- **Automatic daily and monthly ad spend tracking** per brand and campaign
- **Intelligent budget enforcement** - automatically pauses campaigns when budgets are exceeded
- **Scheduled budget resets** at the start of each day/month with campaign reactivation
- **Advanced dayparting** - campaigns only run during allowed hours and days
- **Comprehensive admin panel** for full system management
- **Management commands** for manual enforcement and resets
- **Celery periodic tasks** for complete automation
- **Static typing** throughout the codebase (PEP 484, MyPy)
- **System health monitoring** with detailed status checks
- **PostgreSQL database** for production-ready data storage
- **Docker support** for easy deployment and development
- **One-command setup** - everything runs with a single script

---

## Project Structure
```
remotereps/
├── brands/         # Brand models and admin interface
├── campaigns/      # Campaign models and admin interface
├── spending/       # Spend tracking models, services, and admin
├── scheduling/     # Schedule models, services, and admin
├── tasks/          # Celery background tasks
├── budget_system/  # Django project settings and configuration
├── manage.py       # Django management entrypoint
├── docker-compose.yml  # PostgreSQL and Redis containers
├── setup.sh        # Automated environment setup script
├── run_all.sh      # Complete system startup script
├── run_tests.sh    # Test execution script
├── README.md       # This documentation
├── PSEUDOCODE.md   # High-level system architecture
├── API.md          # API documentation
└── requirements.txt # Python dependencies
```

---

## Quick Start

### 🚀 One-Command Setup (Recommended)

The system now includes complete automation. Just run:

```bash
./run_all.sh
```

This single command will:
1. ✅ Create `.env` file from `.env.example` if needed
2. ✅ Set up virtual environment if needed
3. ✅ Install all Python dependencies
4. ✅ Start PostgreSQL and Redis containers
5. ✅ Wait for services to be ready
6. ✅ Run database migrations
7. ✅ Create admin user (admin/admin123)
8. ✅ Start Django server, Celery worker, and Celery beat
9. ✅ Display access URLs and credentials

### 📊 Access the System

After running `./run_all.sh`, you can access:

- **Django Admin**: http://localhost:8000/admin
  - Username: `admin`
  - Password: `admin123`
- **Django Server**: http://localhost:8000
- **API Endpoints**: http://localhost:8000/api/
- **Swagger Documentation**: http://localhost:8000/api/docs

### 🔧 Manual Setup (Alternative)

If you prefer manual control, you can run setup steps individually:

```bash
# 1. Set up environment
./setup.sh

# 2. Start all services
./run_all.sh
```

### 🗄️ Database Options

The system supports both PostgreSQL (recommended) and SQLite:

#### PostgreSQL (Docker - Default)
- Automatically configured in `docker-compose.yml`
- Production-ready with proper indexing
- Concurrent access support

#### SQLite (Local)
- Edit `.env` and set: `DB_ENGINE=django.db.backends.sqlite3`
- Remove database variables to use SQLite defaults
- Good for development and testing

---

## Data Models

### Core Entities
- **Brand**: name, daily_budget, monthly_budget
- **Campaign**: belongs to Brand, has status (active/paused), daily/monthly spend tracking, pause reason
- **Spend**: campaign, amount, date, type (daily/monthly), description
- **Schedule**: campaign, day_of_week, start_time, end_time, is_active

### Relationships
- Brands have multiple campaigns
- Campaigns belong to one brand
- Campaigns have multiple spends and schedules
- All models include audit fields (created_at, updated_at)

See [PSEUDOCODE.md](./PSEUDOCODE.md) for a high-level, language-agnostic overview and business logic.

---

## Admin Panel Usage

### Access
- **URL**: http://localhost:8000/admin
- **Credentials**: admin / admin123

### Management Features
- **Brands**: Create/edit brands and set daily/monthly budgets
- **Campaigns**: Assign to brands, set status, view spend, pause/activate campaigns
- **Spends**: View all spend records, filter by campaign/brand/date, add manual spends
- **Schedules**: Set dayparting rules (days/times when campaigns are allowed to run)
- **Visual Indicators**: All models have color-coded budget/spend indicators for quick status assessment

### Key Admin Actions
- Monitor budget vs spend in real-time
- Manually pause/activate campaigns
- Add emergency spends or budget adjustments
- Configure dayparting schedules
- View system logs and audit trails

---

## Management Commands

Run with `python manage.py <command>`

### Budget Enforcement
Pauses campaigns that exceed daily/monthly budgets:
```bash
python manage.py enforce_budgets
```

### Dayparting Enforcement
Pauses/activates campaigns based on their schedule:
```bash
python manage.py enforce_dayparting
```

### Spend Reset
Resets daily/monthly spends and reactivates eligible campaigns:
```bash
# Daily reset
python manage.py reset_spends --daily

# Monthly reset
python manage.py reset_spends --monthly

# Both daily and monthly
python manage.py reset_spends --both
```

### Example Output
```
INFO Starting budget enforcement
INFO Budget enforcement completed: {'checked': 2, 'paused_daily': 1, 'paused_monthly': 0, 'errors': 0}
```

---

## Celery Tasks & Health Check

Celery automates all enforcement and reset operations. Tasks are scheduled via Celery Beat.

### Scheduled Tasks
- **Budget enforcement**: Every 5 minutes
- **Dayparting enforcement**: Every minute
- **Daily reset**: Every day at 00:00 UTC
- **Monthly reset**: 1st day of month at 00:00 UTC

### Health Check
Check system health (database, campaigns, services):
```bash
python manage.py shell -c "from tasks.budget_tasks import health_check_task; print(health_check_task())"
```

### Example Health Check Output
```json
{
  "timestamp": "2024-06-26T21:54:39Z",
  "status": "healthy",
  "checks": {
    "database": {"status": "healthy", "connection": "ok"},
    "campaigns": {"status": "healthy", "active": 5, "paused": 2},
    "services": {"status": "healthy", "celery": "running", "redis": "connected"}
  }
}
```

---

## Static Typing & Testing

### Type Safety
- All code uses Python type hints (PEP 484)
- MyPy configuration: `mypy.ini`
- Zero type errors enforced

### Type Checking
```bash
mypy .
```

### Testing
```bash
# Run all tests
./run_tests.sh

# Run specific test modules
python manage.py test brands
python manage.py test campaigns
python manage.py test spending
python manage.py test scheduling

# Run system integration test
python test_system.py

# Run API tests
python manage.py test test_api_endpoints
```

---

## Daily & Monthly Workflow

### Automated Process
1. **Every minute**: Dayparting enforcement (pauses/activates campaigns by schedule)
2. **Every 5 minutes**: Budget enforcement (pauses campaigns that exceed budgets)
3. **00:00 daily**: Resets daily spends, reactivates eligible campaigns
4. **00:00 on 1st of month**: Resets monthly spends, reactivates eligible campaigns

### Manual Actions
- All automated actions can be triggered manually via management commands
- Admin panel provides real-time control and monitoring
- Emergency overrides available for urgent situations

---

## Assumptions & Simplifications

### System Design
- All times are UTC for consistency
- Spending is tracked with cent precision (2 decimal places)
- No real-time notifications (comprehensive logging instead)
- PostgreSQL by default, with SQLite fallback
- REST API available for integration
- Celery + Redis for background task processing

### Business Rules
- Budgets are soft limits (can be exceeded with manual intervention)
- Dayparting is enforced automatically
- Campaign status changes are logged for audit
- No automatic budget increases or alerts

---

## Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check if containers are running
docker-compose ps

# Restart containers
docker-compose down && docker-compose up -d

# Check logs
docker-compose logs postgres
docker-compose logs redis
```

#### Database Connection Issues
```bash
# Check database status
python manage.py dbshell

# Reset database (WARNING: loses data)
docker-compose down -v
docker-compose up -d
python manage.py migrate
```

#### Celery Issues
```bash
# Check Celery status
celery -A budget_system inspect active

# Restart Celery
pkill -f celery
./run_all.sh
```

#### Port Conflicts
- **Port 8000**: Change in `run_all.sh` or stop other Django servers
- **Port 5432**: Stop local PostgreSQL (`brew services stop postgresql`)
- **Port 6379**: Stop local Redis (`brew services stop redis`)

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
./run_all.sh
```

---

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Use static typing everywhere (PEP 484)
4. Run tests before submitting: `./run_tests.sh`
5. Run type checking: `mypy .`
6. Submit a pull request

### Code Standards
- All code must pass MyPy type checking
- Follow PEP 8 style guidelines
- Include type hints for all functions
- Write tests for new features
- Update documentation as needed

---

## Delivery Checklist

- [x] Pseudo-code architecture in `PSEUDOCODE.md`
- [x] Complete Django models and business logic
- [x] Celery tasks for automation
- [x] Management commands for manual control
- [x] Static typing throughout (PEP 484, MyPy)
- [x] Comprehensive README with setup and usage
- [x] REST API endpoints for all resources
- [x] Automated setup and deployment scripts
- [x] Health monitoring and status checks
- [x] Public GitHub repository

---

## Pseudo-code

See [PSEUDOCODE.md](./PSEUDOCODE.md) for a high-level, language-agnostic overview of the system architecture and business logic.

---

## REST API Usage Examples

The system provides comprehensive REST API endpoints for all resources. No authentication is required for demo purposes.

### Brands API

#### List All Brands
```bash
curl -X GET http://localhost:8000/api/brands/
```

#### Create a Brand
```bash
curl -X POST http://localhost:8000/api/brands/ \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Acme Corporation",
    "daily_budget": "100.00",
    "monthly_budget": "2000.00"
  }'
```

#### Get Brand by ID
```bash
curl -X GET http://localhost:8000/api/brands/<brand_id>/
```

#### Update Brand
```bash
curl -X PUT http://localhost:8000/api/brands/<brand_id>/ \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Acme Corp Updated",
    "daily_budget": "150.00",
    "monthly_budget": "3000.00"
  }'
```

#### Delete Brand
```bash
curl -X DELETE http://localhost:8000/api/brands/<brand_id>/
```

### Campaigns API

#### List All Campaigns
```bash
curl -X GET http://localhost:8000/api/campaigns/
```

#### Create a Campaign
```bash
curl -X POST http://localhost:8000/api/campaigns/ \
  -H 'Content-Type: application/json' \
  -d '{
    "brand": "<brand_id>",
    "name": "Summer Sale Campaign",
    "status": "ACTIVE"
  }'
```

#### Update Campaign Status
```bash
curl -X PATCH http://localhost:8000/api/campaigns/<campaign_id>/ \
  -H 'Content-Type: application/json' \
  -d '{"status": "PAUSED"}'
```

### Spends API

#### List All Spends
```bash
curl -X GET http://localhost:8000/api/spends/
```

#### Create a Spend
```bash
curl -X POST http://localhost:8000/api/spends/ \
  -H 'Content-Type: application/json' \
  -d '{
    "campaign": "<campaign_id>",
    "amount": "25.50",
    "spend_date": "2024-06-26",
    "spend_type": "DAILY",
    "description": "Facebook ad spend"
  }'
```

#### Filter Spends by Date Range
```bash
curl -X GET "http://localhost:8000/api/spends/?start_date=2024-06-01&end_date=2024-06-30"
```

### Schedules API

#### List All Schedules
```bash
curl -X GET http://localhost:8000/api/schedules/
```

#### Create a Schedule
```bash
curl -X POST http://localhost:8000/api/schedules/ \
  -H 'Content-Type: application/json' \
  -d '{
    "campaign": "<campaign_id>",
    "day_of_week": 1,
    "start_time": "09:00:00",
    "end_time": "18:00:00",
    "is_active": true
  }'
```

### API Documentation

For interactive API documentation, visit:
- **Swagger**: http://localhost:8000/api/docs
- **Schema Documentation**: http://localhost:8000/api/schema/

> **Note**: Replace `<brand_id>` and `<campaign_id>` with actual UUIDs from your database.

---

## Running All Tests

### Complete Test Suite

Run all unit, integration, and API tests:

```bash
./run_tests.sh
```

This script will:
- Activate the virtual environment
- Run all Django tests (including API and integration tests)
- Display a comprehensive summary of results

### Specific Test Categories

#### Run Tests by App
```bash
# Test specific apps
./run_tests.sh brands
./run_tests.sh campaigns
./run_tests.sh spending
./run_tests.sh scheduling
```

#### Run Specific Test Modules
```bash
# API endpoint tests
python manage.py test test_api_endpoints -v 2

# System integration test
python test_system.py

# Specific test classes
python manage.py test test_api_endpoints.BrandAPITests -v 2
python manage.py test test_api_endpoints.CampaignAPITests -v 2
```

#### Run Individual Test Methods
```bash
# Single test method
python manage.py test test_api_endpoints.BrandAPITests.test_create_brand_success -v 2
```

### Test Output Levels

```bash
# Minimal output
python manage.py test test_api_endpoints

# Standard output (default)
python manage.py test test_api_endpoints -v 1

# Detailed output
python manage.py test test_api_endpoints -v 2

# Very detailed output
python manage.py test test_api_endpoints -v 3
```

### Expected Results

- **Success**: `✅ ALL TESTS PASSED!`
- **Failure**: `❌ SOME TESTS FAILED! Check the output above.`

> **Tip**: The test script automatically activates the virtual environment. Ensure dependencies are installed with `pip install -r requirements.txt` if needed. 