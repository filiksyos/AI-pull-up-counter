#!/usr/bin/env python3
"""
Setup and validation script for AI Pull-Up Counter
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    else:
        print(f"✅ Python version: {sys.version.split()[0]}")
        return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'opencv-python',
        'mediapipe', 
        'numpy',
        'requests',
        'python-dotenv',
        'pillow'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n💡 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists and has API key"""
    env_file = Path('.env')
    template_file = Path('.env.template')
    
    if not env_file.exists():
        if template_file.exists():
            print("❌ .env file not found")
            print("💡 Copy .env.template to .env and add your API key:")
            print("   cp .env.template .env")
            return False
        else:
            print("❌ No .env or .env.template file found")
            return False
    
    # Check if API key is set
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key or api_key == 'your_openrouter_api_key_here':
        print("❌ OPENROUTER_API_KEY not set in .env file")
        print("💡 Edit .env and add your OpenRouter API key")
        return False
    
    print("✅ .env file configured")
    return True

def test_api_connection():
    """Test connection to OpenRouter API"""
    try:
        from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL
        import requests
        
        if not OPENROUTER_API_KEY:
            print("❌ API key not loaded")
            return False
        
        # Test API connection
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{OPENROUTER_BASE_URL}/models",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ OpenRouter API connection successful")
            return True
        else:
            print(f"❌ API connection failed: {response.status_code}")
            print("💡 Check your API key and account credits")
            return False
            
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False

def check_input_video():
    """Check if input video exists"""
    input_video = Path('input_video.mp4')
    
    if input_video.exists():
        print("✅ input_video.mp4 found")
        return True
    else:
        print("⚠️ input_video.mp4 not found")
        print("💡 Place your pull-up video as 'input_video.mp4' to test")
        return False

def create_sample_env():
    """Create sample .env file if it doesn't exist"""
    env_template = Path('.env.template')
    env_file = Path('.env')
    
    if not env_file.exists() and env_template.exists():
        try:
            env_file.write_text(env_template.read_text())
            print("✅ Created .env file from template")
            print("💡 Edit .env and add your OpenRouter API key")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    
    return True

def main():
    """Run setup validation"""
    print("🏋️ AI Pull-Up Counter - Setup Validation")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("API Connection", test_api_connection),
        ("Input Video", check_input_video)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n📋 Checking {name}...")
        if check_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Setup Status: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 Setup complete! Ready to analyze pull-ups.")
        print("\n🚀 Run the analysis with:")
        print("   python pullup.py")
    elif passed >= total - 1:  # Allow missing input video
        print("⚠️ Setup mostly complete!")
        if not Path('input_video.mp4').exists():
            print("💡 Add your pull-up video as 'input_video.mp4' and run:")
            print("   python pullup.py")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        if passed < 3:  # Missing critical components
            print("\n🔧 Quick setup:")
            print("1. Install dependencies: pip install -r requirements.txt")
            if not Path('.env').exists():
                create_sample_env()
            print("2. Edit .env and add your OpenRouter API key")
            print("3. Run setup again: python setup.py")

if __name__ == "__main__":
    main() 