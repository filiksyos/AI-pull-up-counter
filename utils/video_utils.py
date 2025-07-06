import cv2
import numpy as np
from typing import Tuple, Optional, List

def get_video_info(video_path: str) -> dict:
    """Get comprehensive video information"""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        return {}
    
    info = {
        'fps': int(cap.get(cv2.CAP_PROP_FPS)),
        'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        'fourcc': int(cap.get(cv2.CAP_PROP_FOURCC)),
        'duration': 0
    }
    
    if info['fps'] > 0:
        info['duration'] = info['frame_count'] / info['fps']
    
    cap.release()
    return info

def validate_video(video_path: str) -> Tuple[bool, str]:
    """Validate if video is suitable for pull-up analysis"""
    try:
        info = get_video_info(video_path)
        
        if not info:
            return False, "Could not read video file"
        
        # Check minimum requirements
        if info['duration'] < 5:
            return False, "Video too short (minimum 5 seconds)"
        
        if info['width'] < 480 or info['height'] < 360:
            return False, "Video resolution too low (minimum 480x360)"
        
        if info['fps'] < 15:
            return False, "Video frame rate too low (minimum 15 FPS)"
        
        return True, "Video is suitable for analysis"
        
    except Exception as e:
        return False, f"Video validation error: {e}"

def resize_video_if_needed(input_path: str, output_path: str, max_width: int = 1920) -> bool:
    """Resize video if it's too large for efficient processing"""
    try:
        cap = cv2.VideoCapture(input_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        if width <= max_width:
            cap.release()
            return False  # No resizing needed
        
        # Calculate new dimensions
        new_width = max_width
        new_height = int(height * (max_width / width))
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (new_width, new_height))
        
        # Process frames
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            resized_frame = cv2.resize(frame, (new_width, new_height))
            out.write(resized_frame)
        
        cap.release()
        out.release()
        return True
        
    except Exception as e:
        print(f"Error resizing video: {e}")
        return False

def extract_thumbnail(video_path: str, timestamp: float = 5.0) -> Optional[np.ndarray]:
    """Extract thumbnail from video at specified timestamp"""
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(timestamp * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        
        cap.release()
        
        if ret:
            return frame
        return None
        
    except Exception:
        return None

def create_video_preview(video_path: str, output_path: str, num_frames: int = 9) -> bool:
    """Create a preview grid of frames from the video"""
    try:
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Calculate frame indices
        frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
        
        # Extract frames
        frames = []
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                # Resize frame for preview
                preview_frame = cv2.resize(frame, (width // 3, height // 3))
                frames.append(preview_frame)
        
        cap.release()
        
        if len(frames) < num_frames:
            return False
        
        # Create grid
        rows = int(np.sqrt(num_frames))
        cols = int(np.ceil(num_frames / rows))
        
        grid_height = rows * (height // 3)
        grid_width = cols * (width // 3)
        grid = np.zeros((grid_height, grid_width, 3), dtype=np.uint8)
        
        for i, frame in enumerate(frames):
            row = i // cols
            col = i % cols
            y_start = row * (height // 3)
            y_end = y_start + (height // 3)
            x_start = col * (width // 3)
            x_end = x_start + (width // 3)
            
            grid[y_start:y_end, x_start:x_end] = frame
        
        # Save preview
        cv2.imwrite(output_path, grid)
        return True
        
    except Exception as e:
        print(f"Error creating preview: {e}")
        return False

def check_video_quality(video_path: str) -> dict:
    """Analyze video quality for pull-up detection"""
    try:
        cap = cv2.VideoCapture(video_path)
        
        # Sample frames for analysis
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_indices = np.linspace(0, total_frames - 1, 10, dtype=int)
        
        brightness_scores = []
        blur_scores = []
        
        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Brightness analysis
                brightness = np.mean(gray)
                brightness_scores.append(brightness)
                
                # Blur analysis (Laplacian variance)
                blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
                blur_scores.append(blur_score)
        
        cap.release()
        
        avg_brightness = np.mean(brightness_scores)
        avg_blur = np.mean(blur_scores)
        
        # Quality assessment
        quality = {
            'brightness_score': avg_brightness,
            'blur_score': avg_blur,
            'brightness_quality': 'good' if 50 <= avg_brightness <= 200 else 'poor',
            'blur_quality': 'good' if avg_blur > 100 else 'poor',
            'overall_quality': 'good' if (50 <= avg_brightness <= 200) and (avg_blur > 100) else 'needs_improvement'
        }
        
        return quality
        
    except Exception as e:
        return {'error': str(e)}

def convert_video_format(input_path: str, output_path: str, target_fps: int = 30) -> bool:
    """Convert video to optimal format for processing"""
    try:
        cap = cv2.VideoCapture(input_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Create output video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, target_fps, (width, height))
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            out.write(frame)
            frame_count += 1
        
        cap.release()
        out.release()
        
        return frame_count > 0
        
    except Exception as e:
        print(f"Error converting video: {e}")
        return False 