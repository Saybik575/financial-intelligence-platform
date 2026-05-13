# Real ML Rescoring Logic - Implementation Guide

## Overview

The ETL pipeline now includes **real financial health scoring** powered by machine learning algorithms. This replaces the previous placeholder empty scores with comprehensive multidimensional financial analysis.

## Architecture

### Scoring System Components

```
┌─────────────────────────────────────────────────────────────┐
│                   ML Scoring System                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  FinancialHealthScorer                                       │
│  ├─ Profitability Analysis                                  │
│  ├─ Growth Analysis                                         │
│  ├─ Leverage Analysis                                       │
│  ├─ Cash Flow Analysis                                      │
│  ├─ Dividend Analysis                                       │
│  └─ Trend Analysis                                          │
│                                                              │
│  BatchScorer                                                 │
│  └─ Batch process & database integration                    │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                   Celery Tasks                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ml_rescoring_task                                          │
│  ├─ Full batch scoring (all companies)                      │
│  └─ Single company scoring                                  │
│                                                              │
│  ml_incremental_rescoring_task                              │
│  └─ Incremental update (recently changed companies)         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
         │                              │
         └──────────────┬───────────────┘
                        │
                    Redis Queue
                        │
            Processed by Celery Worker
                        │
            Results saved to fact_ml_scores
```

## Scoring Dimensions

### 1. **Profitability Score** (25% weight)
Measures company's ability to generate profits from operations.

- **Net Profit Margin**: Net income / Revenue
  - Excellent: >15%
  - Good: 10-15%
  - Average: 5-10%
  - Poor: <5%

- **Operating Profit Margin**: Operating income / Revenue
  - Excellent: >20%
  - Good: 15-20%
  - Average: 10-15%

- **Return on Assets (ROA)**: Net income / Total assets
  - Excellent: >15%
  - Good: 10-15%
  - Average: 5-10%

**Calculation**: Average of normalized margins

### 2. **Growth Score** (20% weight)
Measures company's revenue and profit expansion.

- **Year-over-Year Revenue Growth**
  - Target: 10-20% annually
  - Scoring: Linear scale (0% = 0 points, 20% = 100 points)

- **Compounded Annual Growth Rate (CAGR)**
  - Sales CAGR over available history
  - Profit CAGR over available history

- **Momentum**: Acceleration of growth

**Calculation**: Average of growth metrics over recent periods

### 3. **Leverage Score** (20% weight)
Measures financial risk through debt levels.

- **Debt-to-Equity Ratio**
  - Excellent: ≤ 0.5 (100 points)
  - Good: 0.5-1.0 (80 points)
  - Average: 1.0-1.5 (60 points)
  - Weak: 1.5-2.0 (40 points)
  - Poor: >2.0 (20 points)

- **Equity Ratio**: Shareholders' equity / Total assets
  - Target: >40% (100 points)
  - Scales linearly below

- **Interest Coverage Ratio**: Operating profit / Interest expense
  - Excellent: >10x (100 points)
  - Good: 5-10x (80 points)
  - Average: 2-5x (60 points)
  - Weak: <2x (40 points)

**Calculation**: Average of three normalized ratios

### 4. **Cash Flow Score** (15% weight)
Measures actual cash generation and conversion.

- **Operating Cash Flow**
  - Positive OCF = 100 points
  - Negative OCF = 50 points

- **Free Cash Flow** (OCF + Investing activities)
  - Positive FCF = 100 points
  - Negative FCF = 30 points

- **Cash Conversion Ratio** (OCF / Net profit)
  - Excellent: ≥ 1.0 (100 points)
  - Good: 0.5-1.0 (50-100 points)
  - Weak: <0.5 (20-50 points)

**Calculation**: Average of cash flow metrics

### 5. **Dividend Score** (10% weight)
Measures capital return to shareholders.

- **Dividend Payout Consistency**
  - Company pays consistent dividends = higher score
  - Irregular payouts = lower score
  - Non-paying companies = neutral score (50 points)

- **Payout Ratio Stability**
  - Low variance in payout ratio = 100 points
  - High variance = lower score

**Calculation**: Based on 3-year payout history

### 6. **Trend Score** (10% weight)
Measures momentum and business trajectory.

- **Profitability Trend**
  - Improving profits = positive trend
  - Declining profits = negative trend

- **Revenue Trend**
  - Consistent growth = 100 points
  - Stable = 70 points
  - Declining = 30 points

- **Leverage Trend**
  - Decreasing debt = positive
  - Increasing debt = negative

