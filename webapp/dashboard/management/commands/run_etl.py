"""
Django management command to trigger ETL pipeline via Celery.

Usage:
    python manage.py run_etl [--async] [--extract] [--transform] [--load] [--with-scoring]
"""

from django.core.management.base import BaseCommand, CommandError
from etl_tasks import run_etl_pipeline, extract_task, transform_task, load_task
from ml_scoring import BatchScorer


class Command(BaseCommand):
    """Management command to run ETL tasks."""

    help = "Run ETL pipeline tasks via Celery"

    def add_arguments(self, parser):
        """Add command-line arguments."""
        parser.add_argument(
            "--async",
            action="store_true",
            help="Run tasks asynchronously (queue them and return immediately)",
        )
        parser.add_argument(
            "--extract",
            action="store_true",
            help="Run only extraction task",
        )
        parser.add_argument(
            "--transform",
            action="store_true",
            help="Run only transformation task",
        )
        parser.add_argument(
            "--load",
            action="store_true",
            help="Run only load task",
        )
        parser.add_argument(
            "--with-scoring",
            action="store_true",
            help="Run ML rescoring after load phase",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        async_mode = options.get("async", False)
        extract_only = options.get("extract", False)
        transform_only = options.get("transform", False)
        load_only = options.get("load", False)
        with_scoring = options.get("with_scoring", False)

        try:
            if extract_only:
                self.stdout.write(self.style.HTTP_INFO("Triggering extraction task..."))
                if async_mode:
                    task = extract_task.delay()
                else:
                    result = extract_task()
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Extraction completed: {result}")
                    )
                    return
                task_id = task.id
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Extraction task queued (ID: {task_id})")
                )

            elif transform_only:
                self.stdout.write(self.style.HTTP_INFO("Triggering transformation task..."))
                if async_mode:
                    task = transform_task.delay()
                else:
                    result = transform_task()
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Transformation completed: {result}")
                    )
                    return
                task_id = task.id
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Transformation task queued (ID: {task_id})")
                )

            elif load_only:
                self.stdout.write(self.style.HTTP_INFO("Triggering load task..."))
                if async_mode:
                    task = load_task.delay()
                    task_id = task.id
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Load task queued (ID: {task_id})")
                    )
                    # Queue scoring task after load
                    if with_scoring:
                        from etl_tasks import ml_incremental_rescoring_task
                        scoring_task = ml_incremental_rescoring_task.apply_async(
                            countdown=5  # Wait 5 seconds for load to complete
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ ML rescoring queued after load (ID: {scoring_task.id})"
                            )
                        )
                else:
                    result = load_task()
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Load completed: {result}")
                    )
                    # Run scoring synchronously if requested
                    if with_scoring:
                        self._run_scoring_sync()
                return

            else:
                # Run full pipeline
                self.stdout.write(self.style.HTTP_INFO("Triggering full ETL pipeline..."))
                if async_mode:
                    task = run_etl_pipeline.delay()
                    task_id = task.id
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ ETL pipeline queued for async execution (ID: {task_id})"
                        )
                    )
                    # Queue scoring after pipeline
                    if with_scoring:
                        from etl_tasks import ml_incremental_rescoring_task
                        scoring_task = ml_incremental_rescoring_task.apply_async(
                            countdown=10  # Wait 10 seconds for full pipeline
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ ML rescoring queued after pipeline (ID: {scoring_task.id})"
                            )
                        )
                else:
                    result = run_etl_pipeline()
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ ETL pipeline completed: {result}")
                    )
                    # Run scoring synchronously if requested
                    if with_scoring:
                        self._run_scoring_sync()

        except Exception as e:
            raise CommandError(f"ETL execution failed: {e}")

    def _run_scoring_sync(self):
        """Run ML scoring synchronously."""
        try:
            self.stdout.write(
                self.style.HTTP_INFO("Running ML rescoring (this may take a minute)...")
            )
            from etl_tasks import ml_rescoring_task

            result = ml_rescoring_task()
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ ML rescoring completed ({result.get('companies_scored', 0)} companies scored)"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ ML rescoring failed: {e}")
            )
