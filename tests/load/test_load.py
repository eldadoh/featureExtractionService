# """
# Load testing with Locust.
# Simulates concurrent users and measures performance.

# Run:
#     locust -f tests/load/test_load.py --host=http://localhost:8000
# """

# import random
# from io import BytesIO
# from locust import HttpUser, task, between, events
# import numpy as np
# from PIL import Image


# class FeatureDetectionUser(HttpUser):
#     """
#     Simulated user for load testing.
    
#     Behavior:
#         - Wait 1-3 seconds between requests
#         - Upload images for feature detection
#         - Mix of cached and uncached requests
#     """
    
#     wait_time = between(1, 3)
    
#     def on_start(self):
#         """Initialize user session."""
#         # Generate sample images for testing
#         self.images = self._generate_test_images(10)
    
#     @task(3)
#     def detect_features(self):
#         """
#         Test feature detection endpoint.
#         Weight: 3 (more frequent)
#         """
#         # Select random image
#         image_bytes = random.choice(self.images)
        
#         files = {
#             "image": ("test.jpg", image_bytes, "image/jpeg")
#         }
        
#         with self.client.post(
#             "/api/v1/features/detect",
#             files=files,
#             catch_response=True,
#             name="/api/v1/features/detect"
#         ) as response:
#             if response.status_code == 200:
#                 data = response.json()
#                 if data.get("success"):
#                     response.success()
#                 else:
#                     response.failure("Success flag was false")
#             else:
#                 response.failure(f"Status code: {response.status_code}")
    
#     @task(1)
#     def check_health(self):
#         """
#         Test health endpoint.
#         Weight: 1 (less frequent)
#         """
#         with self.client.get(
#             "/health",
#             catch_response=True,
#             name="/health"
#         ) as response:
#             if response.status_code == 200:
#                 response.success()
#             else:
#                 response.failure(f"Status code: {response.status_code}")
    
#     def _generate_test_images(self, count: int) -> list[BytesIO]:
#         """
#         Generate random test images.
        
#         Args:
#             count: Number of images to generate
        
#         Returns:
#             List of image BytesIO objects
#         """
#         images = []
#         for i in range(count):
#             # Generate random image
#             size = random.choice([256, 512, 1024])
#             arr = np.random.randint(0, 255, (size, size, 3), dtype=np.uint8)
#             img = Image.fromarray(arr)
            
#             # Convert to bytes
#             img_bytes = BytesIO()
#             img.save(img_bytes, format='JPEG')
#             img_bytes.seek(0)
#             images.append(img_bytes)
        
#         return images


# @events.test_start.add_listener
# def on_test_start(environment, **kwargs):
#     """Called when load test starts."""
#     print("\n" + "="*50)
#     print("🚀 Starting Load Test")
#     print("="*50)


# @events.test_stop.add_listener
# def on_test_stop(environment, **kwargs):
#     """Called when load test stops."""
#     print("\n" + "="*50)
#     print("✅ Load Test Complete")
#     print("="*50)

