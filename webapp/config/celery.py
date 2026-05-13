import os

from celery import Celery


os.environ.setdefault(

    "DJANGO_SETTINGS_MODULE",

    "config.settings"
)


app = Celery("config")


app.config_from_object(

    "django.conf:settings",

    namespace="CELERY"
)


app.autodiscover_tasks()

# Explicitly import etl_tasks module to register tasks
from etl_tasks import (
    extract_task,
    transform_task,
    load_task,
    run_etl_pipeline,
    ml_rescoring_task,
    ml_incremental_rescoring_task,
)