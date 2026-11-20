# install()

> God node · 13 connections · `src/access_log_py/flask_middleware.py`

**Community:** [access_log_py: flask_middleware.py](access-log-py-flask-middleware-py.md)

## Connections by Relation

### calls
- [build_payload()](build-payload.md) `EXTRACTED`
- [default_skip_rules()](default-skip-rules.md) `EXTRACTED`
- [_configure_logger()](configure-logger.md) `EXTRACTED`
- [_make()](make.md) `INFERRED`

### contains
- flask_middleware.py `EXTRACTED`
- _emit_access_log() `EXTRACTED`
- _begin() `EXTRACTED`
- _attach_request_id() `EXTRACTED`

### imports
- __init__.py `EXTRACTED`

### rationale_for
- Install JSON access log middleware on the given Flask app. Each request emits… `EXTRACTED`

### references
- Flask `EXTRACTED`
- IO `EXTRACTED`

### uses
- [SkipRule](skiprule.md) `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*