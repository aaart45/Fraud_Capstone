import os
import time
import hashlib
from django.http import JsonResponse
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin

class SimpleRateLimit(MiddlewareMixin):
    """
    Limits POSTs to /api/v1/predict/ (and legacy /api/predict/) per client IP.
    Uses Django cache (LocMemCache by default); OK for single-instance demo.
    Configure with env:
        RL_MAX_CALLS   default 30
        RL_WINDOW_SEC  default 60
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method != "POST":
            return None
        if request.path not in ("/api/v1/predict/", "/api/predict/"):
            return None

        limit = int(os.getenv("RL_MAX_CALLS", "30"))
        window = int(os.getenv("RL_WINDOW_SEC", "60"))
        ip = request.META.get("REMOTE_ADDR", "unknown")

        seed = f"{ip}:{request.path}"
        key = "rl:" + hashlib.sha1(seed.encode()).hexdigest()

        now = int(time.time())
        data = cache.get(key)  # (start_ts, count)

        if not data:
            cache.set(key, (now, 1), timeout=window)
            return None

        start, count = data
        elapsed = now - start

        if elapsed >= window:
            cache.set(key, (now, 1), timeout=window)
            return None

        if count >= limit:
            retry = max(1, window - elapsed)
            return JsonResponse(
                {"error": "rate_limited", "detail": f"Too many requests. Try again in {retry}s."},
                status=429,
            )

        # increment
        cache.set(key, (start, count + 1), timeout=max(1, window - elapsed))
        return None
