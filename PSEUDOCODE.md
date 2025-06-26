# Pseudocode: Budget Management System

## Data Models

### Brand
```
Brand {
    id: UUID
    name: String
    daily_budget: Decimal
    monthly_budget: Decimal
    created_at: DateTime
    updated_at: DateTime
}
```

### Campaign
```
Campaign {
    id: UUID
    brand_id: UUID (FK -> Brand)
    name: String
    status: Enum (ACTIVE, PAUSED)
    daily_spend: Decimal
    monthly_spend: Decimal
    created_at: DateTime
    updated_at: DateTime
}
```

### Spend
```
Spend {
    id: UUID
    campaign_id: UUID (FK -> Campaign)
    amount: Decimal
    spend_date: Date
    spend_type: Enum (DAILY, MONTHLY)
    created_at: DateTime
}
```

### Schedule (Dayparting)
```
Schedule {
    id: UUID
    campaign_id: UUID (FK -> Campaign)
    day_of_week: Integer (0-6, where 0=Monday)
    start_time: Time
    end_time: Time
    is_active: Boolean
    created_at: DateTime
}
```

## Core Logic

### 1. Spend Tracking
```
FUNCTION track_spend(campaign_id, amount, spend_date):
    // Create spend record
    spend = new Spend(
        campaign_id=campaign_id,
        amount=amount,
        spend_date=spend_date,
        spend_type=DAILY
    )
    spend.save()
    
    // Update campaign spend
    campaign = Campaign.find(campaign_id)
    campaign.daily_spend += amount
    campaign.monthly_spend += amount
    campaign.save()
    
    // Check budget limits
    check_budget_limits(campaign)
```

### 2. Budget Limit Check
```
FUNCTION check_budget_limits(campaign):
    brand = campaign.brand
    
    // Check daily limit
    IF campaign.daily_spend >= brand.daily_budget:
        pause_campaign(campaign, "DAILY_BUDGET_EXCEEDED")
        RETURN
    
    // Check monthly limit
    IF campaign.monthly_spend >= brand.monthly_budget:
        pause_campaign(campaign, "MONTHLY_BUDGET_EXCEEDED")
        RETURN
```

### 3. Pause Campaign
```
FUNCTION pause_campaign(campaign, reason):
    campaign.status = PAUSED
    campaign.pause_reason = reason
    campaign.paused_at = NOW()
    campaign.save()
    
    LOG("Campaign {campaign.id} paused: {reason}")
```

### 4. Daily Reset
```
FUNCTION daily_reset():
    // Reset daily spend for all campaigns
    FOR EACH campaign IN Campaign.all():
        campaign.daily_spend = 0
        campaign.save()
    
    // Reactivate campaigns paused due to daily limit
    FOR EACH campaign IN Campaign.where(status=PAUSED, pause_reason="DAILY_BUDGET_EXCEEDED"):
        IF can_activate_campaign(campaign):
            activate_campaign(campaign)
    
    LOG("Daily reset completed")
```

### 5. Monthly Reset
```
FUNCTION monthly_reset():
    // Reset monthly spend for all campaigns
    FOR EACH campaign IN Campaign.all():
        campaign.monthly_spend = 0
        campaign.save()
    
    // Reactivate campaigns paused due to monthly limit
    FOR EACH campaign IN Campaign.where(status=PAUSED, pause_reason="MONTHLY_BUDGET_EXCEEDED"):
        IF can_activate_campaign(campaign):
            activate_campaign(campaign)
    
    LOG("Monthly reset completed")
```

### 6. Dayparting Check
```
FUNCTION check_dayparting():
    current_time = NOW()
    current_day = current_time.day_of_week
    
    FOR EACH campaign IN Campaign.where(status=ACTIVE):
        schedule = Schedule.find_by(campaign_id=campaign.id, day_of_week=current_day)
        
        IF schedule AND schedule.is_active:
            IF current_time.time BETWEEN schedule.start_time AND schedule.end_time:
                // Campaign should be active
                IF campaign.status != ACTIVE:
                    activate_campaign(campaign)
            ELSE:
                // Outside allowed time
                pause_campaign(campaign, "OUTSIDE_SCHEDULE")
        ELSE:
            // No schedule for this day
            pause_campaign(campaign, "NO_SCHEDULE")
```

### 7. Activate Campaign
```
FUNCTION activate_campaign(campaign):
    // Check if it can be activated
    IF NOT can_activate_campaign(campaign):
        RETURN FALSE
    
    campaign.status = ACTIVE
    campaign.pause_reason = NULL
    campaign.paused_at = NULL
    campaign.save()
    
    LOG("Campaign {campaign.id} activated")
    RETURN TRUE
```

### 8. Check if Campaign Can Be Activated
```
FUNCTION can_activate_campaign(campaign):
    brand = campaign.brand
    
    // Check budget limits
    IF campaign.daily_spend >= brand.daily_budget:
        RETURN FALSE
    
    IF campaign.monthly_spend >= brand.monthly_budget:
        RETURN FALSE
    
    // Check dayparting
    current_time = NOW()
    current_day = current_time.day_of_week
    schedule = Schedule.find_by(campaign_id=campaign.id, day_of_week=current_day)
    
    IF schedule AND schedule.is_active:
        IF current_time.time BETWEEN schedule.start_time AND schedule.end_time:
            RETURN TRUE
        ELSE:
            RETURN FALSE
    
    RETURN FALSE
```

## Scheduled Tasks (Celery)

### Daily Reset Task
```
@periodic_task(run_at=timedelta(days=1))
FUNCTION scheduled_daily_reset():
    daily_reset()
```

### Monthly Reset Task
```
@periodic_task(run_at=timedelta(days=1), day_of_month=1)
FUNCTION scheduled_monthly_reset():
    monthly_reset()
```

### Budget Check Task
```
@periodic_task(run_at=timedelta(minutes=5))
FUNCTION scheduled_budget_check():
    FOR EACH campaign IN Campaign.where(status=ACTIVE):
        check_budget_limits(campaign)
```

### Dayparting Check Task
```
@periodic_task(run_at=timedelta(minutes=1))
FUNCTION scheduled_dayparting_check():
    check_dayparting()
```

## Daily Workflow

1. **00:00** - Daily reset
   - Resets daily spend
   - Reactivates eligible campaigns

2. **00:01** - Dayparting check
   - Activates/deactivates campaigns according to schedule

3. **Every 5 minutes** - Budget check
   - Monitors spend vs. limits
   - Pauses campaigns that exceed budget

4. **Every minute** - Dayparting check
   - Controls allowed campaign hours

5. **1st day of month, 00:00** - Monthly reset
   - Resets monthly spend
   - Reactivates eligible campaigns

## Performance Considerations

- Indices on `campaign_id`, `spend_date`, `status`
- Aggregated spend cache
- Database locks for critical operations
- Structured logs for monitoring
- Performance metrics 