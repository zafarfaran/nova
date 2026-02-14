# Metrics & Logging Quick Reference

Quick reference guide for the Nova metrics and logging system.

## Environment Variables

```bash
# Enable/disable logging globally
LOGGING_ENABLED=true

# Sections to log (comma-separated or "all")
LOGGING_ENABLED_SECTIONS=all

# Log levels per section (comma-separated key:value)
LOGGING_LEVELS=document_processing:DEBUG,chat:INFO
```

## Common Configurations

### Development
```bash
LOGGING_ENABLED=true
LOGGING_ENABLED_SECTIONS=all
LOGGING_LEVELS=document_processing:DEBUG,chat:DEBUG
```

### Production
```bash
LOGGING_ENABLED=true
LOGGING_ENABLED_SECTIONS=document_processing,chat
LOGGING_LEVELS=document_processing:INFO,chat:WARNING
```

### Debug Specific Section
```bash
LOGGING_ENABLED=true
LOGGING_ENABLED_SECTIONS=all
LOGGING_LEVELS=document_processing:DEBUG
```

## Key Metrics

| Metric | Description | Key Labels |
|--------|-------------|------------|
| `http_requests_total` | HTTP request count | method, endpoint, status_code, section |
| `http_request_duration_seconds` | HTTP latency | method, endpoint, section |
| `llm_requests_total` | LLM request count | provider, model, operation, section |
| `llm_cost_total` | LLM cost in USD | provider, model, operation, section |
| `llm_tokens_total` | Token usage | provider, model, token_type, section |
| `llm_errors_total` | LLM error count | provider, model, operation, section |
| `documents_processed_total` | Documents processed | document_type, status, section |

## Quick Prometheus Queries

```promql
# Total LLM cost (last hour)
sum(increase(llm_cost_total[1h]))

# Request rate by section
sum(rate(http_requests_total[5m])) by (section)

# Error rate
sum(rate(llm_errors_total[5m])) / sum(rate(llm_requests_total[5m]))

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

## Sections

- `document_processing` - Document extraction/processing
- `chat` - AI chat interactions
- `validation` - Document validation
- `email` - Email/chaser generation
- `api` - General API endpoints
- `client_management` - Client/engagement management
- `ai` - General AI operations

## Log Levels

- `DEBUG` - Most verbose (all details)
- `INFO` - Standard information (default)
- `WARNING` - Warnings and errors only
- `ERROR` - Errors only
- `CRITICAL` - Critical errors only

## Access Points

- **Metrics**: http://localhost:8000/metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

## Start Monitoring

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

## Log Format

```json
{
  "timestamp": "2025-01-24T10:30:45.123456",
  "level": "INFO",
  "section": "document_processing",
  "source": "app.ai.openai_provider:extract_document_data",
  "message": "LLM request started",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

For full documentation, see [METRICS_LOGGING_README.md](METRICS_LOGGING_README.md)
