import io
import json
import uuid

import pytest
from flask import Flask

from access_log_py import SkipRule, install


def _records(buffer):
    return [json.loads(line) for line in buffer.getvalue().splitlines() if line.strip()]


@pytest.fixture
def make_app():
    """Factory that builds a fresh Flask app + middleware with a unique logger
    name per call, so handlers from one test don't leak into the next."""

    def _make(*, source="test", skip_rules=None):
        buffer = io.StringIO()
        app = Flask(__name__)

        @app.route("/")
        def index():
            return "ok"

        @app.route("/echo")
        def echo():
            return "echo"

        install(
            app,
            source=source,
            logger_name=f"test.access.{uuid.uuid4().hex}",
            skip_rules=skip_rules,
            output_stream=buffer,
        )
        return app, buffer

    return _make


def test_emits_one_json_record_per_request(make_app):
    app, buffer = make_app()
    client = app.test_client()
    client.get("/echo")

    records = _records(buffer)
    assert len(records) == 1
    rec = records[0]
    assert rec["source"] == "test"
    assert rec["method"] == "GET"
    assert rec["uri"] == "/echo"
    assert rec["status"] == 200
    assert "request_id" in rec and rec["request_id"]
    assert "resp_time" in rec
    assert rec["resp_body_size"] == 4  # "echo"


def test_request_id_inbound_is_propagated(make_app):
    app, buffer = make_app()
    client = app.test_client()
    response = client.get("/echo", headers={"X-Request-ID": "abc123"})

    assert response.headers["X-Request-ID"] == "abc123"
    assert _records(buffer)[0]["request_id"] == "abc123"


def test_request_id_generated_when_missing(make_app):
    app, buffer = make_app()
    client = app.test_client()
    response = client.get("/echo")

    assert response.headers["X-Request-ID"]
    assert len(response.headers["X-Request-ID"]) == 32  # uuid4 hex length
    assert _records(buffer)[0]["request_id"] == response.headers["X-Request-ID"]


def test_kube_probe_default_is_skipped(make_app):
    app, buffer = make_app()
    client = app.test_client()
    client.get("/", headers={"User-Agent": "kube-probe/1.33"})
    client.get("/", headers={"User-Agent": "Mozilla/5.0"})

    records = _records(buffer)
    assert len(records) == 1
    assert records[0]["user_agent"].startswith("Mozilla/")


def test_empty_skip_rules_logs_everything(make_app):
    app, buffer = make_app(skip_rules=[])
    client = app.test_client()
    client.get("/", headers={"User-Agent": "kube-probe/1.33"})

    assert len(_records(buffer)) == 1


def test_custom_skip_rule_overrides_default(make_app):
    app, buffer = make_app(skip_rules=[SkipRule(path="/echo")])
    client = app.test_client()
    client.get("/")        # logged
    client.get("/echo")    # skipped

    records = _records(buffer)
    assert len(records) == 1
    assert records[0]["uri"] == "/"


def test_x_forwarded_for_drives_client_address(make_app):
    app, buffer = make_app()
    client = app.test_client()
    client.get("/echo", headers={"X-Forwarded-For": "203.0.113.7, 10.0.0.1"})

    rec = _records(buffer)[0]
    assert rec["client_address"] == "203.0.113.7"
    assert rec["x_forwarded_for"] == "203.0.113.7, 10.0.0.1"


def test_env_overrides_source(monkeypatch, make_app):
    monkeypatch.setenv("ACCESS_LOG_SOURCE", "env-stamped-name")
    app, buffer = make_app(source="code-default")
    client = app.test_client()
    client.get("/echo")

    assert _records(buffer)[0]["source"] == "env-stamped-name"


def test_query_string_preserved_in_uri(make_app):
    app, buffer = make_app()
    client = app.test_client()
    client.get("/echo?foo=bar&baz=1")

    assert _records(buffer)[0]["uri"] == "/echo?foo=bar&baz=1"


def test_path_only_strips_trailing_question_mark(make_app):
    app, buffer = make_app()
    client = app.test_client()
    client.get("/echo")

    assert _records(buffer)[0]["uri"] == "/echo"
