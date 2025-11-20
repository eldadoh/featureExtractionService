# Installation Guide

## 📦 Installation Options

### Option 1: Production Deployment (Docker Compose - Recommended)

For running the API service in production:

```bash
# Start services with Docker Compose
docker-compose up --build -d

# Services will automatically use production dependencies
# No local Python installation needed!
```

**What's included:**
- FastAPI application with 4 workers
- Redis cache
- Minimal production dependencies
- Optimized Docker image

---

### Option 2: Local Development

For local development, testing, and using the Streamlit dashboard:

```bash
# 1. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install development dependencies (includes production deps)
pip install -r requirements-dev.txt

# 3. Start services with Docker Compose
docker-compose up -d

# 4. Run tests
pytest tests/

# 5. Run Streamlit dashboard
streamlit run tools/streamlit_app.py

# 6. Run demo script
python tools/demo_api.py --runs 5
```

**What's included:**
- All production dependencies
- Testing frameworks (pytest, locust)
- Development tools (httpx for demo script)
- Streamlit dashboard
- Test data generators (faker)

---

## 📋 Requirements Files

### `requirements.txt` (Production)
```
fastapi==0.115.0
uvicorn[standard]==0.31.0
redis[hiredis]==5.1.1
opencv-python==4.12.0.88
numpy==2.2.6
Pillow==10.4.0
pydantic==2.9.2
pydantic-settings==2.5.2
aiofiles==24.1.0
python-dotenv==1.0.1
structlog==24.4.0
```

**Used by:** Docker containers, production deployments

**Size:** ~600MB Docker image

---

### `requirements-dev.txt` (Development)
```
-r requirements.txt  # Includes all production deps
httpx==0.27.2
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-cov==5.0.0
locust==2.32.2
faker==30.8.2
streamlit==1.39.0
```

**Used by:** Local development, testing, demo scripts

**Additional tools:**
- **httpx**: Async HTTP client for demo script and tests
- **pytest**: Testing framework
- **locust**: Load testing
- **streamlit**: Interactive dashboard
- **faker**: Test data generation

---

## 🚀 Quick Start by Use Case

### Use Case 1: Just Run the API
```bash
docker-compose up -d
# Done! API available at http://localhost:8000
```

### Use Case 2: Development + Testing
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Start infrastructure
docker-compose up -d

# Run tests
pytest tests/ -v --cov

# Run load tests
locust -f tests/load/test_load.py
```

### Use Case 3: Interactive Dashboard
```bash
# Install dev dependencies (includes streamlit)
pip install -r requirements-dev.txt

# Start API and Redis
docker-compose up -d

# Launch dashboard
streamlit run tools/streamlit_app.py
```

### Use Case 4: Demo Script
```bash
# Install dev dependencies (includes httpx)
pip install -r requirements-dev.txt

# Start API
docker-compose up -d

# Run demo
python tools/demo_api.py --runs 10
```

---

## 🔧 Verifying Installation

### Check Production Dependencies
```bash
# Inside Docker container
docker-compose exec api pip list
```

### Check Development Dependencies
```bash
# Local environment
pip list | grep -E "pytest|locust|streamlit|httpx"
```

---

## 📊 Dependency Size Comparison

| Environment | Dependencies | Approx Size | Use Case |
|-------------|--------------|-------------|----------|
| **Production** | 11 packages | ~600MB | Docker containers |
| **Development** | 18 packages | ~1.2GB | Local dev, testing |

---

## 🐛 Troubleshooting

### Issue: Missing dependencies in Docker
**Solution:** Docker uses `requirements.txt` (production only). This is correct and intentional.

### Issue: Cannot run tests locally
**Solution:** Install dev dependencies:
```bash
pip install -r requirements-dev.txt
```

### Issue: Streamlit not found
**Solution:** Streamlit is not in production requirements. Install dev dependencies:
```bash
pip install -r requirements-dev.txt
```

### Issue: httpx import error in demo_api.py
**Solution:** Install dev dependencies:
```bash
pip install -r requirements-dev.txt
```

### Issue: Pillow version conflict with Streamlit
**Solution:** We use Pillow==10.4.0 (compatible with both OpenCV and Streamlit)

---

## 📁 Project Structure After Setup

```
voyage81_features_api_service/
├── requirements.txt           # Production dependencies (Docker)
├── requirements-dev.txt       # Development dependencies (local)
├── services/
│   ├── feature_detector.py    # Core ML service
│   ├── cache_service.py
│   ├── image_service.py
│   └── feature_service.py
├── api/                       # FastAPI application
├── tests/                     # Test suite (needs dev deps)
├── tools/                     # Development utilities
│   ├── streamlit_app.py      # Dashboard (needs dev deps)
│   └── demo_api.py           # Demo script (needs dev deps)
├── docs/                      # Documentation
└── docker-compose.yml        # Production orchestration
```

---

## 🎯 Best Practices

1. **Production:** Always use Docker Compose (uses `requirements.txt`)
2. **Development:** Install `requirements-dev.txt` in virtual environment
3. **Testing:** Run tests locally with dev dependencies
4. **CI/CD:** Use `requirements.txt` for Docker builds
5. **Demo:** Run dashboard and demo script with dev dependencies installed locally

---

## 📚 Related Documentation

- [Deployment Guide](deployment.md) - Running in production
- [Architecture](architecture.html) - System design
- [Optimization](optimization.md) - Performance analysis
- [Logging Strategy](logging_strategy.md) - Production logging

---

**Note:** The `_task/` folder is no longer needed. `feature_detector.py` has been moved to `services/` for better organization.


