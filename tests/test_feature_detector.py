from pathlib import Path
from services.feature_detector import FeatureDetector


class TestFeatureDetector:
    """Unit tests for FeatureDetector."""
    
    def test_detector_initialization(self):
        """Test detector can be initialized."""
        detector = FeatureDetector()
        assert detector is not None
        assert detector.ready is False
    
    def test_detector_has_executor(self):
        """Test detector has thread pool executor."""
        detector = FeatureDetector()
        assert detector.executor is not None
    
    def test_detect_on_image_file(self):
        """Test detection on real image file."""
        
        detector = FeatureDetector()
        image_path = Path("data/images/lena_color_256.tif")
        
        if not image_path.exists():
            return  
        
        result = detector._detect_features(str(image_path))
        
        assert "keypoints" in result
        assert "descriptors" in result
        assert result["keypoints"] > 0
        assert result["descriptors"][1] == 128

