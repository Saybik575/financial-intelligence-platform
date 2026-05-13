import hmac

import hashlib

from django.http import JsonResponse
from django.core.exceptions import ValidationError

from .models import (
    APIClient,
    APINonce,
)

import time

def verify_hmac(request):

    cached_client = getattr(
        request,
        "_partner_client",
        None
    )

    if cached_client is not None:

        return cached_client

    api_key = request.headers.get(
        "X-API-KEY"
    )

    signature = request.headers.get(
        "X-SIGNATURE"
    )

    timestamp = request.headers.get(
        "X-TIMESTAMP"
    )

    nonce = request.headers.get(
        "X-NONCE"
    )

    if not timestamp or not nonce:

        return None

    try:
        current_time = int(time.time())
        request_time = int(timestamp)
    except (TypeError, ValueError):
        return None

    if abs(current_time - request_time) > 300:

        return None
    
    if not api_key or not signature:

        return None

    try:
        client = APIClient.objects.filter(
            key_id=api_key,
            is_active=True
        ).first()
    except (ValidationError, ValueError, TypeError):
        return None

    if not client:

        return None
    
    existing_nonce = APINonce.objects.filter(
        client=client,
        nonce=nonce
    ).exists()

    if existing_nonce:

        return None

    APINonce.objects.create(
        client=client,
        nonce=nonce
    )

    body = request.body or b""

    body_hash = hashlib.sha256(
        body
    ).hexdigest()

    payload = "\n".join([

        request.method,

        request.get_full_path(),

        timestamp,

        body_hash,

        nonce,
    ])

    generated_signature = hmac.new(

        client.secret_encrypted.encode(),

        payload.encode(),

        hashlib.sha256

    ).hexdigest()

    if not hmac.compare_digest(
        generated_signature,
        signature
    ):

        return None

    request._partner_client = client

    return client