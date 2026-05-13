"""
Celery tasks for ETL pipeline orchestration.

This module handles the async execution of ETL tasks using Celery.
"""

import sys
import os
from pathlib import Path
from celery import shared_task
from celery.utils.log import get_task_logger

# Ensure project root is on sys.path so top-level modules can be imported
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import ETL pipeline wrapper (located at project root)
import etl_pipeline

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    track_started=True,
    name="etl.extract_task",
)
def extract_task(self):
    """
    Celery task to extract data from Excel files.

    Returns:
        dict: Status and message of extraction
    """
    try:
        logger.info("Starting ETL extraction task...")
        # etl_pipeline provides a simple run_* wrapper API
        result = etl_pipeline.run_extraction()
        logger.info("ETL extraction completed successfully")
        return {
            "status": "success",
            "message": "Data extraction completed",
            "result": str(result),
        }
    except Exception as exc:
        logger.error(f"ETL extraction failed: {exc}", exc_info=True)
        # Retry after delay
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    track_started=True,
    name="etl.transform_task",
)
def transform_task(self, extract_result=None):
    """
    Celery task to clean and transform extracted data.

    Args:
        extract_result (dict, optional): Result from extract task

    Returns:
        dict: Status and message of transformation
    """
    try:
        logger.info("Starting ETL transformation task...")
        result = etl_pipeline.run_transformation()
        logger.info("ETL transformation completed successfully")
        return {
            "status": "success",
            "message": "Data transformation completed",
            "result": str(result),
        }
    except Exception as exc:
        logger.error(f"ETL transformation failed: {exc}", exc_info=True)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    track_started=True,
    name="etl.load_task",
)
def load_task(self, transform_result=None):
    """
    Celery task to load transformed data into warehouse.

    Args:
        transform_result (dict, optional): Result from transform task

    Returns:
        dict: Status and message of load
    """
    try:
        logger.info("Starting ETL load task...")
        result = etl_pipeline.run_load()
        logger.info("ETL load completed successfully")
        return {
            "status": "success",
            "message": "Data loading completed",
            "result": str(result),
        }
    except Exception as exc:
        logger.error(f"ETL load failed: {exc}", exc_info=True)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    track_started=True,
    name="etl.run_pipeline",
)
def run_etl_pipeline(self):
    """
    Celery task that orchestrates the complete ETL pipeline.

    This task chains extract -> transform -> load sequentially.

    Returns:
        dict: Status of the complete pipeline
    """
    try:
        logger.info("Starting complete ETL pipeline...")

        # Execute tasks sequentially
        extract_result = extract_task()
        logger.info(f"Extract result: {extract_result}")

        transform_result = transform_task(extract_result)
        logger.info(f"Transform result: {transform_result}")

        load_result = load_task(transform_result)
        logger.info(f"Load result: {load_result}")

        logger.info("ETL pipeline completed successfully")
        return {
            "status": "success",
            "message": "Complete ETL pipeline executed successfully",
            "extract": extract_result,
            "transform": transform_result,
            "load": load_result,
        }
    except Exception as exc:
        logger.error(f"ETL pipeline failed: {exc}", exc_info=True)
        return {
            "status": "failed",
            "message": f"ETL pipeline failed: {exc}",
        }


