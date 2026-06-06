"""Observability wiring shared by every service.

- **Metrics**: Prometheus `/metrics` via prometheus-fastapi-instrumentator
  (scraped by Prometheus, visualized in Grafana).
- **Traces**: OpenTelemetry spans exported over OTLP/HTTP to Jaeger (optional,
  enabled when ``OTEL_TRACES_ENABLED`` and an endpoint are configured).
- **Logs**: structured JSON via :mod:`anime_shared.logging` (Loki + ELK).
"""

from __future__ import annotations

from fastapi import FastAPI

from anime_shared.config import Settings, get_settings


def _setup_tracing(app: FastAPI, service_name: str, settings: Settings) -> None:
    if not (settings.otel_traces_enabled and settings.otel_exporter_otlp_endpoint):
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
        endpoint = settings.otel_exporter_otlp_endpoint.rstrip("/") + "/v1/traces"
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app)
        HTTPXClientInstrumentor().instrument()
    except Exception:  # noqa: BLE001 - tracing must never block startup
        pass


def instrument_metrics(app: FastAPI) -> None:
    """Expose Prometheus metrics at ``/metrics``."""
    from prometheus_fastapi_instrumentator import Instrumentator

    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


def setup_observability(app: FastAPI, service_name: str, settings: Settings | None = None) -> None:
    """Attach metrics + tracing to a FastAPI app."""
    settings = settings or get_settings()
    instrument_metrics(app)
    _setup_tracing(app, service_name, settings)
