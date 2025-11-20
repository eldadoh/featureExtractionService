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
import re
from pathlib import Path
from typing import Dict, Any, List
import subprocess
import sys

# Configuration
API_URL = "http://localhost:8000"
REDIS_HOST = "localhost"
REDIS_PORT = 6379

st.set_page_config(page_title="Feature Detection Dashboard", layout="wide")

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
    """
    Get Redis statistics.
    """
    if not client:
        return {}
    try:
        info = client.info()
        
        return {
            "used_memory_human": info.get('used_memory_human', 'N/A'),
            "total_keys": client.dbsize(),
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
st.title("Feature Detection API Dashboard")
st.markdown("---")

# Tabs for different functionalities
tab1, tab2, tab3, tab4 = st.tabs(["Single Image", "Batch", "Redis Browser", "Docker Logs"])

# Tab 1: Single Image Detection
with tab1:
    st.header("Single Image Feature Detection")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Upload an image", type=['tif', 'png', 'jpg', 'bmp'])
        
        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
            
            if st.button("Detect Features", key="single"):
                # Save temporarily
                temp_path = f"/tmp/{uploaded_file.name}"
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.read())
                
                with st.spinner("Processing..."):
                    result = asyncio.run(detect_features(temp_path, API_URL))
                
                if "error" not in result:
                    st.success("Detection Complete!")
                    
                    # Display results
                    with col2:
                        st.metric("Keypoints Detected", result.get('keypoints', 0))
                        st.metric("Descriptors Shape", str(result.get('descriptors_shape', 'N/A')))
                        
                        cached = result.get('cached', False)
                        cache_status = "CACHE HIT" if cached else "CACHE MISS"
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
            num_runs = st.slider("Runs per image", 1, 20, 5)
            
            if st.button("Run Batch", key="batch"):
                with col2:
                    st.subheader("Output:")
                    
                    # Create placeholder for streaming output
                    output_placeholder = st.empty()
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    output_lines = []
                    
                    # Run subprocess with streaming output (unbuffered)
                    process = subprocess.Popen(
                        [sys.executable, '-u', 'tools/demo_api.py', '--runs', str(num_runs), '--n_images', str(num_images)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    # Stream output line by line
                    total_operations = num_images * num_runs
                    completed = 0
                    
                    for line in process.stdout:
                        output_lines.append(line)
                        
                        # Update progress based on actual processing lines (status icons indicate completion)
                        if "ms" in line and ("|" in line or "Time:" in line):
                            completed += 1
                            progress = min(completed / total_operations, 1.0)
                            progress_bar.progress(progress)
                            status_text.text(f"Processing: {completed}/{total_operations} images")
                        
                        # Update output display with last 100 lines for context
                        output_placeholder.code(''.join(output_lines[-100:]), language='text')
                    
                    process.wait()
                    
                    # Final update
                    progress_bar.progress(1.0)
                    output_placeholder.code(''.join(output_lines), language='text')
                    
                    if process.returncode != 0:
                        st.error(f"Process exited with code {process.returncode}")
        else:
            st.warning(f"Data directory not found: {data_dir}")

# Tab 3: Redis Browser
with tab3:
    st.header("Redis Database Browser")
    
    redis_client = get_redis_client()
    
    if redis_client:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Redis Stats")
            stats = get_redis_stats(redis_client)
            
            if "error" not in stats:
                st.metric("Total Keys", stats.get('total_keys', 0))
                st.metric("Memory Used", stats.get('used_memory_human', 'N/A'))
            else:
                st.error(f"Error: {stats['error']}")
            
            # Clear cache button
            st.markdown("---")
            confirm_clear = st.checkbox("I want to clear all cache", key="confirm_clear")
            if st.button("Clear All Cache", disabled=not confirm_clear, type="primary"):
                redis_client.flushdb()
                st.success("Cache cleared! Refreshing...")
                st.rerun()
        
        with col2:
            st.subheader("Cached Keys")
            
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
                            st.info(f"TTL: {ttl} seconds")
                        elif ttl == -1:
                            st.info("TTL: No expiration")
                        
                        if st.button(f"Delete {selected_key}"):
                            redis_client.delete(selected_key)
                            st.success("Key deleted!")
                            st.rerun()
            else:
                st.info("No keys found matching pattern")
    else:
        st.error("Cannot connect to Redis. Make sure Redis is running.")

# Tab 4: Docker Logs
with tab4:
    st.header("Docker Container Logs")
    
    # Docker Logs Section
    st.subheader("Container Logs")
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        service = st.selectbox(
            "Service",
            ["api", "redis", "both"],
            help="Select which service logs to view"
        )
    
    with col2:
        num_lines = st.selectbox(
            "Number of lines",
            [50, 100, 200, 500, 1000],
            index=0,
            help="How many recent log lines to show"
        )
    
    with col3:
        show_timestamps = st.checkbox("Show Docker timestamps", value=False, help="Add Docker container timestamps (application logs already include timestamps)")
    
    with col4:
        if st.button("Refresh", use_container_width=True):
            st.rerun()
    
    # Build docker compose logs command
    cmd = ['docker', 'compose', 'logs', f'--tail={num_lines}']
    
    if show_timestamps:
        cmd.append('--timestamps')
    
    # Add service(s)
    if service != "both":
        cmd.append(service)
    
    # Execute command
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        # Add log filtering options
        col1, col2 = st.columns([3, 1])
        
        with col1:
            filter_text = st.text_input(
                "Filter logs (regex supported)",
                placeholder="e.g., error, POST, status_code, etc.",
                help="Filter logs by text or regex pattern"
            )
        
        with col2:
            log_level_filter = st.selectbox(
                "Level",
                ["All", "ERROR", "WARNING", "INFO", "DEBUG"],
                help="Filter by log level"
            )
        
        # Process and filter logs (apply both filters correctly)
        logs = result.stdout
        log_lines = logs.split('\n')
        
        # Apply filters
        if filter_text or log_level_filter != "All":
            filtered_lines = []
            
            for line in log_lines:
                # Text filter
                if filter_text:
                    try:
                        if not re.search(filter_text, line, re.IGNORECASE):
                            continue
                    except re.error:
                        st.warning(f"Invalid regex pattern: {filter_text}")
                        break
                
                # Log level filter
                if log_level_filter != "All":
                    if log_level_filter.lower() not in line.lower():
                        continue
                
                # Line passed all filters
                filtered_lines.append(line)
            
            logs = '\n'.join(filtered_lines)
        
        # Display logs
        st.code(logs, language='text', line_numbers=False)
        
        # Log statistics
        total_lines = len(logs.split('\n')) if logs.strip() else 0
        st.caption(f"Showing {total_lines} log lines")
        
    else:
        st.error("Could not fetch logs. Make sure Docker Compose is running.")
        if result.stderr:
            st.code(result.stderr, language='text')

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Feature Detection</p>
</div>
""", unsafe_allow_html=True)


