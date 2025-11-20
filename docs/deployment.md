# Deployment Guide

## Quick Start with Docker Compose

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 5GB disk space

### Step 1: Clone and Setup

```bash
cd /Users/eldado/PycharmProjects/voyage81_features_api_service

# Services will use default settings from docker-compose.yml
```

### Step 2: Build and Run

```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### Step 3: Verify Services

```bash
# Check API health
curl http://localhost:8000/health

# Expected output:
{
  "status": "healthy",
  "service": "Feature Detection API",
  "version": "1.0.0",
  "feature_detector_ready": true,
  "cache_connected": true,
  "uptime_seconds": 12.34
}
```

### Step 4: Test Feature Detection

```bash
# Test with sample image
curl -X POST http://localhost:8000/api/v1/features/detect \
  -F "image=@data/images/lena_color_256.tif" \
  -H "X-Request-ID: test-001"

# Expected output:
{
  "success": true,
  "keypoints": 1247,
  "descriptors_shape": [1247, 128],
  "cached": false,
  "processing_time_ms": 342.5,
  "request_id": "test-001"
}
```

---

## Managing Services

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

### View Logs
```bash
# All services
docker-compose logs -f

# API only
docker-compose logs -f api

# Redis only
docker-compose logs -f redis
```

---

## Database Management

### Accessing Redis CLI

```bash
# Enter Redis container
docker exec -it feature-api-redis redis-cli

# Inside Redis CLI:
redis-cli> PING
PONG

# Check database size
redis-cli> DBSIZE

# List all keys
redis-cli> KEYS features:*

# Check memory usage
redis-cli> INFO memory

# Exit
redis-cli> EXIT
```

### Viewing Cached Data

```bash
# Get cache statistics
docker exec -it feature-api-redis redis-cli INFO stats

# View specific cached result
docker exec -it feature-api-redis redis-cli GET "features:abc123..."
```

---

## Monitoring

### API Metrics

```bash
# View structured logs
docker-compose logs api | tail -100

# Health check
curl http://localhost:8000/health | jq .

# API documentation
open http://localhost:8000/docs
```

### Redis Metrics

```bash
# Get comprehensive stats
docker exec -it feature-api-redis redis-cli INFO

# Memory usage
docker exec -it feature-api-redis redis-cli INFO memory | grep used_memory_human

# Cache hit rate
docker exec -it feature-api-redis redis-cli INFO stats | grep keyspace
```

---

## Testing

### Unit Tests
```bash
# Run all unit tests
docker-compose exec api pytest tests/unit -v

# Run with coverage
docker-compose exec api pytest tests/unit --cov=services --cov-report=html
```

### Integration Tests
```bash
# Run integration tests
docker-compose exec api pytest tests/integration -v
```

### Load Testing
```bash
# Run load test
locust -f tests/load/test_load.py --host=http://localhost:8000
# Open browser to http://localhost:8089
```

---

## Troubleshooting

### API Not Starting

```bash
# Check logs
docker-compose logs api

# Common issues:
# 1. Redis not ready - wait for Redis healthcheck
# 2. Port 8000 in use - change in docker-compose.yml
```

### Redis Connection Failed

```bash
# Check Redis status
docker-compose ps redis

# Test connection
docker exec -it feature-api-redis redis-cli PING

# Restart Redis
docker-compose restart redis
```

---

## Production Deployment

See optimization.md for scaling strategies and performance tuning.
