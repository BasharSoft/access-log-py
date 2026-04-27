# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Set up dev env (Python 3.8+ supported; CI matrix is 3.8/3.11/3.12)
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run the full suite
pytest

# Run a single test
pytest tests/test_flask_middleware.py::test_emits_one_json_record_per_request -v
```

There is no separate lint/format step configured.

## Architecture

This package is a small Flask middleware (`src/access_log_py/`, ~3 modules) that emits one JSON access log line per request. The shape is deliberate:

- **`flask_middleware.install(app, source=...)`** is the only public entry point. It wires three Flask hooks: a `before_request` that stamps `g.request_start` / `g.request_id` / `g.access_logged`, an `after_request` that writes the `X-Request-ID` response header, and a second `after_request` that emits the log line. The `g.access_logged` flag prevents double-emission if `after_request` runs more than once (e.g. error handling paths).
- **`formatter.build_payload(response, source)`** constructs the JSON dict from `flask.request` + `flask.g` + the response. **`JsonFormatter`** is a `logging.Formatter` that pulls the dict out of `record.payload` (passed via `logger.info("", extra={"payload": ...})`) — the empty message is intentional.
- **`filters.SkipRule`** is a frozen dataclass with `path` and `user_agent_prefix` fields, AND-combined. A rule with both fields `None` is explicitly a no-op (refuses to silently drop all traffic). `default_skip_rules()` drops K8s probes only.
- **Logger configuration is idempotent**: `_configure_logger` tags its handler with `_HANDLER_MARKER` so repeated `install()` calls on the same `logger_name` don't stack handlers. `propagate = False` so records don't bubble to the root logger.
- **`ACCESS_LOG_SOURCE` env var overrides the `source` argument** at install time. This is intentional — the same container image is reused across services and the value is stamped per-pod via Helm.

### The schema is a public API

The JSON schema in `build_payload` mirrors the BasharSoft nginx access log format so a single downstream log-pipeline mapping handles both. **Treat field names, types, and presence as a public contract**: adding optional fields is a minor bump; removing/renaming/retyping is a major bump (per `README.md` "Versioning"). `connection` and `connection_requests` from the nginx schema are intentionally omitted because gunicorn doesn't expose per-request connection counters — don't add fake values.

### Test conventions

`tests/test_flask_middleware.py` uses a `make_app` factory fixture that builds a fresh Flask app with a **unique `logger_name` per call** (`f"test.access.{uuid.uuid4().hex}"`). This is required because Python's `logging` module caches loggers globally — without unique names, handlers from one test leak into the next and assertions on captured output break. Follow this pattern when adding tests.

The factory pipes records into an `io.StringIO` via `output_stream=`, then `_records(buffer)` parses JSON lines for assertions.

## Deployment notes worth knowing when editing

- Gunicorn's default access log will duplicate output if `--access-logfile -` is passed. The README warns consumers; don't undo this by re-enabling stdlib propagation.
- The package is not on PyPI — consumers install via `git+ssh://...@<tag>` and must pin a tag, never `@main`. Releases are git tags; the version in `pyproject.toml` and `__init__.py` must be bumped together.
