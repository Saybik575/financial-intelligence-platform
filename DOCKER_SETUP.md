# Docker + Celery + Redis ETL Pipeline Setup

This guide explains how to set up and run the Financial Intelligence Platform with Docker, Celery, and Redis.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                       │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│              │              │              │                    │
│   Web        │   Celery     │   Celery     │   ETL              │
│   (Django)   │   Worker     │   Beat       │   Scheduler        │
│              │              │              │                    │
└──────────────┴──────────────┴──────────────┴────────────────────┘
        │              │              │              │
        └──────────────┴──────────────┴──────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
    ┌───────────┐            ┌──────────────┐
    │  Redis    │            │ PostgreSQL   │
    │ (Broker & │            │  (Warehouse) │
    │  Backend) │            │              │
    └───────────┘            └──────────────┘
```

## Prerequisites

- Docker & Docker Compose (v3.9+)
- Git
- Python 3.12+ (for local development)
- At least 4GB RAM allocated to Docker
- 10GB+ free disk space

## Quick Start

### 1. Clone and Setup

```bash
cd financial-intelligence-platform
cp .env.example .env
```

### 2. Start Services

**On Linux/macOS:**
```bash
chmod +x orchestrate.sh
./orchestrate.sh start
```

**On Windows:**
```cmd
orchestrate.bat start
```

This will:
- Start PostgreSQL database
- Start Redis broker
- Start Django web server
- Start Celery worker
- Start Celery beat scheduler

### 3. Initialize Database

```bash
./orchestrate.sh migrate
./orchestrate.sh create-superuser
```

## Running ETL Pipeline

### Asynchronous Execution (Recommended)

Queue ETL tasks to run in background via Celery:

```bash
# Run complete pipeline
./orchestrate.sh run-etl async

# Run specific phase
./orchestrate.sh run-etl async extract
./orchestrate.sh run-etl async transform
./orchestrate.sh run-etl async load
```

### Synchronous Execution

Run ETL tasks and wait for completion:

```bash
# Run complete pipeline
./orchestrate.sh run-etl sync

# Run specific phase
./orchestrate.sh run-etl sync extract
```

### Using Django Management Command

```bash
# Inside container
docker-compose exec web python manage.py run_etl --help

# Async full pipeline
docker-compose exec -T web python manage.py run_etl --async

# Sync extraction only
docker-compose exec -T web python manage.py run_etl --extract
```

### Using Celery Directly

```bash
# Execute task from web container
docker-compose exec web python manage.py shell
```

Then in Python shell:
```python
from etl_tasks import run_etl_pipeline, extract_task

# Queue task
task = run_etl_pipeline.delay()
task_id = task.id
print(f"Task queued: {task_id}")

# Check status
from celery.result import AsyncResult
result = AsyncResult(task_id)
print(result.state)  # PENDING, STARTED, SUCCESS, FAILURE
print(result.result)  # Task result
```

## Service Management

### View Service Status

```bash
./orchestrate.sh status
```

### View Logs

```bash
# All services
./orchestrate.sh logs

# Specific service
./orchestrate.sh logs web
./orchestrate.sh logs celery_worker
./orchestrate.sh logs redis
./orchestrate.sh logs db
```

### Celery Monitoring

```bash
# Check active tasks
./orchestrate.sh celery-status

# Purge task queue (be careful!)
./orchestrate.sh celery-purge
```

### Stop/Restart Services

```bash
./orchestrate.sh stop
./orchestrate.sh restart
```

## Environment Configuration

Edit `.env` file to customize:

```env
# Database
DB_NAME=fintech
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Django
DEBUG=False
SECRET_KEY=your-secret-key-change-in-production
```

## ETL Task Queue and Routing

The pipeline supports task routing with named queues:

- `default`: Standard tasks
- `etl`: ETL-specific tasks (extract, transform, load)

To route a task to the ETL queue:

```python
from etl_tasks import run_etl_pipeline

# Route to 'etl' queue
task = run_etl_pipeline.apply_async(queue='etl')
```

Celery worker processes both queues:
```bash
celery -A config worker --queues=default,etl
```

## Scheduled ETL Tasks

Celery Beat scheduler enables periodic ETL runs. Configure in Django admin:

1. Go to `/admin`
2. Navigate to "Periodic tasks"
3. Add a new periodic task:
   - Task: `etl.run_pipeline`
   - Schedule: Choose interval (e.g., daily at 2 AM)

Or programmatically:

```python
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from datetime import timedelta

schedule, _ = IntervalSchedule.objects.get_or_create(
    every=1,
    period=IntervalSchedule.DAYS,
)

