# Feature Detection API Service

### Run with Docker Compose

```bash

docker-compose up -d

# Detect features in an image
curl -X POST http://localhost:8000/api/v1/features/detect \
  -F "image=@data/images/lena_color_256.tif"

# View API documentation
open http://localhost:8000/docs
```

### Run Streamlit / CLI Demo

```bash
# Activate virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements-dev.txt

# Run Streamlit demo (single / batch runs , redis overview, docker logs)
streamlit run tools/streamlit_app.py
```

### Shutdown

```bash
docker-compose down -v
```

### System Overview

```
┌─────────────────┐
│   Client        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  FastAPI        │◄─────┤  Redis       │
│  (N Workers)    │      │  Cache       │
└────────┬────────┘      └──────────────┘
         │
         ▼
┌─────────────────┐
│ Feature         │
│ Detector        │
└─────────────────┘
```

### Data Flow

1. Client uploads image → API validates format/size
2. API generates SHA256 hash → checks Redis cache
3. **Cache Hit**: Returns cached results
4. **Cache Miss**: 
   - Detects features
   - Caches result in Redis
   - Returns response




### Project Structure

```
features_api_service/
├── api/                          # API Layer
│   ├── main.py                   # FastAPI application
│   ├── dependencies.py           # Dependency injection
│   ├── middleware.py             # Request logging & error handling
│   └── routes/
│       ├── features.py           # Feature detection endpoint
│       └── health.py             # Health check endpoints
├── core/                         
│   ├── config.py                 # Settings management
│   ├── exceptions.py             # Custom exceptions
│   └── logging_config.py         # Structured logging setup
├── services/                     
│   ├── cache_service.py          # Redis cache operations
│   ├── feature_detector.py       # feature detection
│   ├── feature_service.py        # Feature detection orchestration
│   └── image_service.py          # Image validation & processing
├── models/                       # Data Models
│   └── responses.py              # Pydantic response models
├── tests/                        
│   ├── test_api.py               # API integration tests
│   └── test_feature_detector.py  # Unit tests
├── tools/                        
│   ├── demo_api.py               # demo script
│   └── streamlit_app.py          # Interactive demo
├── data/                         
│   └── images/                   # Sample images
├── docker-compose.yml            
├── Dockerfile                    
├── requirements.txt              # Production dependencies
└── requirements-dev.txt          # Development dependencies
```

### Testing

```
pytest tests/ -v
```

### Configuration

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