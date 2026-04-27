# access-log-py

JSON access log middleware for Flask, shaped to mirror the BasharSoft nginx access log schema. One JSON line per request to stdout — drop-in for any Flask + gunicorn service so a single log pipeline mapping covers nginx and Python services alike.

## Install

This package is not on PyPI. Install it directly from the GitHub repo, pinned to a tag:

```
# requirements.txt
access-log-py @ git+ssh://git@github.com/BasharSoft/access-log-py.git@v0.1.0
```

Use `git+https://` if your build environment doesn't have SSH credentials to the org. Always pin a tag — never `@main` — so a half-baked main commit can't silently ship to consumers.

## Usage

```python
# app/__init__.py
from flask import Flask
from access_log_py import install

def create_app():
    app = Flask(__name__)
    # ... your blueprints, extensions, config ...
    install(app, source="my-service-name")
    return app
```

That's it. Every request now emits one JSON line like:

```json
{"source":"my-service-name","time":"2026-04-27T10:11:12.345+00:00","timestamp":1777284672.345,"host":"my-service.svc","client_address":"40.0.17.23","x_forwarded_for":"40.0.17.23","x_real_ip":null,"x_forwarded_proto":"https","proxy_add_x_forwarded_for":"40.0.17.23, 10.42.0.7","protocol":"HTTP/1.1","method":"POST","uri":"/api/foo","status":200,"request_length":188432,"resp_body_size":3972,"resp_time":0.218,"http_referer":null,"user_agent":"GuzzleHttp/7","request_id":"be41c430871cba2a1a723c59b70a7acd"}
```

Every response also carries an `X-Request-ID` header for cross-service tracing — taken from the inbound request when present, otherwise a fresh `uuid4().hex`.

## Configuration

```python
install(
    app,
    source="my-service-name",          # required
    logger_name="access",              # python logging channel
    skip_rules=None,                   # see "Skipping traffic" below
    output_stream=None,                # defaults to sys.stdout
)
```

### `source`

The `source` field on every record. The `ACCESS_LOG_SOURCE` environment variable overrides the value passed in code, so the same image can be deployed across services and stamped per-pod via Helm:

```yaml
# Helm values
env:
  - name: ACCESS_LOG_SOURCE
    value: cv-parser-algorithm
```

### Skipping traffic

By default, K8s liveness/readiness probes (path `/`, User-Agent `kube-probe/*`) are dropped — they'd otherwise flood stdout every 5–10 s with no diagnostic value. To customize:

```python
from access_log_py import SkipRule, install

install(
    app,
    source="my-service",
    skip_rules=[
        SkipRule(path="/", user_agent_prefix="kube-probe/"),  # default kept
        SkipRule(path="/healthz"),                            # skip a custom probe path
        SkipRule(user_agent_prefix="ELB-HealthChecker/"),     # skip AWS ALB checks
    ],
)
```

Pass `skip_rules=[]` to log everything (including probes). A `SkipRule` with no fields set is a no-op — the package refuses to silently swallow all traffic.

### Disabling gunicorn's plain-text access log

Gunicorn's default access log will compete with this middleware on stdout, producing two records per request. Make sure your gunicorn invocation does **not** include `--access-logfile -`:

```bash
# Right
gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 8 --timeout 120 'app:create_app()'

# Wrong (duplicates output)
gunicorn ... --access-logfile - 'app:create_app()'
```

If your service runs in K8s with a Helm-rendered entrypoint, check the chart's `values-*.yaml` and any ConfigMap-mounted entrypoint script too — the Dockerfile `CMD` is overridden if the deployment sets `command:` / `args:`.

## Schema

| Field | Type | Notes |
|---|---|---|
| `source` | str | Service identifier (see configuration above) |
| `time` | str | ISO 8601, UTC, ms precision |
| `timestamp` | float | epoch seconds, ms precision |
| `host` | str | `Host` header |
| `client_address` | str | First hop of `X-Forwarded-For`, falling back to `REMOTE_ADDR` |
| `x_forwarded_for` | str \| null | raw header |
| `x_real_ip` | str \| null | raw header |
| `x_forwarded_proto` | str \| null | raw header |
| `proxy_add_x_forwarded_for` | str | derived: `f"{xff}, {remote_addr}"` if XFF set, else `remote_addr` |
| `protocol` | str | e.g. `HTTP/1.1` |
| `method` | str | |
| `uri` | str | path + query string |
| `status` | int | response status code |
| `request_length` | int | request body bytes (`Content-Length`); 0 if unknown |
| `resp_body_size` | int | response body bytes; 0 if streaming/unknown |
| `resp_time` | float | seconds spent in Flask, 3 d.p. |
| `http_referer` | str \| null | |
| `user_agent` | str \| null | |
| `request_id` | str | inbound `X-Request-ID` or `uuid4().hex` |

`connection` and `connection_requests` from the nginx schema are intentionally omitted — gunicorn doesn't expose per-request connection counters. Downstream pipelines should treat this as a strict subset of the nginx record.

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Versioning

Strict [SemVer](https://semver.org/):

- **Patch** (`0.1.0` → `0.1.1`): bug fixes, no schema changes.
- **Minor** (`0.1.0` → `0.2.0`): new optional fields, new config knobs, additive only.
- **Major** (`0.x.y` → `1.0.0`): breaking schema changes, removed config, renamed fields.

The JSON schema is treated like a public API. Breaking changes invalidate downstream queries and dashboards, so they require a major bump and a coordinated rollout across consumers.

## License

Internal — BasharSoft.
