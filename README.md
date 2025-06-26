# Budget Management System (Django + Celery)

## Overview
A backend system for ad agencies to manage daily/monthly budgets, campaign control, and dayparting, using Django and Celery. The system tracks ad spend, enforces budget rules, resets budgets, and respects campaign schedules.

---

## Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Setup & Running Locally](#setup--running-locally)
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
- **Tracks daily and monthly ad spend per brand and campaign**
- **Automatically pauses campaigns** when budgets are exceeded
- **Resets budgets** at the start of each day/month and reactivates eligible campaigns
- **Dayparting**: campaigns only run during allowed hours
- **Admin panel** for full management
- **Management commands** for enforcement and resets
- **Celery periodic tasks** for automation
- **Static typing** (PEP 484, MyPy)
- **Health check** for system status

---

## Project Structure
```
remotereps/
├── brands/         # Brand models/admin
├── campaigns/      # Campaign models/admin
├── spending/       # Spend models/services/admin
├── scheduling/     # Schedule models/services/admin
├── tasks/          # Celery tasks
├── budget_system/  # Django project settings
├── manage.py       # Django entrypoint
├── run_all.sh      # Script to run all services
├── README.md       # This file
├── PSEUDOCODE.md   # High-level pseudo-code (see below)
└── ...
```

---

## Setup & Running Locally
### Prerequisites
- Python 3.11+
- Redis (for Celery broker)
- SQLite (default) or PostgreSQL

### Installation
```bash
# Clone the repo
$ git clone <repository-url>
$ cd remotereps

# Create and activate virtualenv
$ python -m venv venv
$ source venv/bin/activate

# Install dependencies
$ pip install -r requirements.txt

# Install and start Redis
# Mac (Homebrew)
$ brew install redis && brew services start redis
# Ubuntu
$ sudo apt-get install redis-server && sudo service redis-server start
# Docker
$ docker run -d -p 6379:6379 redis:alpine

# Configure environment variables
$ cp env.example .env
# (Edit .env as needed)

# Run migrations
$ python manage.py migrate

# Create admin user
$ python manage.py createsuperuser

# Start all services (Django, Celery worker, Celery beat)
$ ./run_all.sh
```

---

## Data Models
- **Brand**: name, daily_budget, monthly_budget
- **Campaign**: belongs to Brand, has status (active/paused), daily/monthly spend, pause reason
- **Spend**: campaign, amount, date, type (daily/monthly), description
- **Schedule**: campaign, day_of_week, start_time, end_time, is_active

See [PSEUDOCODE.md](./PSEUDOCODE.md) for a high-level, language-agnostic overview and logic.

---

