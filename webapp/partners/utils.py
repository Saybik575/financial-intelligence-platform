import secrets
from .models import WebhookSubscription, WebhookEvent
from .tasks import send_webhook_event
from companies.models import Company


def generate_api_secret():

    return secrets.token_hex(32)


def dispatch_webhook(event_type, company_symbol, company_data=None):
    """
    Dispatch webhook events to all subscribed partners.
    
    Args:
        event_type: 'score_updated' or 'anomaly_flagged'
        company_symbol: Company symbol (e.g., 'TCS')
        company_data: Optional dict with additional data
    """
    try:
        company = Company.objects.get(symbol=company_symbol)
    except Company.DoesNotExist:
        return None
    
    # Find all active subscriptions for this event
    subscriptions = WebhookSubscription.objects.filter(
        event_type=event_type,
        is_active=True
    )
    
    # Create event records and dispatch tasks
    for subscription in subscriptions:
        webhook_event = WebhookEvent.objects.create(
            webhook_subscription=subscription,
            event_type=event_type,
            company_symbol=company_symbol,
            status="pending"
        )
        
        # Dispatch async task
        send_webhook_event.delay(
            webhook_event.id,
            event_type,
            company_symbol,
            company_data or {}
        )
    
    return len(subscriptions)