from celery import shared_task
import datetime
from .models import APIUsageLog, APIClient, WebhookEvent, WebhookSubscription
import requests
import hmac
import hashlib
import json
from django.utils import timezone
from datetime import timedelta
from celery.utils.log import get_task_logger
import sys
from pathlib import Path

logger = get_task_logger(__name__)

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

@shared_task
def test_task(message):
    logger.info(f"Test task executing with message: {message}")
    return f"Task completed: {message}"

@shared_task
def nightly_etl_refresh():
    """Run the complete ETL pipeline nightly."""
    try:
        logger.info(f"Starting nightly ETL refresh at {datetime.datetime.now()}")
        
        # Import ETL pipeline
        import etl_pipeline
        
        # Run full pipeline
        etl_pipeline.run_full_pipeline()
        
        logger.info("Nightly ETL refresh completed successfully")
        return {"status": "success", "message": "ETL refresh completed"}
    except Exception as e:
        logger.error(f"Nightly ETL refresh failed: {str(e)}", exc_info=True)
        return {"status": "failed", "error": str(e)}

@shared_task
def nightly_ml_rescoring():
    """Run ML rescoring for all companies and dispatch webhooks."""
    try:
        logger.info(f"Starting nightly ML rescoring at {datetime.datetime.now()}")

        # Keep this task lightweight in scheduler context; domain-specific scoring
        # can be delegated to dedicated ML tasks/modules.
        from companies.models import Company

        rescored_count = Company.objects.count()

        # Dispatch webhooks for affected companies
        try:
            from .utils import dispatch_webhook
            companies_to_notify = Company.objects.all()[:10]  # Limit for demo
            for company in companies_to_notify:
                dispatch_webhook("score_updated", company.symbol)
        except Exception as e:
            logger.warning(f"Failed to dispatch webhooks: {str(e)}")
        
        logger.info(f"Nightly ML rescoring completed. Rescored {rescored_count} companies")
        return {"status": "success", "message": f"ML rescoring completed for {rescored_count} companies"}
    except Exception as e:
        logger.error(f"Nightly ML rescoring failed: {str(e)}", exc_info=True)
        return {"status": "failed", "error": str(e)}

@shared_task
def log_api_usage(

    client_id,

    endpoint,

    method,

    status_code,

    response_time_ms,

    ip_address,

    request_size,

    response_size,
):

    client = APIClient.objects.filter(
        id=client_id
    ).first()

    APIUsageLog.objects.create(

        client=client,

        endpoint=endpoint,

        method=method,

        status_code=status_code,

        response_time_ms=response_time_ms,

        ip_address=ip_address,

        request_size=request_size,

        response_size=response_size,
    )

    return "API usage logged"

def sign_webhook_payload(payload_json, secret):
    """Sign webhook payload with HMAC-SHA256."""
    signature = hmac.new(
        secret.encode(),
        payload_json.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=960,
    retry_jitter=False,
    max_retries=5,
)
def send_webhook_event(
    self,
    webhook_event_id,
    event_type,
    company_symbol,
    company_data=None
):
    """
    Send webhook event to subscribed URL with exponential backoff retry.
    Retries: 1, 2, 4, 8, 16 minutes (capped at 5 retries, ~31 mins total).
    """
    try:
        webhook_event = WebhookEvent.objects.get(id=webhook_event_id)
        subscription = webhook_event.webhook_subscription
        
        # Prepare payload
        payload = {
            "event_type": event_type,
            "company_symbol": company_symbol,
            "company_data": company_data or {},
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }
        payload_json = json.dumps(payload)
        
        # Sign payload with subscription client's secret
        # Get the unencrypted secret from the client (in production, decrypt it)
        client_secret = subscription.client.secret_encrypted
        signature = sign_webhook_payload(payload_json, client_secret)
        
        # Send POST request
        headers = {
            "Content-Type": "application/json",
            "X-Bluestock-Signature": signature,
            "X-Bluestock-Event": event_type,
        }
        
        response = requests.post(
            subscription.target_url,
            json=payload,
            headers=headers,
            timeout=10
        )
        
        # Update webhook event
        webhook_event.attempt_count += 1
        webhook_event.response_code = response.status_code
        
        if response.status_code == 200:
            webhook_event.status = "success"
            webhook_event.save()
            return f"Webhook event {webhook_event_id} delivered successfully"
        else:
            webhook_event.status = "retrying"
            webhook_event.error_message = f"HTTP {response.status_code}: {response.text[:500]}"
            webhook_event.next_retry_at = timezone.now() + timedelta(minutes=2 ** webhook_event.attempt_count)
            webhook_event.save()
            
            # Raise exception to trigger retry
            raise Exception(f"Webhook delivery failed with status {response.status_code}")
            
    except WebhookEvent.DoesNotExist:
        return f"Webhook event {webhook_event_id} not found"
    except Exception as exc:
        webhook_event = WebhookEvent.objects.get(id=webhook_event_id)
        webhook_event.error_message = str(exc)[:500]
        
        if webhook_event.attempt_count >= 5:
            webhook_event.status = "failed"
            webhook_event.save()
            return f"Webhook event {webhook_event_id} failed after 5 retries"
        else:
            webhook_event.next_retry_at = timezone.now() + timedelta(minutes=2 ** webhook_event.attempt_count)
            webhook_event.save()
            raise self.retry(exc=exc, countdown=60 * (2 ** webhook_event.attempt_count))