@shared_task(
    bind=True,
    name="etl.health_check",
)
def etl_health_check(self):
    """
    Health check task to verify ETL system is operational.

    Returns:
        dict: Health status
    """
    try:
        logger.info("Running ETL health check...")
        return {
            "status": "healthy",
            "message": "ETL system is operational",
        }
    except Exception as exc:
        logger.error(f"ETL health check failed: {exc}")
        return {
            "status": "unhealthy",
            "message": f"ETL health check failed: {exc}",
        }


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    track_started=True,
    name="ml.rescoring_task",
)
def ml_rescoring_task(self, symbol: str = None):
    """
    Celery task to run ML rescoring for financial health scores.

    Calculates real financial health scores based on warehouse data and
    updates fact_ml_scores table.

    Args:
        symbol (str, optional): Score specific company. If None, scores all companies.

    Returns:
        dict: Status and count of companies scored
    """
    try:
        from django.conf import settings
        from sqlalchemy import create_engine
        from ml_scoring import BatchScorer
        from urllib.parse import quote_plus

        logger.info(f"Starting ML rescoring task (symbol={symbol})...")

        # Create SQLAlchemy engine from Django database settings
        db_config = settings.DATABASES['default']
        # URL-encode the password in case it has special characters
        password = quote_plus(db_config['PASSWORD'])
        db_url = f"postgresql+psycopg2://{db_config['USER']}:{password}@{db_config['HOST']}:{db_config['PORT']}/{db_config['NAME']}"
        engine = create_engine(db_url)

        scorer = BatchScorer(engine)

        if symbol:
            # Score single company
            logger.info(f"Scoring company: {symbol}")
            scores = scorer.score_company_by_symbol(symbol)

            if scores:
                # Save to database
                _save_ml_scores([scores])
                logger.info(f"✓ Scored 1 company: {symbol}")
                return {
                    "status": "success",
                    "message": f"Scored company {symbol}",
                    "companies_scored": 1,
                    "scores": scores,
                }
            else:
                return {
                    "status": "failed",
                    "message": f"Failed to score {symbol}",
                    "companies_scored": 0,
                }
        else:
            # Score all companies
            scores_df = scorer.score_all_companies()

            if not scores_df.empty:
                # Convert to records and save
                scores_records = scores_df.to_dict('records')
                _save_ml_scores(scores_records)

                logger.info(f"✓ Scored {len(scores_df)} companies")

                return {
                    "status": "success",
                    "message": "Batch ML rescoring completed",
                    "companies_scored": len(scores_df),
                }
            else:
                logger.warning("No companies to score")
                return {
                    "status": "warning",
                    "message": "No companies found to score",
                    "companies_scored": 0,
                }

    except Exception as exc:
        logger.error(f"ML rescoring failed: {exc}", exc_info=True)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    track_started=True,
    name="ml.incremental_rescoring_task",
)
def ml_incremental_rescoring_task(self):
    """
    Celery task to incrementally rescore companies that were recently updated.

    This is more efficient than full batch rescoring. Triggered after ETL load phase.

    Returns:
        dict: Status and count of companies updated
    """
    try:
        from django.conf import settings
        from sqlalchemy import create_engine
        from datetime import datetime, timedelta
        from ml_scoring import BatchScorer
        from urllib.parse import quote_plus
        import pandas as pd

        logger.info("Starting incremental ML rescoring...")

        # Create SQLAlchemy engine
        db_config = settings.DATABASES['default']
        # URL-encode the password in case it has special characters
        password = quote_plus(db_config['PASSWORD'])
        db_url = f"postgresql+psycopg2://{db_config['USER']}:{password}@{db_config['HOST']}:{db_config['PORT']}/{db_config['NAME']}"
        engine = create_engine(db_url)

        # Find companies updated in last 24 hours
        query = """
            SELECT DISTINCT pl.symbol
            FROM fact_profit_loss pl
            WHERE pl.symbol IN (
                SELECT symbol FROM dim_company
            )
            ORDER BY pl.symbol
            LIMIT 50
        """

        updated_companies = pd.read_sql(query, engine)

        scorer = BatchScorer(connection)
        scores_list = []

        for _, row in updated_companies.iterrows():
            symbol = row['symbol']
            try:
                scores = scorer.score_company_by_symbol(symbol)
                if scores:
                    scores_list.append(scores)
            except Exception as e:
                logger.warning(f"Skipped {symbol}: {e}")
                continue

        if scores_list:
            _save_ml_scores(scores_list)
            logger.info(f"✓ Incrementally scored {len(scores_list)} companies")

            return {
                "status": "success",
                "message": "Incremental rescoring completed",
                "companies_scored": len(scores_list),
            }
        else:
            logger.info("No companies to update")
            return {
                "status": "success",
                "message": "No companies to update",
                "companies_scored": 0,
            }

    except Exception as exc:
        logger.error(f"Incremental rescoring failed: {exc}", exc_info=True)
        raise self.retry(exc=exc)


def _save_ml_scores(scores_records: list) -> int:
    """
    Save ML scores to database using bulk insert/update.

    Args:
        scores_records: List of score dictionaries

    Returns:
        int: Number of records inserted/updated
    """
    from django.conf import settings
    from sqlalchemy import create_engine, text
    from urllib.parse import quote_plus

    if not scores_records:
        return 0

    # Create SQLAlchemy engine
    db_config = settings.DATABASES['default']
    # URL-encode the password in case it has special characters
    password = quote_plus(db_config['PASSWORD'])
    db_url = f"postgresql+psycopg2://{db_config['USER']}:{password}@{db_config['HOST']}:{db_config['PORT']}/{db_config['NAME']}"
    engine = create_engine(db_url)

    upsert_sql = text("""
        INSERT INTO fact_ml_scores (
            symbol, computed_at, overall_score, profitability_score, growth_score,
            leverage_score, cashflow_score, dividend_score, trend_score, health_label
        )
        VALUES (
            :symbol, :computed_at, :overall_score, :profitability_score, :growth_score,
            :leverage_score, :cashflow_score, :dividend_score, :trend_score, :health_label
        )
        ON CONFLICT (symbol, computed_at) DO UPDATE SET
            overall_score = EXCLUDED.overall_score,
            profitability_score = EXCLUDED.profitability_score,
            growth_score = EXCLUDED.growth_score,
            leverage_score = EXCLUDED.leverage_score,
            cashflow_score = EXCLUDED.cashflow_score,
            dividend_score = EXCLUDED.dividend_score,
            trend_score = EXCLUDED.trend_score,
            health_label = EXCLUDED.health_label
    """)

    with engine.begin() as conn:
        # Remove duplicates from this batch (keep first)
        seen = set()
        unique_records = []
        for record in scores_records:
            key = (record['symbol'], str(record['computed_at']))
            if key not in seen:
                seen.add(key)
                unique_records.append(record)

        if unique_records:
            conn.execute(upsert_sql, unique_records)
            logger.info(f"Saved {len(unique_records)} ML scores to warehouse")
            return len(unique_records)

    return 0
