"""
Streamlit Dashboard for Feature Detection API
Minimal code, maximum functionality
"""
import streamlit as st
import httpx
import asyncio
import redis
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import subprocess
import sys

# Configuration
API_URL = "http://localhost:8000"
REDIS_HOST = "localhost"
REDIS_PORT = 6379

st.set_page_config(page_title="Feature Detection Dashboard", layout="wide", page_icon="🔍")

# Redis connection helper
@st.cache_resource
def get_redis_client():
    try:
        return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    except Exception as e:
        st.error(f"Redis connection failed: {e}")
        return None

async def detect_features(image_path: str, api_url: str) -> Dict[str, Any]:
    """Send image to API and get results"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        with open(image_path, 'rb') as f:
            start = time.time()
            response = await client.post(
                f"{api_url}/api/v1/features/detect",
                files={"image": (Path(image_path).name, f, "image/tiff")}
            )
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                result = response.json()
                result['request_latency_ms'] = latency
                return result
            else:
                return {"error": response.text, "status_code": response.status_code}

def get_redis_stats(client) -> Dict[str, Any]:
    """Get Redis statistics"""
    if not client:
        return {}
    try:
        info = client.info()
        return {
            "connected_clients": info.get('connected_clients', 0),
            "used_memory_human": info.get('used_memory_human', 'N/A'),
            "total_keys": client.dbsize(),
            "hit_rate": info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1), 1),
            "hits": info.get('keyspace_hits', 0),
            "misses": info.get('keyspace_misses', 0),
            "uptime_seconds": info.get('uptime_in_seconds', 0),
        }
    except Exception as e:
        return {"error": str(e)}

def get_redis_keys(client, pattern: str = "features:*", limit: int = 100) -> List[str]:
    """Get Redis keys matching pattern"""
    if not client:
        return []
    try:
        return list(client.scan_iter(match=pattern, count=limit))[:limit]
    except Exception as e:
        st.error(f"Error fetching keys: {e}")
        return []

def get_redis_value(client, key: str) -> Any:
    """Get value for a Redis key"""
    if not client:
        return None
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        return {"error": str(e)}

# Streamlit UI
st.title("🔍 Feature Detection API Dashboard")
st.markdown("---")

# Tabs for different functionalities
tab1, tab2, tab3, tab4 = st.tabs(["📸 Single Image", "🚀 Batch Demo", "💾 Redis Browser", "📊 Logs & Stats"])

# Tab 1: Single Image Detection
with tab1:
    st.header("Single Image Feature Detection")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Upload an image", type=['tif', 'png', 'jpg', 'bmp'])
        
        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
            
            if st.button("🔍 Detect Features", key="single"):
                # Save temporarily
                temp_path = f"/tmp/{uploaded_file.name}"
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.read())
                
                with st.spinner("Processing..."):
                    result = asyncio.run(detect_features(temp_path, API_URL))
                
                if "error" not in result:
                    st.success("✅ Detection Complete!")
                    
                    # Display results
                    with col2:
                        st.metric("Keypoints Detected", result.get('keypoints', 0))
                        st.metric("Descriptors Shape", str(result.get('descriptors_shape', 'N/A')))
                        
                        cached = result.get('cached', False)
                        cache_status = "🟢 CACHE HIT" if cached else "🔴 CACHE MISS"
                        st.metric("Cache Status", cache_status)
                        
                        st.metric("Processing Time (ms)", f"{result.get('processing_time_ms', 0):.2f}")
                        st.metric("Total Request Time (ms)", f"{result.get('request_latency_ms', 0):.2f}")
                        
                        st.json(result)
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")

# Tab 2: Batch Demo
with tab2:
    st.header("Batch Processing Demo")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        data_dir = Path('data/images')
        if data_dir.exists():
            images = list(data_dir.glob('*.tif')) + list(data_dir.glob('*.png')) + list(data_dir.glob('*.bmp'))
            
            num_images = st.slider("Number of images", 1, len(images), min(3, len(images)))
            num_runs = st.slider("Runs per image", 1, 20, 2)
            
            if st.button("🚀 Run Batch Demo", key="batch"):
                with st.spinner("Running batch processing..."):
                    result = subprocess.run(
                        [sys.executable, 'tools/demo_api.py', '--runs', str(num_runs)],
                        capture_output=True,
                        text=True
                    )
                    
                    with col2:
                        st.subheader("Output:")
                        st.code(result.stdout, language='text')
                        
                        if result.stderr:
                            st.error("Errors:")
                            st.code(result.stderr, language='text')
        else:
            st.warning(f"Data directory not found: {data_dir}")

# Tab 3: Redis Browser
with tab3:
    st.header("Redis Database Browser")
    
    redis_client = get_redis_client()
    
    if redis_client:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("📊 Redis Stats")
            stats = get_redis_stats(redis_client)
            
            if "error" not in stats:
                st.metric("Total Keys", stats.get('total_keys', 0))
                st.metric("Memory Used", stats.get('used_memory_human', 'N/A'))
                st.metric("Connected Clients", stats.get('connected_clients', 0))
                st.metric("Cache Hit Rate", f"{stats.get('hit_rate', 0):.2%}")
                st.metric("Hits", stats.get('hits', 0))
                st.metric("Misses", stats.get('misses', 0))
                st.metric("Uptime (seconds)", stats.get('uptime_seconds', 0))
            else:
                st.error(f"Error: {stats['error']}")
            
            # Clear cache button
            if st.button("🗑️ Clear All Cache"):
                if st.checkbox("Confirm deletion"):
                    redis_client.flushdb()
                    st.success("Cache cleared!")
                    st.rerun()
        
        with col2:
            st.subheader("🔑 Cached Keys")
            
            pattern = st.text_input("Key pattern", "features:*")
            keys = get_redis_keys(redis_client, pattern)
            
            if keys:
                st.write(f"Found {len(keys)} keys:")
                
                selected_key = st.selectbox("Select a key to inspect:", keys)
                
                if selected_key:
                    value = get_redis_value(redis_client, selected_key)
                    
                    if value:
                        st.json(value)
                        
                        ttl = redis_client.ttl(selected_key)
                        if ttl > 0:
                            st.info(f"⏰ TTL: {ttl} seconds")
                        elif ttl == -1:
                            st.info("⏰ TTL: No expiration")
                        
                        if st.button(f"🗑️ Delete {selected_key}"):
                            redis_client.delete(selected_key)
                            st.success("Key deleted!")
                            st.rerun()
            else:
                st.info("No keys found matching pattern")
    else:
        st.error("❌ Cannot connect to Redis. Make sure Redis is running.")

# Tab 4: Logs & Stats
with tab4:
    st.header("API Logs & Statistics")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🏥 Health Check")
        try:
            response = httpx.get(f"{API_URL}/health", timeout=5.0)
            if response.status_code == 200:
                health = response.json()
                st.success("✅ API is healthy")
                st.json(health)
            else:
                st.error(f"❌ API unhealthy: {response.status_code}")
        except Exception as e:
            st.error(f"❌ API not reachable: {e}")
    
    with col2:
        st.subheader("📝 Recent Docker Logs")
        
        if st.button("🔄 Refresh Logs"):
            result = subprocess.run(
                ['docker', 'compose', 'logs', '--tail=50', 'api'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                st.code(result.stdout, language='text')
            else:
                st.error("Could not fetch logs. Make sure Docker Compose is running.")
    
    st.markdown("---")
    
    # Redis stats in this tab too
    redis_client = get_redis_client()
    if redis_client:
        st.subheader("💾 Cache Performance")
        
        stats = get_redis_stats(redis_client)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Keys", stats.get('total_keys', 0))
        with col2:
            st.metric("Cache Hits", stats.get('hits', 0))
        with col3:
            st.metric("Cache Misses", stats.get('misses', 0))
        with col4:
            st.metric("Hit Rate", f"{stats.get('hit_rate', 0):.2%}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Feature Detection API Dashboard | Built with Streamlit</p>
    <p>🔍 Production-Ready MLOps Service</p>
</div>
""", unsafe_allow_html=True)