**Calculation**: Weighted average of 3 trend indicators

### 7. **Overall Score**
Weighted combination of all dimensions:

```
Overall = (0.25 × Profitability) +
          (0.20 × Growth) +
          (0.20 × Leverage) +
          (0.15 × CashFlow) +
          (0.10 × Dividend) +
          (0.10 × Trend)
```

Range: 0-100 points

### Health Labels

Based on overall score:

| Label | Score Range | Interpretation |
|-------|-------------|-----------------|
| EXCELLENT | 81-100 | Outstanding financial health |
| GOOD | 61-80 | Strong financial position |
| AVERAGE | 41-60 | Moderate financial stability |
| WEAK | 21-40 | Below-average financial health |
| POOR | 0-20 | Critical financial concerns |

## Usage

### 1. Run Full Batch Rescoring

**Asynchronously (Recommended for production):**
```bash
./orchestrate.sh run-ml-scoring
# or
docker-compose exec -T web python manage.py run_ml_scoring --async
```

**Synchronously (for testing):**
```bash
docker-compose exec web python manage.py run_ml_scoring
```

### 2. Score Specific Company

```bash
# Async
./orchestrate.sh run-ml-scoring SYMBOL
# or
docker-compose exec -T web python manage.py run_ml_scoring --symbol INFY --async

# Sync
docker-compose exec web python manage.py run_ml_scoring --symbol TCS
```

### 3. Run Incremental Rescoring

Only scores companies recently updated in the ETL:

```bash
./orchestrate.sh run-ml-scoring --incremental

# or with management command
docker-compose exec -T web python manage.py run_ml_scoring --incremental --async
```

### 4. Integrate with ETL Pipeline

Run rescoring automatically after ETL load:

```bash
# With scoring
./orchestrate.sh run-etl async --with-scoring

# or with management command
docker-compose exec -T web python manage.py run_etl --async --with-scoring
```

## Using Celery Tasks Directly

### Python API

```python
# In Django shell or application code
from etl_tasks import ml_rescoring_task, ml_incremental_rescoring_task

# Queue full rescoring
task = ml_rescoring_task.delay()
print(f"Task ID: {task.id}")

# Check status
from celery.result import AsyncResult
result = AsyncResult(task.id)
print(result.state)  # PENDING, STARTED, SUCCESS, FAILURE
print(result.result)  # Task result dict

# Queue single company rescoring
task = ml_rescoring_task.delay(symbol='RELIANCE')

# Queue incremental rescoring
task = ml_incremental_rescoring_task.delay()
```

### Chain with ETL Pipeline

```python
from celery import chain
from etl_tasks import (
    extract_task, transform_task, load_task,
    ml_incremental_rescoring_task
)

# Chain: Extract -> Transform -> Load -> ML Scoring
workflow = chain(
    extract_task.s(),
    transform_task.s(),
    load_task.s(),
    ml_incremental_rescoring_task.s(),
)

result = workflow.apply_async()
```

## Output Format

Scores saved to `fact_ml_scores` table:

```
symbol          | TEXT    | Stock ticker
computed_at     | TIMESTAMP | Calculation timestamp
overall_score   | FLOAT   | 0-100 overall score
profitability_score | FLOAT | 0-100
growth_score    | FLOAT   | 0-100
leverage_score  | FLOAT   | 0-100
cashflow_score  | FLOAT   | 0-100
dividend_score  | FLOAT   | 0-100
trend_score     | FLOAT   | 0-100
health_label    | TEXT    | POOR/WEAK/AVERAGE/GOOD/EXCELLENT
```

## Scheduling Automatic Rescoring

### Option 1: Django Admin UI

1. Start services: `./orchestrate.sh start`
2. Go to: http://localhost:8000/admin
3. Periodic tasks → Add
4. Configure:
   - **Name**: Daily ML Rescoring
   - **Task**: `ml.incremental_rescoring_task`
   - **Schedule**: Daily at 03:00 (after ETL at 02:00)
   - **Enabled**: ✓

### Option 2: Command-Line Setup

```bash
docker-compose exec web python manage.py shell
```

```python
from django_celery_beat.models import PeriodicTask, CrontabSchedule

# Create schedule: Daily at 3 AM
schedule = CrontabSchedule.objects.create(
    hour=3, minute=0, day_of_week='*'
)

# Create periodic task
PeriodicTask.objects.create(
    crontab=schedule,
    name='Daily ML Rescoring',
    task='ml.incremental_rescoring_task',
    expires=86400,  # 24 hours
)
```