PeriodicTask.objects.create(
    interval=schedule,
    name='Daily ETL Pipeline',
    task='etl.run_pipeline',
    kwargs='{}',
    expires=timedelta(hours=23),
)
```

## File Structure

```
financial-intelligence-platform/
├── docker-compose.yml          # Service definitions
├── Dockerfile                  # Container build config
├── orchestrate.sh              # Linux/macOS orchestration
├── orchestrate.bat             # Windows orchestration
├── .env.example                # Environment template
├── etl/
│   ├── 01_extract_from_excel.py
│   ├── 02_clean_and_transform.py
│   └── 03_load_to_warehouse.py
├── etl_pipeline.py             # ETL pipeline wrapper
├── webapp/
│   ├── manage.py
│   ├── config/
│   │   ├── celery.py           # Celery config
│   │   ├── settings.py
│   │   └── urls.py
│   ├── etl_tasks.py            # Celery tasks
│   └── dashboard/
│       └── management/commands/
│           └── run_etl.py      # Django command
└── data/
    ├── raw/                    # Input Excel files
    ├── clean/                  # Cleaned CSV outputs
    └── logs/                   # Application logs
```

## Troubleshooting

### Services won't start

```bash
# Check Docker resources
docker stats

# Check Docker logs
docker-compose logs -f

# Rebuild images
docker-compose build --no-cache
```

### Celery worker not picking up tasks

```bash
# Check worker status
./orchestrate.sh celery-status

# Purge queue and restart
./orchestrate.sh celery-purge
./orchestrate.sh restart
```

### Database connection issues

```bash
# Check if database is running
docker-compose exec db psql -U postgres -d fintech -c "SELECT 1;"

# Reinitialize database
docker-compose down -v
docker-compose up -d db
./orchestrate.sh migrate
```

### Redis connection issues

```bash
# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Check Redis usage
docker-compose exec redis redis-cli info memory
```

### ETL task failures

1. Check logs:
```bash
./orchestrate.sh logs web
./orchestrate.sh logs celery_worker
```

2. Check task details in database or Redis
3. Review ETL scripts for data validation errors
4. Ensure raw data files are present in `data/raw/`

## Performance Tuning

### Celery Worker Concurrency

Adjust in docker-compose.yml:
```yaml
celery_worker:
  command: celery -A config worker --concurrency=8
```

- Set to number of CPU cores for CPU-bound tasks
- Can be higher for I/O-bound tasks

### Database Connection Pooling

```python
# In settings.py
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

### Redis Configuration

Update docker-compose.yml:
```yaml
redis:
  command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
```

## Monitoring and Observability

### Flower - Celery Monitoring

Add to docker-compose.yml:
```yaml
flower:
  image: mher/flower
  command: celery --broker=redis://redis:6379/0 flower
  ports:
    - "5555:5555"
  depends_on:
    - redis
    - celery_worker
```

Then access at: http://localhost:5555

### Logging

Logs are written to `/app/logs/`:
- `etl_pipeline.log` - ETL execution logs
- `celery_worker.log` - Celery worker logs

Configure log level in `.env`:
```env
LOG_LEVEL=DEBUG  # or INFO, WARNING, ERROR
```

## Security Considerations

1. **Change default passwords** in `.env` (database, Redis)
2. **Use environment variables** for sensitive data
3. **Enable Redis password** in production:
   ```env
   REDIS_PASSWORD=secure_password_here
   ```
4. **Update Django SECRET_KEY** in `.env`
5. **Use HTTPS** in production
6. **Restrict network access** to services

## Cleanup

### Remove All Data

```bash
./orchestrate.sh clean
```

This removes:
- All containers
- All volumes (database, Redis data)
- Configuration

### Keep Data, Remove Containers

```bash
docker-compose down
```

To restart:
```bash
./orchestrate.sh start
```

## Advanced Topics

### Custom Task Queues

Define in celery config:
```python
app.conf.task_routes = {
    'etl.extract_task': {'queue': 'etl'},
    'etl.transform_task': {'queue': 'etl'},
    'etl.load_task': {'queue': 'etl'},
}
```

### Task Priority

Queue with priority:
```python
from etl_tasks import run_etl_pipeline

task = run_etl_pipeline.apply_async(
    priority=9,  # 0-10, higher = more important
)
```

### Dead Letter Queue

Configure in settings:
```python
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_TRACK_STARTED = True
```

## Support & Documentation

- [Docker Documentation](https://docs.docker.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [Django Documentation](https://docs.djangoproject.com/)

## License

See LICENSE file for details.
