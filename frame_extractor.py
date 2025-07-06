import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import json
from typing import List, Tuple, Dict
from config import IMAGE_QUALITY

class FrameExtractor:
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps
        
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        print(f"📹 Video loaded: {self.fps} FPS, {self.total_frames} frames, {self.duration:.1f}s duration")
        
    def extract_key_frames(self, interval: float = 0.5) -> List[Dict]:
        """Extract key frames at specified intervals"""
        key_frames = []
        frame_numbers = []
        
        # Calculate frame numbers to extract
        for t in np.arange(0, self.duration, interval):
            frame_number = int(t * self.fps)
            if frame_number < self.total_frames:
                frame_numbers.append(frame_number)
        
        print(f"🎯 Extracting {len(frame_numbers)} key frames...")
        
        # Extract frames
        for i, frame_num in enumerate(frame_numbers):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = self.cap.read()
            if ret:
                timestamp = frame_num / self.fps
                base64_frame = self.frame_to_base64(frame)
                key_frames.append({
                    'frame_number': frame_num,
                    'timestamp': timestamp,
                    'base64_data': base64_frame
                })
                
                # Progress indicator
                if (i + 1) % 10 == 0:
                    print(f"   Extracted {i + 1}/{len(frame_numbers)} frames...")
        
        print(f"✅ Successfully extracted {len(key_frames)} key frames")
        return key_frames
    
    def frame_to_base64(self, frame: np.ndarray) -> str:
        """Convert frame to base64 string"""
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(frame_rgb)
        
        # Save to BytesIO buffer
        buffer = BytesIO()
        pil_image.save(buffer, format='JPEG', quality=IMAGE_QUALITY)
        
        # Encode to base64
        base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return base64_string
    
    def extract_motion_frames(self, motion_threshold: float = 30.0) -> List[Dict]:
        """Extract frames with significant motion for pull-up analysis"""
        motion_frames = []
        prev_frame = None
        frame_count = 0
        
        print(f"🎬 Analyzing motion with threshold: {motion_threshold}")
        
        # Reset video capture to beginning
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
                
            # Convert to grayscale for motion detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            if prev_frame is not None:
                # Calculate frame difference
                frame_diff = cv2.absdiff(prev_frame, gray)
                thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
                
                # Calculate motion score
                motion_score = np.sum(thresh) / (frame.shape[0] * frame.shape[1])
                
                if motion_score > motion_threshold:
                    timestamp = frame_count / self.fps
                    base64_frame = self.frame_to_base64(frame)
                    motion_frames.append({
                        'frame_number': frame_count,
                        'timestamp': timestamp,
                        'motion_score': motion_score,
                        'base64_data': base64_frame
                    })
            
            prev_frame = gray
            frame_count += 1
            
            # Progress indicator
            if frame_count % (self.fps * 10) == 0:  # Every 10 seconds
                print(f"   Analyzed {frame_count} frames...")
        
        print(f"✅ Found {len(motion_frames)} frames with significant motion")
        return motion_frames
    
    def get_video_info(self) -> Dict:
        """Get video information"""
        return {
            'fps': self.fps,
            'total_frames': self.total_frames,
            'duration': self.duration,
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        }
    
    def __del__(self):
        if hasattr(self, 'cap'):
            self.cap.release() 