## Admin Panel Usage
- Access: [http://localhost:8000/admin](http://localhost:8000/admin)
- Log in with your superuser credentials
- **Brands**: Create/edit brands and set budgets
- **Campaigns**: Assign to brands, set status, view spend, pause/activate
- **Spends**: View all spend records, filter by campaign/brand/date
- **Schedules**: Set dayparting (days/times when campaigns are allowed to run)
- All models have color-coded budget/spend indicators for quick status

---

## Management Commands
Run with `python manage.py <command>`

### Enforce Budgets
Pauses campaigns that exceed daily/monthly budgets.
```bash
python manage.py enforce_budgets
```

### Enforce Dayparting
Pauses/activates campaigns based on their schedule.
```bash
python manage.py enforce_dayparting
```

### Reset Spends
Resets daily/monthly spends and reactivates eligible campaigns.
```bash
# Daily reset
python manage.py reset_spends --daily
# Monthly reset
python manage.py reset_spends --monthly
# Both
python manage.py reset_spends --both
```

#### Example Output
```
INFO Starting budget enforcement
INFO Budget enforcement completed: {'checked': 2, 'paused_daily': 1, 'paused_monthly': 0, 'errors': 0}
```

---

## Celery Tasks & Health Check
Celery automates enforcement and resets. Tasks are scheduled via Celery Beat.

- **Budget enforcement**: every 5 minutes
- **Dayparting enforcement**: every minute
- **Daily reset**: every day at 00:00
- **Monthly reset**: 1st day of month at 00:00

### Health Check (manual)
Check system health (DB, campaigns, services):
```bash
python manage.py shell -c "from tasks.budget_tasks import health_check_task; print(health_check_task())"
```
Example output:
```
{'timestamp': '...', 'status': 'healthy', 'checks': {'database': {'status': 'healthy', ...}, 'campaigns': {'status': 'healthy', ...}, 'services': {'status': 'healthy', ...}}}
```

---

## Static Typing & Testing
- All code uses Python type hints (PEP 484)
- MyPy config: `mypy.ini`
- Check typing:
```bash
mypy .
```
- Run the full system test:
```bash
python test_system.py
```

---

## Daily & Monthly Workflow
1. **Every minute**: Dayparting enforcement (pauses/activates campaigns by schedule)
2. **Every 5 minutes**: Budget enforcement (pauses campaigns that exceed budgets)
3. **00:00 daily**: Resets daily spends, reactivates eligible campaigns
4. **00:00 on 1st of month**: Resets monthly spends, reactivates eligible campaigns
5. **Manual/admin actions**: All can be triggered via management commands or admin panel

---

## Assumptions & Simplifications
- All times are UTC
- Spending is tracked with cent precision
- No real-time notifications (logs only)
- SQLite by default, but supports Postgres
- No REST API (admin/commands only)
- No external queueing libraries (only Celery + Redis)

---

## Troubleshooting
- **Redis not running**: See error in `run_all.sh` and start Redis as instructed
- **Port 8000 in use**: Stop other Django servers or change port in `run_all.sh`
- **Celery not starting**: Check if Redis is running and accessible
- **Migrations fail**: Check DB config and run `python manage.py migrate` again
- **Static typing errors**: Run `mypy .` and fix any reported issues

---

## Contributing
1. Fork the repo
2. Create a feature branch
3. Use static typing everywhere
4. Run `mypy .` and `python test_system.py` before PR
5. Submit a pull request

---

## Delivery Checklist
- [x] Pseudo-code in `PSEUDOCODE.md`
- [x] Django models and logic for spend tracking and campaign control
- [x] Celery tasks for resets and dayparting enforcement
- [x] Management commands for enforcement and resets
- [x] Static typing everywhere, MyPy config, zero errors
- [x] README with setup, usage, workflow, and troubleshooting
- [x] Public GitHub repository

---

## Pseudo-code
See [PSEUDOCODE.md](./PSEUDOCODE.md) for a high-level, language-agnostic overview of models and logic.

---

## Bonus: REST API Usage Examples

The system provides REST API endpoints for all main resources. No authentication is required for demo purposes.

### List Brands
```bash
curl -X GET http://localhost:8000/api/brands/
```

### Create a Brand
```bash
curl -X POST http://localhost:8000/api/brands/ \
  -H 'Content-Type: application/json' \
  -d '{"name": "Acme", "daily_budget": "100.00", "monthly_budget": "2000.00"}'
```

### Get a Brand by ID
```bash
curl -X GET http://localhost:8000/api/brands/<brand_id>/
```

### Delete a Brand
```bash
curl -X DELETE http://localhost:8000/api/brands/<brand_id>/
```

---

### List Campaigns
```bash
curl -X GET http://localhost:8000/api/campaigns/
```

### Create a Campaign
```bash
curl -X POST http://localhost:8000/api/campaigns/ \
  -H 'Content-Type: application/json' \
  -d '{"brand": "<brand_id>", "name": "Summer Sale", "status": "ACTIVE"}'
```

---

### List Spends
```bash
curl -X GET http://localhost:8000/api/spends/
```

### Create a Spend
```bash
curl -X POST http://localhost:8000/api/spends/ \
  -H 'Content-Type: application/json' \
  -d '{"campaign": "<campaign_id>", "amount": "10.00", "spend_date": "2024-06-01", "spend_type": "DAILY"}'
```

---

### List Schedules
```bash
curl -X GET http://localhost:8000/api/schedules/
```

### Create a Schedule
```bash
curl -X POST http://localhost:8000/api/schedules/ \
  -H 'Content-Type: application/json' \
  -d '{"campaign": "<campaign_id>", "day_of_week": 0, "start_time": "09:00:00", "end_time": "18:00:00", "is_active": true}'
```

---

Replace `<brand_id>` and `<campaign_id>` with real UUIDs from your database.

For full API documentation, see the browsable API at [http://localhost:8000/api/](http://localhost:8000/api/). 

## Running All Tests

To run all unit, integration, and API tests for the system, use the provided script:

```bash
./run_tests.sh
```

This will:
- Activate the virtual environment
- Run all Django tests (including API and integration)
- Show a summary of the results

### Running Specific Tests

You can also run tests for a specific app or test module:

```bash
./run_tests.sh test_api_endpoints
./run_tests.sh brands
./run_tests.sh campaigns
```

This will only run the tests for the specified label (see Django test discovery for more options).

### Running Individual Test Modules

For more granular control, you can run specific test modules directly:

#### API Endpoints Tests
```bash
python manage.py test test_api_endpoints -v 2
```

#### System Integration Test
```bash
python test_system.py
```

#### Specific Test Classes
```bash
# Run only brand API tests
python manage.py test test_api_endpoints.BrandAPITests -v 2

# Run only campaign API tests
python manage.py test test_api_endpoints.CampaignAPITests -v 2

# Run only schedule API tests
python manage.py test test_api_endpoints.ScheduleAPITests -v 2
```

#### Specific Test Methods
```bash
# Run a single test method
python manage.py test test_api_endpoints.BrandAPITests.test_create_brand_success -v 2
```

#### Verbosity Levels
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

### Output
- If all tests pass, you'll see:
  - `✅ ALL TESTS PASSED!`
- If any test fails, you'll see:
  - `❌ SOME TESTS FAILED! Check the output above.`

> **Tip:** The script will automatically activate the virtual environment if it exists. If you haven't installed dependencies, run `pip install -r requirements.txt` first. 