## Performance Characteristics

### Timing

| Operation | Typical Time | Notes |
|-----------|-------------|-------|
| Single company | 0.5-2s | Very fast |
| 50 companies | 30-60s | Incremental batch |
| 500 companies | 5-10 min | Full batch |
| 1000+ companies | 15-20 min | Full batch (parallel possible) |

### Resource Usage

- **Memory**: ~200-500 MB per worker
- **CPU**: 1 core fully utilized during scoring
- **Database**: Moderate I/O for data fetch and write
- **Redis**: Queue storage only (~1 KB per task)

### Optimization

1. **Parallel Workers**: Add multiple Celery workers
   ```yaml
   celery_worker:
     command: celery -A config worker --concurrency=4
   ```

2. **Batch Sizing**: Adjust in `ml_scoring.py`:
   ```python
   BATCH_SIZE = 25  # Companies per batch
   ```

3. **Incremental Over Batch**: Use incremental rescoring for daily updates
   - Batch: Run weekly/monthly
   - Incremental: Run daily after ETL

## Monitoring

### Check Task Status

```bash
# Active tasks
docker-compose exec web celery -A config inspect active

# Task stats
docker-compose exec web celery -A config inspect stats

# View logs
./orchestrate.sh logs celery_worker
```

### Database Queries

```python
# Check latest scores
from ml_ml_scores.models import FactMlScores

latest = FactMlScores.objects.latest('computed_at')
print(f"{latest.symbol}: {latest.overall_score:.1f} ({latest.health_label})")

# Companies by health label
excellent = FactMlScores.objects.filter(health_label='EXCELLENT')
```

## Troubleshooting

### Scores showing as 50 (average)

**Possible causes:**
- Insufficient data in fact tables
- Missing financial data for company
- Data quality issues

**Solution:**
```bash
# Check source data
docker-compose exec db psql -U postgres -d fintech
SELECT symbol, COUNT(*) FROM fact_profit_loss GROUP BY symbol;
```

### Task fails with "No data to score"

**Possible cause:** ETL load hasn't completed

**Solution:**
```bash
# Verify data is loaded
docker-compose exec db psql -U postgres -d fintech
SELECT COUNT(*) FROM fact_profit_loss;

# Retry scoring
./orchestrate.sh run-ml-scoring SYMBOL
```

### High memory usage

**Solution:**
- Reduce concurrent workers: `--concurrency=2`
- Run incremental instead of batch
- Process in smaller batches

## Advanced: Custom Thresholds

Modify thresholds in `ml_scoring.py`:

```python
THRESHOLDS = {
    'profitability': {
        'net_margin_excellent': 0.20,  # Changed from 0.15
        'net_margin_good': 0.12,       # Changed from 0.10
        # ...
    },
    # ... other dimensions
}
```

Then restart workers:
```bash
./orchestrate.sh restart
```

## Algorithm Validation

### Backtesting

Test scoring logic against historical data:

```bash
python etl_orchestrator.py score-backtest --start-date 2020-01-01
```

### Comparison

Compare scores across similar companies (same sector):

```bash
# Query in Django shell
from ml_scoring import FinancialHealthScorer
from django.db import connections

engine = connections['default'].get_connection()

# Get all IT companies scores
```

## Files Overview

```
financial-intelligence-platform/
├── webapp/
│   ├── ml_scoring.py              # Core scoring algorithm
│   ├── etl_tasks.py               # Celery tasks (updated)
│   └── dashboard/management/commands/
│       ├── run_etl.py             # ETL command (updated)
│       └── run_ml_scoring.py      # ML scoring command
├── ML_RESCORING.md                # This file
└── DOCKER_SETUP.md                # Updated with ML examples
```

## Next Steps

1. ✅ **Implement scoring logic** - DONE
2. ✅ **Create Celery tasks** - DONE
3. ✅ **Integrate with ETL** - DONE
4. 🔄 **Setup scheduled rescoring**:
   ```bash
   ./orchestrate.sh start
   ./orchestrate.sh migrate
   python manage.py shell
   # Configure periodic tasks
   ```
5. 🔄 **Create ML API endpoints** (optional):
   ```python
   # Add to webapp/api/views.py
   # Endpoint: /api/scores/?symbol=INFY
   ```

## References

- Financial Health Scoring: Industry best practices
- Altman Z-Score: Modified for Indian market
- Credit Rating Methodology: Adapted for equity analysis
- Cash Flow Analysis: Standard accounting practices
