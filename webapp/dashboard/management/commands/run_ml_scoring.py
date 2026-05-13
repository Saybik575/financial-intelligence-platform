"""
Django management command to trigger ML rescoring via Celery.

Usage:
    python manage.py run_ml_scoring [--async] [--symbol SYMBOL]
"""

from django.core.management.base import BaseCommand, CommandError
from etl_tasks import ml_rescoring_task, ml_incremental_rescoring_task


class Command(BaseCommand):
    """Management command to run ML scoring tasks."""

    help = "Run ML rescoring tasks via Celery"

    def add_arguments(self, parser):
        """Add command-line arguments."""
        parser.add_argument(
            "--async",
            action="store_true",
            help="Run rescoring asynchronously (queue and return immediately)",
        )
        parser.add_argument(
            "--symbol",
            type=str,
            default=None,
            help="Score specific company by symbol (e.g., TCS, INFY)",
        )
        parser.add_argument(
            "--incremental",
            action="store_true",
            help="Run incremental rescoring only (recently updated companies)",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        async_mode = options.get("async", False)
        symbol = options.get("symbol", None)
        incremental = options.get("incremental", False)

        try:
            if incremental:
                self.stdout.write(
                    self.style.HTTP_INFO("Triggering incremental ML rescoring...")
                )
                if async_mode:
                    task = ml_incremental_rescoring_task.delay()
                    task_id = task.id
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Incremental rescoring queued (ID: {task_id})"
                        )
                    )
                else:
                    result = ml_incremental_rescoring_task()
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Incremental rescoring completed")
                    )
                    self._print_result(result)

            elif symbol:
                self.stdout.write(
                    self.style.HTTP_INFO(f"Triggering ML rescoring for {symbol}...")
                )
                if async_mode:
                    task = ml_rescoring_task.delay(symbol=symbol)
                    task_id = task.id
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Rescoring for {symbol} queued (ID: {task_id})"
                        )
                    )
                else:
                    result = ml_rescoring_task(symbol=symbol)
                    if result.get('status') == 'success':
                        self.stdout.write(
                            self.style.SUCCESS(f"✓ Rescoring completed for {symbol}")
                        )
                        self._print_result(result)
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"✗ Rescoring failed: {result.get('message')}")
                        )

            else:
                # Full batch rescoring
                self.stdout.write(
                    self.style.HTTP_INFO("Triggering full batch ML rescoring...")
                )
                if async_mode:
                    task = ml_rescoring_task.delay()
                    task_id = task.id
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Full rescoring queued (ID: {task_id})"
                        )
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            "ℹ This may take 5-10 minutes for large datasets"
                        )
                    )
                else:
                    result = ml_rescoring_task()
                    if result.get('status') == 'success':
                        self.stdout.write(
                            self.style.SUCCESS(f"✓ Full rescoring completed")
                        )
                        self._print_result(result)
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"✗ Rescoring failed: {result.get('message')}")
                        )

        except Exception as e:
            raise CommandError(f"ML rescoring execution failed: {e}")

    def _print_result(self, result: dict):
        """Pretty print rescoring result."""
        self.stdout.write(
            self.style.SUCCESS(f"  Message: {result.get('message', 'N/A')}")
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"  Companies scored: {result.get('companies_scored', 0)}"
            )
        )

        # Print individual scores if single company
        if 'scores' in result and result['scores']:
            scores = result['scores']
            self.stdout.write("\n  Score Breakdown:")
            self.stdout.write(f"    Overall Score: {scores.get('overall_score', 0):.1f}")
            self.stdout.write(f"    Health Label: {scores.get('health_label', 'N/A')}")
            self.stdout.write(
                f"    Profitability: {scores.get('profitability_score', 0):.1f}"
            )
            self.stdout.write(
                f"    Growth: {scores.get('growth_score', 0):.1f}"
            )
            self.stdout.write(
                f"    Leverage: {scores.get('leverage_score', 0):.1f}"
            )
            self.stdout.write(
                f"    Cash Flow: {scores.get('cashflow_score', 0):.1f}"
            )
            self.stdout.write(
                f"    Dividend: {scores.get('dividend_score', 0):.1f}"
            )
            self.stdout.write(
                f"    Trend: {scores.get('trend_score', 0):.1f}"
            )
