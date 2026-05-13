import os

import redis

from rest_framework.throttling import BaseThrottle

from .auth import verify_hmac


redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=int(os.getenv("REDIS_DB", "1")),
    decode_responses=True,
)


WINDOWS = {
    "minute": 60,
    "hour": 3600,
    "day": 86400,
}


TIER_LIMITS = {
    "BASIC": {
        "minute": 10,
        "hour": 100,
        "day": 500,
    },
    "PRO": {
        "minute": 60,
        "hour": 1000,
        "day": 10000,
    },
    "ENTERPRISE": {
        "minute": 300,
        "hour": 10000,
        "day": 999999999,
    },
}


class PartnerRateThrottle(BaseThrottle):

    def _build_key(self, client_key, window):
        return f"rate_limit:{client_key}:{window}"


    def _window_limits(self, client):
        return TIER_LIMITS.get(client.tier, TIER_LIMITS["BASIC"])


    def _snapshot(self, client, client_key):
        limits = self._window_limits(client)
        usage = {}
        remaining = {}
        retry_after = 60

        for window, seconds in WINDOWS.items():
            redis_key = self._build_key(client_key, window)
            current_count = int(redis_client.get(redis_key) or 0)
            ttl = redis_client.ttl(redis_key)

            usage[window] = {
                "used": current_count,
                "limit": limits[window],
                "remaining": max(limits[window] - current_count, 0),
            }
            remaining[window] = usage[window]["remaining"]

            if current_count >= limits[window]:
                return {
                    "limits": limits,
                    "usage": usage,
                    "remaining": remaining,
                    "retry_after": ttl if ttl and ttl > 0 else seconds,
                    "window": window,
                }

            if ttl and ttl > 0:
                retry_after = min(retry_after, ttl)

        return {
            "limits": limits,
            "usage": usage,
            "remaining": remaining,
            "retry_after": retry_after,
            "window": None,
        }


    def allow_request(self, request, view):
        client = verify_hmac(request)

        if not client:
            return True

        client_key = str(client.key_id)
        snapshot = self._snapshot(client, client_key)

        if snapshot["window"]:
            view._partner_throttle_details = {
                "error": "Rate limit exceeded",
                "tier": client.tier,
                "client": str(client.key_id),
                "quota": snapshot,
            }
            self.wait_time = snapshot["retry_after"]
            return False

        pipe = redis_client.pipeline()
        for window, seconds in WINDOWS.items():
            redis_key = self._build_key(client_key, window)
            pipe.incr(redis_key, 1)
            pipe.expire(redis_key, seconds)
        pipe.execute()

        view._partner_throttle_details = {
            "tier": client.tier,
            "client": str(client.key_id),
            "quota": snapshot,
        }
        return True


    def wait(self):
        return getattr(self, "wait_time", 60)