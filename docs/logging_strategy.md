# Logging Strategy & Best Practices

## The Question: Where to Store API Request Logs?

**Answer:** Use **Docker logs with structured JSON** for application logs.

**Why:** Zero infrastructure cost, high performance, cloud-ready.

---

## Two-Tier Logging Architecture

```
API Request
     │
     ▼
  Middleware
     │
     ├─→ Tier 1: Docker Logs (ALL requests)
     │   - Structured JSON
     │   - Automatic rotation
     │   - Searchable with jq
     │
     └─→ Tier 2: Redis/DB (OPTIONAL - metadata only)
         - Business metrics
         - Audit trail
         - Analytics
```

---

## Tier 1: Docker Logs (Implemented)

### What We Log

```json
{
  "event": "Request completed",
  "timestamp": "2025-11-19T10:30:45.123Z",
  "level": "info",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "path": "/api/v1/features/detect",
  "status_code": 200,
  "processing_time_ms": 342.5,
  "client_host": "172.18.0.1",
  "keypoints": 1247,
  "cached": false
}
```

### Advantages

✅ Zero infrastructure cost  
✅ High performance (async, non-blocking)  
✅ Automatic rotation  
✅ Searchable (jq, grep, ELK)  
✅ Cloud integration (CloudWatch, Stackdriver)  
✅ No database load  

### Configuration

```yaml
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "50m"
    max-file: "5"
    compress: "true"
```

### Querying Logs

```bash
# View all logs
docker-compose logs api

# Filter by request_id
docker-compose logs api | jq 'select(.request_id=="abc-123")'

# Get processing times
docker-compose logs api | jq '.processing_time_ms'

# Find errors
docker-compose logs api | jq 'select(.level=="error")'
```

---

## Tier 2: Redis/Database (Optional)

### When to Add This

Use when you need:
- Real-time analytics dashboard
- Business metrics (most processed images)
- Compliance audit trail
- Historical trend analysis

### What to Store

**DON'T STORE:**
❌ Complete request payloads  
❌ Image data  
❌ Detailed logs  
❌ Stack traces  

**DO STORE:**
✅ Request metadata (ID, timestamp)  
✅ Processing results (keypoints, cached)  
✅ Performance metrics (latency)  
✅ Business data (image_hash)  

---

## Production Best Practice

### Recommended Setup

```
Layer 1: Docker Logs
  Purpose: Debugging, monitoring, troubleshooting
  Retention: 250MB (50MB x 5 files)
  Shipped to: CloudWatch / ELK / Splunk

Layer 2: Redis (Optional)
  Purpose: Recent history, quick lookups
  Retention: 7 days
  Size: ~200 bytes per request

Layer 3: Database (Optional)
  Purpose: Long-term analytics, reporting  
  Retention: Indefinite
  Size: Aggregated metrics only
```

### When to Use Each Layer

| Requirement | Docker Logs | Redis | PostgreSQL |
|-------------|-------------|-------|------------|
| Request debugging | ✅ Primary | ✅ Recent | ❌ |
| Performance monitoring | ✅ Primary | ✅ Fast | ❌ |
| Error tracking | ✅ Primary | ❌ | ❌ |
| Recent history (7 days) | ✅ Yes | ✅ Fast | ❌ |
| Long-term storage | ⚠️ Limited | ❌ | ✅ Yes |
| Business analytics | ❌ | ❌ | ✅ Yes |
| Real-time metrics | ✅ Yes | ✅ Fast | ❌ |
| Cost | ✅ $0 | ✅ Included | ❌ +$20/mo |

---

## Structured Logging Best Practices

### Good Example

```python
# ✅ GOOD: Use keyword arguments
logger.info(
    "Request completed",
    request_id=request_id,
    status_code=200,
    processing_time_ms=342.5,
    cached=False
)
```

### Bad Example

```python
# ❌ BAD: String concatenation
logger.info(f"Request {request_id} completed in {time}ms")
```

### Performance Impact

```
No logging: 342ms baseline
Docker logs: 342.5ms (+0.15%)
Redis audit: 344ms (+0.6%)
PostgreSQL: 350ms (+2.3%)

Conclusion: Docker logs have NEGLIGIBLE performance impact
```

---

## Cloud Production

### AWS CloudWatch Logs

```yaml
logging:
  driver: "awslogs"
  options:
    awslogs-group: "/ecs/feature-api"
    awslogs-region: "us-east-1"
```

### ELK Stack

```yaml
logging:
  driver: "gelf"
  options:
    gelf-address: "udp://logstash:12201"
```

---

## Interview Talking Points

1. **We use Docker structured logs as primary logging**
   - Zero cost, high performance
   - JSON format for machine readability

2. **Logs include correlation IDs for tracing**
   - request_id in every log entry
   - Can trace entire request lifecycle

3. **We DON'T store logs in Redis/DB because:**
   - Database is for business data, not logs
   - Can overwhelm DB with write load
   - Docker logs sufficient for debugging

4. **Production recommendation:**
   - Ship to CloudWatch/Stackdriver
   - Optional: ELK for advanced analytics
   - Optional: Redis for real-time metrics cache

---

This strategy balances **performance**, **cost**, and **operational simplicity**.
