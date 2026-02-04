# Metrics and Logging System Documentation

This document provides comprehensive documentation for the Nova metrics and logging system, including setup, configuration, and usage.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Metrics Reference](#metrics-reference)
6. [Logging Reference](#logging-reference)
7. [Prometheus Setup](#prometheus-setup)
8. [Grafana Setup](#grafana-setup)
9. [Monitoring Best Practices](#monitoring-best-practices)
10. [Troubleshooting](#troubleshooting)

## Overview

The Nova metrics and logging system provides:

- **Always-on Metrics**: Comprehensive Prometheus metrics for HTTP requests, LLM calls, costs, and business metrics
- **Configurable Logging**: Per-section logging with verbosity control
- **Request Tracking**: End-to-end request tracking with unique request IDs
- **Cost Tracking**: Real-time LLM cost calculation and tracking
- **Structured Logging**: JSON-formatted logs for easy parsing and shipping to log aggregation services

### Key Features

- ✅ Metrics always collected (cannot be disabled)
- ✅ Configurable logging per section
- ✅ Log verbosity control (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- ✅ Section-based organization (document_processing, chat, validation, etc.)
- ✅ Source location tracking (module:function)
- ✅ Request ID propagation through logs
- ✅ LLM response logging for debugging
- ✅ Cost tracking per provider/model/operation

## Architecture

```
┌─────────────────┐
│   FastAPI App   │
│                 │
│  ┌───────────┐  │
│  │Middleware │──┼──► HTTP Metrics
│  └───────────┘  │
│                 │
│  ┌───────────┐  │
│  │LLM Provider│─┼──► LLM Metrics + Logs
│  └───────────┘  │
│                 │
│  ┌───────────┐  │
│  │JSON Logger │─┼──► Structured Logs
│  └───────────┘  │
└────────┬────────┘
         │
         ├──► /metrics (Prometheus endpoint)
         │
         └──► JSON Logs (stdout)
              │
              ├──► Prometheus (scrapes /metrics)
              │    │
              │    └──► Grafana (visualizes metrics)
              │
              └──► Log Aggregation (CloudWatch, etc.)
```

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start Monitoring Stack

```bash
# Start Prometheus and Grafana
docker-compose -f docker-compose.monitoring.yml up -d
```

### 3. Access Dashboards

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)
- **Metrics Endpoint**: http://localhost:8000/metrics

### 4. Configure Logging (Optional)

Add to your `.env` file:

```bash
# Enable logging for specific sections
LOGGING_ENABLED=true
LOGGING_ENABLED_SECTIONS=all

# Set verbosity per section
LOGGING_LEVELS=document_processing:DEBUG,chat:INFO
```

## Configuration

### Environment Variables

#### Logging Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LOGGING_ENABLED` | `true` | Enable/disable structured logging globally |
| `LOGGING_ENABLED_SECTIONS` | `all` | Comma-separated list of sections to log |
| `LOGGING_LEVELS` | (empty) | Comma-separated `section:level` pairs |

#### Logging Levels

- `DEBUG`: Most verbose, includes all details (use for debugging)
- `INFO`: Standard information (default, recommended for production)
- `WARNING`: Only warnings and errors
- `ERROR`: Only errors
- `CRITICAL`: Only critical errors

### Configuration Examples

#### Example 1: Development - Debug Everything

```bash
LOGGING_ENABLED=true
LOGGING_ENABLED_SECTIONS=all
LOGGING_LEVELS=document_processing:DEBUG,chat:DEBUG,validation:DEBUG
```

#### Example 2: Production - Minimal Logging

```bash
LOGGING_ENABLED=true
LOGGING_ENABLED_SECTIONS=document_processing,chat
LOGGING_LEVELS=document_processing:INFO,chat:WARNING
```

#### Example 3: Debug Specific Section

```bash
LOGGING_ENABLED=true
LOGGING_ENABLED_SECTIONS=all
LOGGING_LEVELS=document_processing:DEBUG
# All other sections default to INFO
```

#### Example 4: Errors Only

```bash
LOGGING_ENABLED=true
LOGGING_ENABLED_SECTIONS=all
LOGGING_LEVELS=document_processing:ERROR,chat:ERROR,validation:ERROR
```

## Metrics Reference

### HTTP Metrics

#### `http_requests_total`
Total number of HTTP requests.

**Labels:**
- `method`: HTTP method (GET, POST, etc.)
- `endpoint`: Request path
- `status_code`: HTTP status code
- `section`: Section name
- `source`: Source location (METHOD:endpoint)

**Example Query:**
```promql
rate(http_requests_total[5m])
```

#### `http_request_duration_seconds`
HTTP request duration histogram.

**Labels:** `method`, `endpoint`, `section`, `source`

**Example Query:**
```promql
histogram_quantile(0.95, http_request_duration_seconds_bucket)
```

#### `request_size_bytes` / `response_size_bytes`
Request and response size histograms.

**Labels:** `method`, `endpoint`, `section`, `source`

### LLM Metrics

#### `llm_requests_total`
Total number of LLM API requests.

**Labels:**
- `provider`: AI provider (openai, anthropic)
- `model`: Model name (gpt-4o, claude-sonnet-4-20250514)
- `operation`: Operation name (extract_document_data, chat, etc.)
- `status`: Request status (success, error)
- `section`: Section name
- `source`: Source location (module:function)

**Example Query:**
```promql
rate(llm_requests_total[5m])
```

#### `llm_request_duration_seconds`
LLM request duration histogram.

**Labels:** `provider`, `model`, `operation`, `section`, `source`

**Example Query:**
```promql
histogram_quantile(0.95, llm_request_duration_seconds_bucket)
```

#### `llm_tokens_total`
Total LLM tokens used.

**Labels:** `provider`, `model`, `operation`, `token_type` (input/output), `section`, `source`

**Example Query:**
```promql
sum(rate(llm_tokens_total[5m])) by (token_type)
```

#### `llm_cost_total`
Total LLM cost in USD.

**Labels:** `provider`, `model`, `operation`, `section`, `source`

**Example Query:**
```promql
sum(increase(llm_cost_total[1h]))
```

#### `llm_errors_total`
Total LLM errors.

**Labels:** `provider`, `model`, `operation`, `error_type`, `section`, `source`

**Example Query:**
```promql
rate(llm_errors_total[5m])
```

### Business Metrics

#### `documents_processed_total`
Total documents processed.

**Labels:** `document_type`, `status`, `section`, `source`

**Example Query:**
```promql
rate(documents_processed_total[5m])
```

### System Metrics

#### `active_requests`
Currently active HTTP requests (gauge).

**Example Query:**
```promql
active_requests
```

## Logging Reference

### Log Format

All logs are emitted as JSON with the following structure:

```json
{
  "timestamp": "2025-01-24T10:30:45.123456",
  "level": "INFO",
  "logger": "app.ai.openai_provider",
  "message": "LLM request started",
  "module": "openai_provider",
  "function": "extract_document_data",
  "line": 67,
  "section": "document_processing",
  "source": "app.ai.openai_provider:extract_document_data",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "extra_fields": {
    "provider": "openai",
    "model": "gpt-4o",
    "operation": "extract_document_data",
    "input_tokens": 1500,
    "output_tokens": 500,
    "cost_usd": 0.00375
  }
}
```

### Log Fields

| Field | Description |
|-------|-------------|
| `timestamp` | UTC timestamp in ISO format |
| `level` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `logger` | Logger name |
| `message` | Log message |
| `module` | Python module name |
| `function` | Function name |
| `line` | Line number |
| `section` | Section name (auto-detected) |
| `source` | Source location (module:function) |
| `request_id` | Unique request ID (if available) |
| `extra_fields` | Additional context-specific fields |

### LLM Log Fields

When logging LLM operations, `extra_fields` may include:

- `provider`: AI provider name
- `model`: Model name
- `operation`: Operation name
- `input_tokens`: Number of input tokens
- `output_tokens`: Number of output tokens
- `cost_usd`: Cost in USD
- `duration_seconds`: Request duration
- `request`: Request data (if enabled)
- `response`: Response data (if enabled, may be truncated)

### Sections

Sections are automatically detected from:

- **Module paths**: For LLM calls (e.g., `app.services.documents` → `document_processing`)
- **Endpoint paths**: For HTTP requests (e.g., `/api/v1/documents` → `document_processing`)
- **Logger names**: For general logging (e.g., `app.ai` → `ai`)

Available sections:

- `document_processing`: Document extraction and processing
- `chat`: AI chat interactions
- `validation`: Document validation
- `email`: Email and chaser generation
- `api`: General API endpoints
- `client_management`: Client and engagement management
- `ai`: General AI operations

## Prometheus Setup

### Configuration

The Prometheus configuration is in `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'nova-backend'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Accessing Prometheus

1. Start the monitoring stack: `docker-compose -f docker-compose.monitoring.yml up -d`
2. Open http://localhost:9090
3. Use the query interface to explore metrics

### Useful Prometheus Queries

#### LLM Cost Per Hour
```promql
sum(increase(llm_cost_total[1h])) by (provider, section)
```

#### Request Rate by Section
```promql
sum(rate(http_requests_total[5m])) by (section)
```

#### Error Rate
```promql
sum(rate(http_requests_total{status_code=~"5.."}[5m])) + sum(rate(llm_errors_total[5m]))
```

#### P95 Latency
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

## Grafana Setup

### Initial Setup

1. Start Grafana: `docker-compose -f docker-compose.monitoring.yml up -d`
2. Access Grafana: http://localhost:3001
3. Login: `admin` / `admin` (change password on first login)

### Data Source

Prometheus data source is automatically configured via provisioning.

To manually configure:
1. Go to Configuration → Data Sources
2. Add Prometheus
3. URL: `http://prometheus:9090` (from Docker network) or `http://localhost:9090` (from host)

### Dashboard

The Nova metrics dashboard is automatically loaded from `grafana/dashboards/nova-metrics.json`.

**Dashboard Panels:**

1. **LLM Requests per Minute** - Request rate by provider/model/operation
2. **LLM Cost (USD)** - Total cost and cost by provider/section
3. **LLM Token Usage** - Input vs output tokens
4. **LLM Response Times (p95)** - 95th percentile latency
5. **HTTP Request Rate** - Request rate by method/endpoint
6. **HTTP Request Latency (p95)** - 95th percentile latency
7. **Active Requests** - Currently active requests
8. **Error Rates** - HTTP and LLM errors
9. **Documents Processed** - Processing rate by type/status
10. **LLM Requests by Section** - Breakdown by section
11. **LLM Cost by Section** - Cost breakdown by section

### Custom Dashboards

You can create custom dashboards using any of the available metrics. See the [Metrics Reference](#metrics-reference) section for available metrics and labels.

## Monitoring Best Practices

### 1. Cost Monitoring

Set up alerts for LLM costs:

```promql
# Alert if hourly cost exceeds $10
sum(increase(llm_cost_total[1h])) > 10
```

### 2. Error Monitoring

Monitor error rates:

```promql
# Alert if error rate exceeds 5%
sum(rate(llm_errors_total[5m])) / sum(rate(llm_requests_total[5m])) > 0.05
```

### 3. Latency Monitoring

Track response times:

```promql
# Alert if p95 latency exceeds 5 seconds
histogram_quantile(0.95, rate(llm_request_duration_seconds_bucket[5m])) > 5
```

### 4. Log Management

- Use `WARNING` or `ERROR` levels in production to reduce log volume
- Enable `DEBUG` only for specific sections when troubleshooting
- Consider shipping logs to a log aggregation service (CloudWatch, Datadog, etc.)

### 5. Section-Based Monitoring

Monitor specific sections:

```promql
# Document processing errors
sum(rate(llm_errors_total{section="document_processing"}[5m]))

# Chat costs
sum(increase(llm_cost_total{section="chat"}[1h]))
```

## Troubleshooting

### Metrics Not Appearing

1. **Check metrics endpoint**: Visit http://localhost:8000/metrics
2. **Check Prometheus targets**: In Prometheus UI, go to Status → Targets
3. **Check network**: Ensure Prometheus can reach the backend (use `host.docker.internal` for Docker)
4. **Check scrape interval**: Default is 15s, metrics may take time to appear

### Logs Not Appearing

1. **Check logging configuration**: Verify `LOGGING_ENABLED=true`
2. **Check section configuration**: Verify section is in `LOGGING_ENABLED_SECTIONS`
3. **Check log level**: Ensure log level meets configured verbosity
4. **Check stdout**: Logs go to stdout, check your process output

### High Log Volume

1. **Increase log levels**: Use `WARNING` or `ERROR` for noisy sections
2. **Disable sections**: Remove sections from `LOGGING_ENABLED_SECTIONS`
3. **Disable response logging**: Set `log_response=False` in LLM instrumentation calls

### Cost Tracking Issues

1. **Check pricing**: Verify pricing in `backend/app/core/llm_costs.py`
2. **Check token extraction**: Ensure token usage is being extracted from responses
3. **Check metrics**: Query `llm_tokens_total` to verify tokens are being tracked

### Grafana Dashboard Not Loading

1. **Check provisioning**: Verify `grafana/provisioning/` directory structure
2. **Check dashboard file**: Ensure `nova-metrics.json` is valid JSON
3. **Check permissions**: Ensure Grafana can read dashboard files
4. **Restart Grafana**: `docker-compose restart grafana`

## AWS Migration

When migrating to AWS, you can:

1. **CloudWatch Metrics**: Use OpenTelemetry CloudWatch exporter
2. **CloudWatch Logs**: Ship JSON logs via CloudWatch Logs agent
3. **CloudWatch Metrics for Prometheus**: Use managed Prometheus service

The instrumentation code remains the same - only the exporters change.

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Logging Configuration Guide](METRICS_CONFIG.md)

## Support

For issues or questions:
1. Check this documentation
2. Review configuration in `.env`
3. Check Prometheus/Grafana logs: `docker-compose logs prometheus grafana`
4. Verify metrics endpoint: `curl http://localhost:8000/metrics`
