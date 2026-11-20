# Known Issues

These were found while writing this wiki from the code, as of `main` at `1cffc82`. Items marked ✓ were checked by opening the exact lines.

**Secrets:** none in the repo.

## Correctness

| # | Issue | Where | Impact |
|---|---|---|---|
| 1 | ✓ **Requests stopped by an earlier `before_request` hook are logged without timing or id.** Flask skips later `before_request` hooks when one returns a response, so `_begin` doesn't run. `resp_time` then falls back to "now minus now" (≈0) and `request_id` is `null`; the `X-Request-ID` header is empty | `src/access_log_py/flask_middleware.py:67-71`, `src/access_log_py/formatter.py:57` | Both consumers call `install()` last, so any earlier auth or validation hook that returns early produces such records (inferred for their actual hooks) |
| 2 | ✓ **`client_address` trusts the first `X-Forwarded-For` value**, which the client controls unless the edge proxy overwrites it | `src/access_log_py/formatter.py:18-24` | Logged client IPs can be faked. nginx's own log uses the connection address after its `real_ip` rules |
| 3 | ✓ **Incoming `X-Request-ID` is used as-is** with no length or format check, and echoed back | `src/access_log_py/flask_middleware.py:70`, `:75` | A client can choose ids that collide with others or are very long. JSON encoding prevents log-line injection |
| 4 | ✓ `request_length` is the body length only, while nginx's field of the same name counts the whole request | `src/access_log_py/formatter.py:55` | Same field name, different meaning across sources |
| 5 | ✓ `resp_body_size` is 0 for streamed responses | `src/access_log_py/formatter.py:56` | |
| 6 | ✓ Any error while building or writing the record is swallowed with no trace | `src/access_log_py/flask_middleware.py:84-89` | A broken field would silently stop all access logs |

## Maintenance

| # | Issue | Notes |
|---|---|---|
| 1 | Flask only. The three jobrex FastAPI services keep their own copies of the same code (`jobrex-search/jobrexai/access_log.py` and siblings), so the schema can drift between copies | One package with a Flask and an ASGI adapter would keep one schema |
| 2 | Supports Python 3.8, which is end-of-life; CI still tests it | `pyproject.toml`, `.github/workflows/test.yml` |
| 3 | No release automation. `__version__` in `__init__.py` and `version` in `pyproject.toml` are both hand-edited, and consumers depend on a git tag | |
