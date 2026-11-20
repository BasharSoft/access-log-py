# CLAUDE.md

access-log-py (package `access_log_py`, v0.1.0) is a small Flask middleware library that writes one JSON access-log line per request to stdout, with the same field names as BasharSoft's nginx JSON access log, and sets `X-Request-ID` on every response. Used by cv-parser-algorithm and wuzzuf-talent.
Python >= 3.8, Flask >= 2.0, hatchling build. Not on PyPI.
Live branch: `main`. Releases are git tags.

## Commands

```bash
# Set up dev env (Python 3.8+ supported; CI matrix is 3.8/3.11/3.12)
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest                     # full suite (CI runs pytest -v)
pytest tests/test_flask_middleware.py::test_emits_one_json_record_per_request -v   # single test
```

There is no separate lint/format step configured.

## Architecture

| Path | What lives there |
|---|---|
| `src/access_log_py/__init__.py` | Exports `install`, `SkipRule`, `default_skip_rules`; `__version__` |
| `src/access_log_py/flask_middleware.py` | `install(app, *, source, logger_name="access", skip_rules=None, output_stream=None)`; `_configure_logger()` |
| `src/access_log_py/formatter.py` | `build_payload(response, source)` (the record schema), `JsonFormatter` |
| `src/access_log_py/filters.py` | `SkipRule`, `default_skip_rules()` |
| `tests/test_flask_middleware.py` | `make_app` factory fixture, `_records()` helper, 10 tests |
| `.github/workflows/test.yml` | pytest on 3.8/3.11/3.12 for PRs and pushes to `main` |

Flow: `before_request` stamps `g.request_start`, `g.request_id`, `g.access_logged` -> view -> `after_request` writes `X-Request-ID` -> second `after_request` checks skip rules and emits `logger.info("", extra={"payload": build_payload(...)})`.

## Team rules

- `install(app, source=...)` is the only public entry point. It wires three Flask hooks: a `before_request` that stamps `g.request_start` / `g.request_id` / `g.access_logged`, an `after_request` that writes the `X-Request-ID` response header, and a second `after_request` that emits the log line. The `g.access_logged` flag prevents double-emission if `after_request` runs more than once.
- `JsonFormatter` pulls the dict out of `record.payload` (passed via `logger.info("", extra={"payload": ...})`); the empty message is intentional.
- `SkipRule` is a frozen dataclass with `path` and `user_agent_prefix`, AND-combined. A rule with both fields `None` is explicitly a no-op (refuses to silently drop all traffic). `default_skip_rules()` drops K8s probes only.
- Logger configuration is idempotent: `_configure_logger` tags its handler with `_HANDLER_MARKER` so repeated `install()` calls on the same `logger_name` don't stack handlers. `propagate = False` so records don't bubble to the root logger.
- The `ACCESS_LOG_SOURCE` env var overrides the `source` argument at install time. This is intentional: the same image is reused across services and the value is stamped per pod via Helm.
- The JSON schema in `build_payload` is a public API mirroring the nginx access log format. Adding optional fields is a minor bump; removing/renaming/retyping is a major bump. `connection` and `connection_requests` are intentionally omitted because gunicorn doesn't expose per-request connection counters; don't add fake values.
- Tests: use the `make_app` factory, which builds a fresh Flask app with a unique `logger_name` per call (`f"test.access.{uuid.uuid4().hex}"`), because `logging` caches loggers globally. It pipes records into an `io.StringIO` via `output_stream=`; parse them with `_records(buffer)`. Follow this pattern for new tests.
- Gunicorn's default access log duplicates output if `--access-logfile -` is passed. Don't "fix" this by re-enabling stdlib propagation.
- Consumers install from GitHub at a pinned tag (`git+https://github.com/BasharSoft/access-log-py.git@v0.1.0`), never `@main`. Bump the version in `pyproject.toml` and `__init__.py` together.

## Gotchas

- If a `before_request` hook registered before `install()` returns early, `_begin` doesn't run: the record gets `request_id: null` and `resp_time` ~0. Both consumers call `install()` last.
- `client_address` trusts the first `X-Forwarded-For` value; incoming `X-Request-ID` is used and echoed unchecked.
- `request_length` is body length only (nginx counts the whole request); `resp_body_size` is 0 for streamed responses.
- Any error while building/writing the record is swallowed silently (`flask_middleware.py`).
- The jobrex FastAPI services keep their own copies of this logic (`jobrexai/access_log.py` etc.). A schema change here should be mirrored there.

## Connections

- Used by [cv-parser-algorithm](https://github.com/BasharSoft/cv-parser-algorithm/blob/production/docs/wiki/README.md) (`app/__init__.py`) and [wuzzuf-talent](https://github.com/BasharSoft/wuzzuf-talent/blob/production/docs/wiki/README.md) (`talent/config/__init__.py`) via pip from a git tag.
- Schema mirrored in `access_log.py` of [jobrex-search](https://github.com/BasharSoft/jobrex-search/blob/main/docs/wiki/README.md), [jobrex-llm-asr](https://github.com/BasharSoft/jobrex-llm-asr/blob/main/docs/wiki/README.md), [jobrex-recruitment-utils](https://github.com/BasharSoft/jobrex-recruitment-utils/blob/main/docs/wiki/README.md).

## Deploy

Library: push a git tag (e.g. `v0.1.1`) after bumping both version strings; consumers update their `requirements.txt` pin. No release automation.

## More

- Wiki: [docs/wiki/README.md](docs/wiki/README.md), [architecture.md](docs/wiki/architecture.md), [known-issues.md](docs/wiki/known-issues.md)
- Code map: [docs/wiki/code-map/index.md](docs/wiki/code-map/index.md)
- Graph: `graphify explain "install()" --graph ../graphify/repos/access-log-py/graph.json`
