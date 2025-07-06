#!/usr/bin/env python3
"""
Quick test script to verify AI Pull-Up Counter components
"""

import os
import sys
from pathlib import Path

def test_imports():
    """Test if all components can be imported"""
    print("🧪 Testing component imports...")
    
    try:
        # Test core components
        from frame_extractor import FrameExtractor
        print("✅ FrameExtractor")
        
        from ai_analyzer import PullUpAIAnalyzer
        print("✅ PullUpAIAnalyzer")
        
        from utils.pose_detector import PullUpPoseDetector
        print("✅ PullUpPoseDetector")
        
        from utils.overlay_system import OverlaySystem
        print("✅ OverlaySystem")
        
        from utils.video_utils import get_video_info, validate_video
        print("✅ VideoUtils")
        
        import config
        print("✅ Config")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\n🔧 Testing configuration...")
    
    try:
        import config
        
        # Check if required constants exist
        required_configs = [
            'OPENROUTER_BASE_URL',
            'MODEL_NAME', 
            'KEY_FRAME_INTERVAL',
            'MAX_FRAMES_PER_REQUEST'
        ]
        
        for conf in required_configs:
            if hasattr(config, conf):
                print(f"✅ {conf}: {getattr(config, conf)}")
            else:
                print(f"❌ Missing config: {conf}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def test_video_processing():
    """Test video processing components without actual video"""
    print("\n📹 Testing video processing capabilities...")
    
    try:
        from utils.video_utils import get_video_info
        
        # Test with a non-existent file (should handle gracefully)
        info = get_video_info("nonexistent.mp4")
        if info == {}:
            print("✅ Video info handles missing files")
        else:
            print("❌ Video info should return empty dict for missing files")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Video processing error: {e}")
        return False

def test_ai_analyzer_init():
    """Test AI analyzer initialization"""
    print("\n🤖 Testing AI analyzer initialization...")
    
    try:
        # This should fail gracefully if no API key
        from ai_analyzer import PullUpAIAnalyzer
        
        # Try to initialize (will fail without API key, but shouldn't crash)
        try:
            analyzer = PullUpAIAnalyzer()
            print("✅ AI analyzer initialized successfully")
            return True
        except ValueError as e:
            if "OPENROUTER_API_KEY" in str(e):
                print("✅ AI analyzer correctly requires API key")
                return True
            else:
                print(f"❌ Unexpected API key error: {e}")
                return False
        
    except Exception as e:
        print(f"❌ AI analyzer error: {e}")
        return False

def test_pose_detector_init():
    """Test pose detector initialization"""
    print("\n🦴 Testing pose detector initialization...")
    
    try:
        from utils.pose_detector import PullUpPoseDetector
        
        detector = PullUpPoseDetector()
        print("✅ Pose detector initialized successfully")
        
        # Test if MediaPipe is working
        if hasattr(detector, 'mp_pose') and hasattr(detector, 'pose'):
            print("✅ MediaPipe components loaded")
            return True
        else:
            print("❌ MediaPipe components not properly loaded")
            return False
        
    except Exception as e:
        print(f"❌ Pose detector error: {e}")
        return False

def main():
    """Run all tests"""
    print("🏋️ AI Pull-Up Counter - Component Tests")
    print("=" * 50)
    
    tests = [
        ("Component Imports", test_imports),
        ("Configuration", test_config),
        ("Video Processing", test_video_processing),
        ("AI Analyzer", test_ai_analyzer_init),
        ("Pose Detector", test_pose_detector_init)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n📋 Testing {name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {name} test failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All component tests passed!")
        print("💡 System is ready for pull-up analysis")
        print("\n🚀 Next steps:")
        print("1. Run setup validation: python setup.py")
        print("2. Add your video as input_video.mp4")
        print("3. Run analysis: python pullup.py")
    else:
        print("⚠️ Some tests failed. Check your installation:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Check Python version (3.8+ required)")
        print("3. Run tests again: python test_setup.py")

if __name__ == "__main__":
    main() 