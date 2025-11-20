#!/usr/bin/env python3
"""
API Demo Script - Test feature detection with local images.

Usage:
    python tools/demo_api.py
    python tools/demo_api.py --runs 2
    python tools/demo_api.py --image data/images/lena_color_256.tif
"""

import argparse
import time
from pathlib import Path
from typing import Dict, List

import httpx
import redis


class APIDemo:
    """Demo script for feature detection API."""
    
    def __init__(self, api_url: str = "http://localhost:8000", redis_host: str = "localhost"):
        self.api_url = api_url
        self.redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
        self.results: List[Dict] = []
    
    def get_redis_stats(self) -> Dict:
        """Get Redis statistics."""
        info = self.redis_client.info()
        return {
            "keys": self.redis_client.dbsize(),
            "memory_mb": round(info['used_memory'] / (1024 * 1024), 2),
            "hits": info.get('keyspace_hits', 0),
            "misses": info.get('keyspace_misses', 0),
            "hit_rate": round(info.get('keyspace_hits', 0) / max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0)) * 100, 1)
        }
    
    def process_image(self, image_path: Path, request_id: str) -> Dict:
        """Send image to API for processing."""
        start = time.perf_counter()
        
        with open(image_path, 'rb') as f:
            files = {'image': (image_path.name, f, 'image/tiff')}
            headers = {'X-Request-ID': request_id}
            
            response = httpx.post(
                f"{self.api_url}/api/v1/features/detect",
                files=files,
                headers=headers,
                timeout=30.0
            )
        
        elapsed = (time.perf_counter() - start) * 1000
        data = response.json()
        
        return {
            "image": image_path.name,
            "status": response.status_code,
            "keypoints": data.get("keypoints"),
            "cached": data.get("cached"),
            "api_time_ms": data.get("processing_time_ms"),
            "total_time_ms": round(elapsed, 2),
            "request_id": request_id
        }
    
    def run_demo(self, image_paths: List[Path], runs: int = 15):
        """Run demo with multiple images and runs."""
        print("=" * 80)
        print("🚀 Feature Detection API Demo")
        print("=" * 80)
        
        # Initial Redis stats
        print(f"\n📊 Initial Redis Stats:")
        stats = self.get_redis_stats()
        print(f"   Keys: {stats['keys']} | Memory: {stats['memory_mb']}MB | Hit Rate: {stats['hit_rate']}%")
        
        # Process images
        for run in range(1, runs + 1):
            print(f"\n{'─' * 80}")
            print(f"🔄 Run #{run} - {'Cache MISS expected' if run == 1 else 'Cache HIT expected'}")
            print(f"{'─' * 80}")
            
            for i, img_path in enumerate(image_paths, 1):
                request_id = f"demo-run{run}-img{i}"
                result = self.process_image(img_path, request_id)
                self.results.append(result)
                
                # Display result
                cache_icon = "💾" if result['cached'] else "🔄"
                status_icon = "✅" if result['status'] == 200 else "❌"
                
                print(f"{status_icon} {result['image']:25} | "
                      f"Keypoints: {result['keypoints']:4} | "
                      f"{cache_icon} {'CACHED' if result['cached'] else 'PROCESSED':9} | "
                      f"Time: {result['api_time_ms']:6.1f}ms")
        
        # Final stats
        print(f"\n{'=' * 80}")
        print("📈 Final Results")
        print(f"{'=' * 80}")
        
        stats = self.get_redis_stats()
        print(f"\n📊 Redis Stats:")
        print(f"   Cached Keys: {stats['keys']}")
        print(f"   Memory Used: {stats['memory_mb']}MB")
        print(f"   Cache Hits: {stats['hits']}")
        print(f"   Cache Misses: {stats['misses']}")
        print(f"   Hit Rate: {stats['hit_rate']}%")
        
        # Performance summary
        cache_hits = [r for r in self.results if r['cached']]
        cache_misses = [r for r in self.results if not r['cached']]
        
        if cache_hits and cache_misses:
            avg_hit = sum(r['api_time_ms'] for r in cache_hits) / len(cache_hits)
            avg_miss = sum(r['api_time_ms'] for r in cache_misses) / len(cache_misses)
            speedup = avg_miss / avg_hit
            
            print(f"\n⚡ Performance:")
            print(f"   Cache Miss Avg: {avg_miss:6.1f}ms")
            print(f"   Cache Hit Avg:  {avg_hit:6.1f}ms")
            print(f"   Speedup: {speedup:.1f}x faster with cache! 🚀")
        
        print(f"\n{'=' * 80}")
        print(f"✅ Demo Complete! Processed {len(self.results)} requests")
        print(f"{'=' * 80}\n")
    
    def check_health(self) -> bool:
        """Check API health."""
        try:
            response = httpx.get(f"{self.api_url}/health", timeout=5.0)
            return response.status_code == 200
        except:
            return False


def main():
    parser = argparse.ArgumentParser(description="Demo script for Feature Detection API")
    parser.add_argument('--image', type=str, help='Specific image to process')
    parser.add_argument('--runs', type=int, default=2, help='Number of runs (default: 2)')
    parser.add_argument('--api', type=str, default='http://localhost:8000', help='API URL')
    args = parser.parse_args()
    
    demo = APIDemo(api_url=args.api)
    
    # Check API health
    print("🔍 Checking API health...")
    if not demo.check_health():
        print("❌ API is not responding. Make sure it's running:")
        print("   docker-compose up -d")
        return
    print("✅ API is healthy!\n")
    
    # Find images
    if args.image:
        images = [Path(args.image)]
    else:
        data_dir = Path('data/images')
        images = list(data_dir.glob('*.tif')) + list(data_dir.glob('*.png')) + list(data_dir.glob('*.bmp')) + list(data_dir.glob('*.jpg'))
    
    if not images:
        print("❌ No images found in data/images/")
        return
    
    # Run demo
    demo.run_demo(images, runs=args.runs)


if __name__ == "__main__":
    main()


