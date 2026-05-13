import uuid

from django.db import models

TIER_CHOICES = [

    ("BASIC", "Basic"),

    ("PRO", "Pro"),

    ("ENTERPRISE", "Enterprise"),
]

class APIClient(models.Model):

    tier = models.CharField(

        max_length=20,

        choices=TIER_CHOICES,

        default="BASIC"
    )

    name = models.CharField(
        max_length=255
    )

    key_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    secret_encrypted = models.CharField(
        max_length=255
    )

    rate_limit_per_minute = models.IntegerField(
        default=60
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.name
    
class APINonce(models.Model):

    client = models.ForeignKey(
        APIClient,
        on_delete=models.CASCADE
    )

    nonce = models.UUIDField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        unique_together = (
            "client",
            "nonce",
        )

class WebhookSubscription(models.Model):

    EVENT_CHOICES = [

        ("score_updated", "Score Updated"),

        ("anomaly_flagged", "Anomaly Flagged"),
    ]

    client = models.ForeignKey(

        APIClient,

        on_delete=models.CASCADE
    )

    target_url = models.URLField()

    event_type = models.CharField(

        max_length=100,

        choices=EVENT_CHOICES
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return (
            f"{self.client.name} - "
            f"{self.event_type}"
        )
    
class APIUsageLog(models.Model):

    client = models.ForeignKey(

        APIClient,

        on_delete=models.SET_NULL,

        null=True
    )

    endpoint = models.CharField(
        max_length=500
    )

    method = models.CharField(
        max_length=10
    )

    status_code = models.IntegerField()

    response_time_ms = models.FloatField()

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    request_size = models.IntegerField(
        default=0
    )

    response_size = models.IntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return (
            f"{self.method} "
            f"{self.endpoint}"
        )

class WebhookEvent(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("retrying", "Retrying"),
    ]

    webhook_subscription = models.ForeignKey(
        WebhookSubscription,
        on_delete=models.CASCADE,
        related_name="events"
    )

    event_type = models.CharField(
        max_length=100,
        choices=WebhookSubscription.EVENT_CHOICES
    )

    company_symbol = models.CharField(
        max_length=20
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    response_code = models.IntegerField(
        null=True,
        blank=True
    )

    error_message = models.TextField(
        null=True,
        blank=True
    )

    next_retry_at = models.DateTimeField(
        null=True,
        blank=True
    )

    attempt_count = models.IntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"{self.webhook_subscription.client.name} - "
            f"{self.event_type} - {self.company_symbol}"
        )