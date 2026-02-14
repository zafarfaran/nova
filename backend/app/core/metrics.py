"""Prometheus metrics for the application."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST
from fastapi import Response

# HTTP Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code", "section", "source"]
)

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "section", "source"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
)

# LLM Metrics
llm_requests_total = Counter(
    "llm_requests_total",
    "Total LLM API requests",
    ["provider", "model", "operation", "status", "section", "source"]
)

llm_request_duration = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration in seconds",
    ["provider", "model", "operation", "section", "source"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
)

llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total LLM tokens used",
    ["provider", "model", "operation", "token_type", "section", "source"]  # token_type: input/output
)

llm_cost_total = Counter(
    "llm_cost_total",
    "Total LLM cost in USD",
    ["provider", "model", "operation", "section", "source"]
)

llm_errors_total = Counter(
    "llm_errors_total",
    "Total LLM errors",
    ["provider", "model", "operation", "error_type", "section", "source"]
)

# Request Tracking
active_requests = Gauge(
    "active_requests",
    "Currently active HTTP requests"
)

request_size_bytes = Histogram(
    "request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint", "section", "source"],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000, 500000)
)

response_size_bytes = Histogram(
    "response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint", "section", "source"],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000)
)

# Database Metrics
db_query_duration = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "section", "source"]
)

# Business Metrics
documents_processed_total = Counter(
    "documents_processed_total",
    "Total documents processed",
    ["document_type", "status", "section", "source"]
)


def get_metrics() -> Response:
    """Get Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
