import logging
import os
import sys
import time
import uuid
from typing import IO, Iterable, Optional

from flask import Flask, g, request

from .filters import SkipRule, default_skip_rules
from .formatter import JsonFormatter, build_payload


_HANDLER_MARKER = "_access_log_py_handler"


def _configure_logger(name: str, stream: IO[str]) -> logging.Logger:
    logger = logging.getLogger(name)
    if any(getattr(h, _HANDLER_MARKER, False) for h in logger.handlers):
        return logger
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    setattr(handler, _HANDLER_MARKER, True)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def install(
    app: Flask,
    *,
    source: str,
    logger_name: str = "access",
    skip_rules: Optional[Iterable[SkipRule]] = None,
    output_stream: Optional[IO[str]] = None,
) -> None:
    """Install JSON access log middleware on the given Flask app.

    Each request emits exactly one JSON line to `output_stream` (default stdout)
    via the Python `logging` channel named `logger_name`.

    Args:
        app: Flask application instance.
        source: Service identifier emitted as the `source` field. Overridden by
                the `ACCESS_LOG_SOURCE` env var when set, so the same container
                image can be reused across services with the value stamped at
                deploy time (e.g. via Helm).
        logger_name: Python logging channel name. Default `"access"`.
        skip_rules: Iterable of `SkipRule` defining traffic to suppress. Pass
                    `[]` to log everything. Defaults to `default_skip_rules()`
                    which drops K8s probes.
        output_stream: File-like to write JSON records to. Defaults to
                       `sys.stdout`. Tests typically pass an `io.StringIO`.

    Side effects:
        - Registers `before_request` and two `after_request` hooks on `app`.
        - Sets the response header `X-Request-ID` on every response.
        - Configures a Python logger; subsequent calls with the same
          `logger_name` are idempotent (handler is added at most once).
    """
    resolved_source = os.environ.get("ACCESS_LOG_SOURCE", source)
    rules = list(skip_rules) if skip_rules is not None else default_skip_rules()
    logger = _configure_logger(logger_name, output_stream or sys.stdout)

    @app.before_request
    def _begin():
        g.request_start = time.perf_counter()
        g.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        g.access_logged = False

    @app.after_request
    def _attach_request_id(response):
        try:
            response.headers["X-Request-ID"] = g.get("request_id", "")
        except Exception:
            pass
        return response

    @app.after_request
    def _emit_access_log(response):
        if g.get("access_logged"):
            return response
        if any(rule.matches() for rule in rules):
            g.access_logged = True
            return response
        try:
            logger.info("", extra={"payload": build_payload(response, resolved_source)})
            g.access_logged = True
        except Exception:
            pass
        return response
