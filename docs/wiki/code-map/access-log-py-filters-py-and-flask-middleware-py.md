# access_log_py: filters.py + flask_middleware.py

> 14 nodes · cohesion 0.23

## Key Concepts

- **flask_middleware.py** (16 connections) — `src/access_log_py/flask_middleware.py`
- **SkipRule** (8 connections) — `src/access_log_py/filters.py`
- **filters.py** (7 connections) — `src/access_log_py/filters.py`
- **default_skip_rules()** (6 connections) — `src/access_log_py/filters.py`
- **__init__.py** (6 connections) — `src/access_log_py/__init__.py`
- **Flask** (5 connections)
- **typing** (3 connections)
- **uuid** (2 connections)
- **dataclasses** (1 connections)
- **os** (1 connections)
- **Default rules — drop K8s liveness/readiness probes hitting `/` with a `kube-…** (1 connections) — `src/access_log_py/filters.py`
- **A rule that, when matched against the current request, suppresses the access…** (1 connections) — `src/access_log_py/filters.py`
- **.matches()** (1 connections) — `src/access_log_py/filters.py`
- **sys** (1 connections)

## Relationships

- [access_log_py/formatter.py (1)](access-log-py-formatter-py-1.md) (6 shared connections)
- [access_log_py: flask_middleware.py](access-log-py-flask-middleware-py.md) (6 shared connections)
- [tests/test_flask_middleware.py](tests-test-flask-middleware-py.md) (4 shared connections)
- [access_log_py/formatter.py (2)](access-log-py-formatter-py-2.md) (1 shared connections)

## Source Files

- `src/access_log_py/__init__.py`
- `src/access_log_py/filters.py`
- `src/access_log_py/flask_middleware.py`

## Audit Trail

- EXTRACTED: 36 (95%)
- INFERRED: 2 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*