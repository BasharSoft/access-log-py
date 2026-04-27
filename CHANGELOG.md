# Changelog

All notable changes to this package will be documented here. Versions follow [Semantic Versioning](https://semver.org/).

## [0.1.0]

Initial release.

- Flask middleware emitting one JSON access log line per request to stdout.
- Schema mirrors the BasharSoft nginx access log format so a single log pipeline mapping covers both.
- Inbound `X-Request-ID` is honored and echoed back as a response header; otherwise a `uuid4().hex` is generated.
- Default skip rule drops K8s liveness/readiness probes (path `/` + UA prefix `kube-probe/`).
- `ACCESS_LOG_SOURCE` env var overrides the `source` field at runtime so the same image can be reused across services.
