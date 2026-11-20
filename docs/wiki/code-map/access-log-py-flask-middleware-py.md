# access_log_py: flask_middleware.py

> 11 nodes · cohesion 0.20

## Key Concepts

- **install()** (13 connections) — `src/access_log_py/flask_middleware.py`
- **_configure_logger()** (5 connections) — `src/access_log_py/flask_middleware.py`
- **_make()** (4 connections) — `tests/test_flask_middleware.py`
- **IO** (3 connections)
- **_emit_access_log()** (2 connections) — `src/access_log_py/flask_middleware.py`
- **Logger** (1 connections)
- **_attach_request_id()** (1 connections) — `src/access_log_py/flask_middleware.py`
- **_begin()** (1 connections) — `src/access_log_py/flask_middleware.py`
- **Install JSON access log middleware on the given Flask app. Each request emits…** (1 connections) — `src/access_log_py/flask_middleware.py`
- **echo()** (1 connections) — `tests/test_flask_middleware.py`
- **index()** (1 connections) — `tests/test_flask_middleware.py`

## Relationships

- [access_log_py: filters.py + flask_middleware.py](access-log-py-filters-py-and-flask-middleware-py.md) (6 shared connections)
- [tests/test_flask_middleware.py](tests-test-flask-middleware-py.md) (2 shared connections)
- [access_log_py/formatter.py (1)](access-log-py-formatter-py-1.md) (2 shared connections)
- [access_log_py/formatter.py (2)](access-log-py-formatter-py-2.md) (1 shared connections)

## Source Files

- `src/access_log_py/flask_middleware.py`
- `tests/test_flask_middleware.py`

## Audit Trail

- EXTRACTED: 19 (86%)
- INFERRED: 3 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*