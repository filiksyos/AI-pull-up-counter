import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "google/gemini-2.5-flash-preview"  # Cost-effective multimodal
# Alternative: "google/gemini-2.5-pro" for higher accuracy

# Video Processing Configuration
FRAME_EXTRACTION_RATE = 3  # Extract every 3rd frame for analysis
KEY_FRAME_INTERVAL = 0.5   # Analyze key frames every 0.5 seconds
MAX_FRAMES_PER_REQUEST = 8  # Send 8 frames per API request
IMAGE_QUALITY = 85         # JPEG quality for base64 encoding

# Pull-Up Detection Thresholds
CHIN_OVER_BAR_THRESHOLD = 0.1    # Relative position threshold
FULL_EXTENSION_ANGLE = 170       # Elbow angle for full extension
MIN_HOLD_TIME = 0.2             # Minimum time at top position

# Web Server Configuration
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = 8000
UPLOAD_DIR = "/app/input_videos"
OUTPUT_DIR = "/app/output_videos"
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB limit 