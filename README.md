# Feature Detection API Service

A production-ready, scalable FastAPI service for detecting SIFT features in images with Redis caching.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)

### Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# Check service health
curl http://localhost:8000/health

# Detect features in an image
curl -X POST http://localhost:8000/api/v1/features/detect \
  -F "image=@path/to/your/image.jpg"

# View API documentation
open http://localhost:8000/docs
```

### Run Demo

```bash
# Activate virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements-dev.txt

# Run API demo
python tools/demo_api.py --n_images 3 --runs 2

# Run Streamlit dashboard
streamlit run tools/streamlit_app.py
```

### Stop Services

```bash
docker-compose down
```

## Architecture

### System Overview

```
┌─────────────────┐
│   Client        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  FastAPI        │◄─────┤  Redis       │
│  (4 Workers)    │      │  Cache       │
└────────┬────────┘      └──────────────┘
         │
         ▼
┌─────────────────┐
│ SIFT Feature    │
│ Detector        │
└─────────────────┘
```

### Key Components

- **FastAPI Service**: Async API with 4 Uvicorn workers for concurrent request handling
- **Redis Cache**: In-memory caching with LRU eviction, 1-hour TTL
- **Feature Detector**: OpenCV SIFT with Non-Local Means Denoising
- **Thread Pool**: Offloads CPU-bound feature detection from async event loop

### Data Flow

1. Client uploads image → API validates format/size
2. API generates SHA256 hash → checks Redis cache
3. **Cache Hit**: Returns cached results (< 10ms)
4. **Cache Miss**: 
   - Detects features using SIFT (500-2000ms)
   - Caches result in Redis
   - Returns response

## Technology Stack

### Core Technologies
- **FastAPI** - Async web framework
- **Uvicorn** - ASGI server with multiple workers
- **Redis** - In-memory cache
- **OpenCV** - SIFT feature detection
- **Pydantic** - Data validation

### Development Tools
- **pytest** - Testing framework
- **Streamlit** - Interactive dashboard
- **Docker & Docker Compose** - Containerization
- **structlog** - Structured logging

### Python Libraries
```
fastapi==0.115.6
uvicorn[standard]==0.34.0
redis==5.2.1
opencv-python==4.10.0.84
pydantic==2.10.3
pydantic-settings==2.6.1
structlog==24.4.0
```

## Project Structure

```
voyage81_features_api_service/
├── api/                          # API Layer
│   ├── main.py                   # FastAPI application
│   ├── dependencies.py           # Dependency injection
│   ├── middleware.py             # Request logging & error handling
│   └── routes/
│       ├── features.py           # Feature detection endpoint
│       └── health.py             # Health check endpoints
├── core/                         # Core Configuration
│   ├── config.py                 # Settings management
│   ├── exceptions.py             # Custom exceptions
│   └── logging_config.py         # Structured logging setup
├── services/                     # Business Logic
│   ├── cache_service.py          # Redis cache operations
│   ├── feature_detector.py       # SIFT feature detection
│   ├── feature_service.py        # Feature detection orchestration
│   └── image_service.py          # Image validation & processing
├── models/                       # Data Models
│   └── responses.py              # Pydantic response models
├── tests/                        # Test Suite
│   ├── test_api.py               # API integration tests
│   └── test_feature_detector.py  # Unit tests
├── tools/                        # Development Tools
│   ├── demo_api.py               # CLI demo script
│   └── streamlit_app.py          # Interactive dashboard
├── data/                         # Data Storage
│   └── images/                   # Sample images
├── docker-compose.yml            # Docker orchestration
├── Dockerfile                    # API service container
├── requirements.txt              # Production dependencies
└── requirements-dev.txt          # Development dependencies
```

## Testing

### Run All Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Test Structure

**Unit Tests** (`test_feature_detector.py`)
- Detector initialization
- Thread pool executor validation
- Feature detection on sample images

**Integration Tests** (`test_api.py`)
- Health endpoint validation
- Feature detection with real images
- End-to-end API workflow

### Expected Output

```
tests/test_api.py::TestAPI::test_health_endpoint PASSED           [ 20%]
tests/test_api.py::TestAPI::test_detect_endpoint PASSED           [ 40%]
tests/test_feature_detector.py::...::test_detector_initialization PASSED [ 60%]
tests/test_feature_detector.py::...::test_detector_has_executor PASSED   [ 80%]
tests/test_feature_detector.py::...::test_detect_on_image_file PASSED    [100%]

============================== 5 passed in 48.22s ==============================
```

## Configuration

### Environment Variables

Configure the service by setting environment variables or creating a `.env` file:

```bash
# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_MAX_CONNECTIONS=50

# Cache Configuration
CACHE_TTL=3600
CACHE_ENABLED=true

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Image Processing
MAX_IMAGE_SIZE_MB=10
UPLOAD_DIR=/app/data/uploads

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Application
APP_NAME=Feature Detection API
APP_VERSION=1.0.0
ENVIRONMENT=production
```

### Configuration Details

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `redis` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `CACHE_TTL` | `3600` | Cache time-to-live (seconds) |
| `API_WORKERS` | `4` | Number of Uvicorn workers |
| `MAX_IMAGE_SIZE_MB` | `10` | Maximum image size |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |

### Docker Compose Configuration

The `docker-compose.yml` defines two services:

- **api**: FastAPI service with 4 workers
- **redis**: Redis cache with persistence

Volumes:
- `./data:/app/data` - Image storage
- `redis_data:/data` - Redis persistence

---

**API Documentation**: http://localhost:8000/docs  
**Health Check**: http://localhost:8000/health

