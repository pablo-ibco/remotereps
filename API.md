# REST API Documentation

This document describes the REST API endpoints for the Budget Management System.

- All endpoints are under `/api/`
- No authentication is required for demo purposes (add Token/Auth for production)
- For interactive docs, see [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)

---

## Endpoints Overview

| Resource   | List/Create           | Retrieve/Update/Delete         |
|------------|----------------------|-------------------------------|
| Brands     | GET/POST `/brands/`  | GET/PUT/PATCH/DELETE `/brands/{id}/` |
| Campaigns  | GET/POST `/campaigns/` | GET/PUT/PATCH/DELETE `/campaigns/{id}/` |
| Spends     | GET/POST `/spends/`  | GET/PUT/PATCH/DELETE `/spends/{id}/` |
| Schedules  | GET/POST `/schedules/` | GET/PUT/PATCH/DELETE `/schedules/{id}/` |

---

## Brands

### List Brands
- **GET** `/api/brands/`
- **Response:**
```json
[
  {
    "id": "uuid",
    "name": "Acme",
    "daily_budget": "100.00",
    "monthly_budget": "2000.00",
    "created_at": "2024-06-01T12:00:00Z",
    "updated_at": "2024-06-01T12:00:00Z"
  }
]
```

### Create Brand
- **POST** `/api/brands/`
- **Body:**
```json
{
  "name": "Acme",
  "daily_budget": "100.00",
  "monthly_budget": "2000.00"
}
```
- **Response:** 201 Created
```json
{
  "id": "uuid",
  "name": "Acme",
  "daily_budget": "100.00",
  "monthly_budget": "2000.00",
  "created_at": "...",
  "updated_at": "..."
}
```
- **Error Example:** 400 Bad Request
```json
{
  "name": ["This field must be unique."]
}
```

### Retrieve/Update/Delete Brand
- **GET/PUT/PATCH/DELETE** `/api/brands/{id}/`

---

## Campaigns

### List Campaigns
- **GET** `/api/campaigns/`
- **Response:**
```json
[
  {
    "id": "uuid",
    "brand": "brand-uuid",
    "name": "Summer Sale",
    "status": "ACTIVE",
    "daily_spend": "0.00",
    "monthly_spend": "0.00",
    "pause_reason": null,
    "paused_at": null,
    "created_at": "...",
    "updated_at": "..."
  }
]
```

### Create Campaign
- **POST** `/api/campaigns/`
- **Body:**
```json
{
  "brand": "brand-uuid",
  "name": "Summer Sale",
  "status": "ACTIVE"
}
```
- **Response:** 201 Created

### Retrieve/Update/Delete Campaign
- **GET/PUT/PATCH/DELETE** `/api/campaigns/{id}/`

---

## Spends

### List Spends
- **GET** `/api/spends/`
- **Response:**
```json
[
  {
    "id": "uuid",
    "campaign": "campaign-uuid",
    "amount": "10.00",
    "spend_date": "2024-06-01",
    "spend_type": "DAILY",
    "description": "Test spend",
    "created_at": "..."
  }
]
```

### Create Spend
- **POST** `/api/spends/`
- **Body:**
```json
{
  "campaign": "campaign-uuid",
  "amount": "10.00",
  "spend_date": "2024-06-01",
  "spend_type": "DAILY",
  "description": "Test spend"
}
```
- **Response:** 201 Created

### Retrieve/Update/Delete Spend
- **GET/PUT/PATCH/DELETE** `/api/spends/{id}/`

---

## Schedules

### List Schedules
- **GET** `/api/schedules/`
- **Response:**
```json
[
  {
    "id": "uuid",
    "campaign": "campaign-uuid",
    "day_of_week": 0,
    "start_time": "09:00:00",
    "end_time": "18:00:00",
    "is_active": true,
    "created_at": "...",
    "updated_at": "..."
  }
]
```

### Create Schedule
- **POST** `/api/schedules/`
- **Body:**
```json
{
  "campaign": "campaign-uuid",
  "day_of_week": 0,
  "start_time": "09:00:00",
  "end_time": "18:00:00",
  "is_active": true
}
```
- **Response:** 201 Created

### Retrieve/Update/Delete Schedule
- **GET/PUT/PATCH/DELETE** `/api/schedules/{id}/`

---

## Field Descriptions

### Brand
| Field           | Type    | Required | Description                |
|-----------------|---------|----------|----------------------------|
| id              | UUID    | No       | Unique identifier          |
| name            | String  | Yes      | Brand name (unique)        |
| daily_budget    | String  | Yes      | Daily budget (decimal str) |
| monthly_budget  | String  | Yes      | Monthly budget (decimal)   |
| created_at      | String  | No       | Creation timestamp         |
| updated_at      | String  | No       | Last update timestamp      |

### Campaign
| Field         | Type    | Required | Description                |
|---------------|---------|----------|----------------------------|
| id            | UUID    | No       | Unique identifier          |
| brand         | UUID    | Yes      | Brand ID                   |
| name          | String  | Yes      | Campaign name              |
| status        | String  | Yes      | ACTIVE or PAUSED           |
| daily_spend   | String  | No       | Daily spend (decimal str)  |
| monthly_spend | String  | No       | Monthly spend (decimal)    |
| pause_reason  | String  | No       | Reason for pause           |
| paused_at     | String  | No       | When paused                |
| created_at    | String  | No       | Creation timestamp         |
| updated_at    | String  | No       | Last update timestamp      |

### Spend
| Field        | Type    | Required | Description                |
|--------------|---------|----------|----------------------------|
| id           | UUID    | No       | Unique identifier          |
| campaign     | UUID    | Yes      | Campaign ID                |
| amount       | String  | Yes      | Amount spent (decimal str) |
| spend_date   | String  | Yes      | Date (YYYY-MM-DD)          |
| spend_type   | String  | Yes      | DAILY or MONTHLY           |
| description  | String  | No       | Optional description       |
| created_at   | String  | No       | Creation timestamp         |

### Schedule
| Field        | Type    | Required | Description                |
|--------------|---------|----------|----------------------------|
| id           | UUID    | No       | Unique identifier          |
| campaign     | UUID    | Yes      | Campaign ID                |
| day_of_week  | Int     | Yes      | 0=Monday, 6=Sunday         |
| start_time   | String  | Yes      | Start time (HH:MM:SS)      |
| end_time     | String  | Yes      | End time (HH:MM:SS)        |
| is_active    | Bool    | Yes      | Whether schedule is active |
| created_at   | String  | No       | Creation timestamp         |
| updated_at   | String  | No       | Last update timestamp      |

---

## Errors
- 400 Bad Request: Invalid input or missing required fields
- 404 Not Found: Resource does not exist
- 405 Method Not Allowed: Invalid HTTP method

---

## Interactive API Docs (click here after running the app locally)
- [Browsable API](http://localhost:8000/api/)
- [Swagger UI](http://localhost:8000/api/docs/)
- [OpenAPI Schema (JSON) - Download](http://localhost:8000/api/schema/) 