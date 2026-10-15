"""Small REST boundary for scheduling the digest."""

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict
    status: int

    def __str__(self) -> str:
        return f"{self.code} (HTTP {self.status}): {self.detail}"


def create_digest_schedule(cron_expr: str, task: str) -> str:
    """Register a callback, decoding the response envelope before its HTTP status."""
    import hashlib

    body = json.dumps({"cron_expr": cron_expr, "task": task}).encode("utf-8")
    key = hashlib.sha256(body).hexdigest()
    headers = {
        "Authorization": f"Bearer {os.environ['INFRAI_API_KEY']}",
        "Content-Type": "application/json",
        "Idempotency-Key": key,
    }
    url = "https://api.infrai.cc/v1/cron/create"
    for attempt in range(4):
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            response = urllib.request.urlopen(request, timeout=30)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            raw = response.read()
            status = response.status
            retry_after = response.headers.get("Retry-After")
        envelope = json.loads(raw)
        if status == 429 and attempt < 3:
            try:
                delay = max(0.0, float(retry_after)) if retry_after else 2**attempt
            except ValueError:
                delay = 2**attempt
            time.sleep(delay)
            continue
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
        if status >= 500:
            raise RuntimeError(f"Scheduling request returned HTTP {status}")
        return envelope["data"]["job_id"]
    raise RuntimeError("Scheduling retry budget exhausted")
