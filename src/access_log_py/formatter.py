import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict

from flask import g, request


class JsonFormatter(logging.Formatter):
    """Serializes the structured `payload` extra into a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(getattr(record, "payload", {}), default=str, ensure_ascii=False)


def _client_address():
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        first = xff.split(",", 1)[0].strip()
        if first:
            return first
    return request.remote_addr


def _proxy_add_xff():
    xff = request.headers.get("X-Forwarded-For")
    remote = request.remote_addr or ""
    if xff:
        return f"{xff}, {remote}" if remote else xff
    return remote or None


def _request_uri():
    full = request.full_path
    return full[:-1] if full.endswith("?") and not request.query_string else full


def build_payload(response, source: str) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "source": source,
        "time": now.isoformat(timespec="milliseconds"),
        "timestamp": round(now.timestamp(), 3),
        "host": request.host,
        "client_address": _client_address(),
        "x_forwarded_for": request.headers.get("X-Forwarded-For"),
        "x_real_ip": request.headers.get("X-Real-IP"),
        "x_forwarded_proto": request.headers.get("X-Forwarded-Proto"),
        "proxy_add_x_forwarded_for": _proxy_add_xff(),
        "protocol": request.environ.get("SERVER_PROTOCOL"),
        "method": request.method,
        "uri": _request_uri(),
        "status": response.status_code,
        "request_length": request.content_length or 0,
        "resp_body_size": response.calculate_content_length() or 0,
        "resp_time": round(time.perf_counter() - g.get("request_start", time.perf_counter()), 3),
        "http_referer": request.referrer,
        "user_agent": request.user_agent.string or None,
        "request_id": g.get("request_id"),
    }
