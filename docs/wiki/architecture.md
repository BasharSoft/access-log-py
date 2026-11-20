# Architecture

## `install()`

```python
from access_log_py import SkipRule, install

install(app, source="my-service", skip_rules=[SkipRule(path="/", user_agent_prefix="kube-probe/")])
```

Signature (`src/access_log_py/flask_middleware.py:30-37`):

| Argument | Default | Meaning |
|---|---|---|
| `app` | — | The Flask app |
| `source` | — | Service name written to every record. The `ACCESS_LOG_SOURCE` environment variable overrides it (line 63). So each deployment of the same image can stamp its own value |
| `logger_name` | `"access"` | Python logger name |
| `skip_rules` | `default_skip_rules()` | Requests to not log. `[]` logs everything. Passing a list **replaces** the defaults |
| `output_stream` | `sys.stdout` | Where JSON lines go (tests pass a `StringIO`) |

What it registers on the app (lines 67-90):

1. `before_request` `_begin`: stores the start time, the request id (incoming `X-Request-ID` header or a new `uuid4().hex`) and `access_logged = False` in `flask.g`.
2. `after_request` `_attach_request_id`: sets `X-Request-ID` on the response.
3. `after_request` `_emit_access_log`: if no skip rule matches, logs one record. It swallows errors while logging.

Flask runs `after_request` hooks in reverse order. So the library writes the record before it sets the header. This has no effect on the record, which reads `g.request_id`.

The logger gets one `StreamHandler` with `JsonFormatter`, level `INFO`, and `propagate = False`, so records don't also go to the root logger. Calling `install()` twice with the same logger name doesn't add a second handler (a marker attribute on the handler, lines 16-27). But it does register the Flask hooks twice. The `access_logged` flag in `g` stops a second record.

## Skip rules (`src/access_log_py/filters.py`)

`SkipRule(path=None, user_agent_prefix=None)`, frozen dataclass. A rule matches when every field it sets matches: `request.path` equals `path` exactly, and the User-Agent starts with `user_agent_prefix`. A rule with both fields unset never matches, on purpose, so it can't hide all traffic. The default is one rule: path `/` with User-Agent `kube-probe/`.

## The record (`src/access_log_py/formatter.py:39-60`)

One JSON object per line, `ensure_ascii=False`, non-JSON values turned to strings.

| Field | Value | Notes |
|---|---|---|
| `source` | The `source` argument or `ACCESS_LOG_SOURCE` | |
| `time` | UTC (Coordinated Universal Time) ISO-8601 with milliseconds | Time of the log, not of the request start |
| `timestamp` | Unix seconds, 3 decimals | |
| `host` | `request.host` | |
| `client_address` | First `X-Forwarded-For` entry, else `remote_addr` | |
| `x_forwarded_for`, `x_real_ip`, `x_forwarded_proto` | Raw headers or `null` | |
| `proxy_add_x_forwarded_for` | `X-Forwarded-For` + `, ` + `remote_addr`, like nginx's variable | |
| `protocol` | `SERVER_PROTOCOL`, e.g. `HTTP/1.1` | |
| `method` | HTTP method | |
| `uri` | Path plus query string; a lone trailing `?` is removed | |
| `status` | Response status code | |
| `request_length` | Request `Content-Length` or 0 | Body only. nginx's `request_length` includes the request line and headers |
| `resp_body_size` | `response.calculate_content_length()` or 0 | 0 for streamed responses |
| `resp_time` | Seconds since `_begin`, 3 decimals | |
| `http_referer` | `Referer` or `null` | |
| `user_agent` | User-Agent or `null` | |
| `request_id` | From `g.request_id` | |

## How consumers use it

Both consumers call `install()` at the end of app setup, after their blueprints. Each passes its own skip list, which also drops Uptime Kuma checks and its health-check paths. See the [README](README.md#related-repos).

Both run under gunicorn in Kubernetes, so records go to container stdout. The cluster log agent then ships them. We inferred this from the stdout design; the log shipper isn't in this repo.

## Tests (`tests/test_flask_middleware.py`)

Ten tests use a `make_app` fixture that writes to a `StringIO`. They check that:

- each request gives one record with the expected fields;
- the library keeps the incoming request id;
- it generates a request id when one is missing;
- it skips `kube-probe` by default;
- `[]` logs everything;
- a custom rule replaces the default;
- `X-Forwarded-For` drives `client_address`;
- `ACCESS_LOG_SOURCE` overrides `source`;
- it keeps the query string in `uri`;
- it removes a bare trailing `?`.
