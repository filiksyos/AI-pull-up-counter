import cv2
import numpy as np
from typing import List, Dict, Any, Optional
import time

class OverlaySystem:
    def __init__(self):
        self.last_event_time = None
        self.animation_duration = 2.0  # seconds
        self.current_animation_color = (255, 255, 255)  # white
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        
    def add_pull_up_overlays(self, frame: np.ndarray, pull_up_events: List[Dict], 
                            current_time: float, stats: Dict) -> np.ndarray:
        """Add comprehensive overlays to frame"""
        
        # Get current pull-up event
        current_event = self._get_current_event(pull_up_events, current_time)
        
        # Add main statistics overlay
        frame = self._add_stats_overlay(frame, pull_up_events, current_time)
        
        # Add progress bar
        frame = self._add_progress_overlay(frame, pull_up_events, current_time)
        
        # Add feedback text
        if current_event:
            frame = self._add_feedback_overlay(frame, current_event)
        
        # Add form score indicator
        frame = self._add_form_score_overlay(frame, current_event)
        
        # Add processing info
        frame = self._add_processing_info(frame, stats)
        
        # Add timestamp
        frame = self._add_timestamp_overlay(frame, current_time)
        
        return frame
    
    def _add_stats_overlay(self, frame: np.ndarray, events: List[Dict], current_time: float) -> np.ndarray:
        """Add main statistics overlay in top-left corner"""
        completed = len([e for e in events if e.get('result') == 'completed'])
        failed = len([e for e in events if e.get('result') == 'failed'])
        
        # Calculate current animation color
        animation_color = self._get_animation_color(events, current_time)
        
        # Main stats text
        stats_text = [
            f"Pull-ups: {completed}",
            f"Failed: {failed}",
            f"Total: {completed + failed}"
        ]
        
        # Add background box
        box_width = 200
        box_height = 130
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (box_width, box_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Add border
        cv2.rectangle(frame, (10, 10), (box_width, box_height), (255, 255, 255), 2)
        
        # Add stats text
        for i, text in enumerate(stats_text):
            y_pos = 45 + i * 35
            
            # Black outline
            cv2.putText(frame, text, (20, y_pos), self.font, 1.0, (0, 0, 0), 4)
            # Colored text
            cv2.putText(frame, text, (20, y_pos), self.font, 1.0, animation_color, 2)
        
        return frame
    
    def _add_progress_overlay(self, frame: np.ndarray, events: List[Dict], current_time: float) -> np.ndarray:
        """Add progress bar overlay in top-right corner"""
        if not events:
            return frame
        
        # Calculate progress through workout
        total_events = len(events)
        current_events = len([e for e in events if self._timestamp_to_seconds(e.get('timestamp_end', '0:00')) <= current_time])
        
        # Progress bar dimensions
        bar_width = 250
        bar_height = 25
        bar_x = frame.shape[1] - bar_width - 20
        bar_y = 30
        
        # Draw progress bar background
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 2)
        
        # Draw progress fill
        if total_events > 0:
            progress_ratio = current_events / total_events
            fill_width = int(progress_ratio * bar_width)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height), (0, 255, 0), -1)
        
        # Progress text
        progress_text = f"Progress: {current_events}/{total_events}"
        text_size = cv2.getTextSize(progress_text, self.font, 0.6, 2)[0]
        text_x = bar_x + (bar_width - text_size[0]) // 2
        text_y = bar_y - 10
        
        cv2.putText(frame, progress_text, (text_x, text_y), self.font, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def _add_feedback_overlay(self, frame: np.ndarray, event: Dict) -> np.ndarray:
        """Add feedback text overlay at bottom center"""
        feedback = event.get('feedback', '')
        if not feedback:
            return frame
        
        # Text properties
        font_scale = 1.0
        thickness = 2
        
        # Calculate text size and position
        text_size = cv2.getTextSize(feedback, self.font, font_scale, thickness)[0]
        text_x = (frame.shape[1] - text_size[0]) // 2
        text_y = frame.shape[0] - 60
        
        # Add background rectangle
        padding = 15
        bg_start = (text_x - padding, text_y - text_size[1] - padding)
        bg_end = (text_x + text_size[0] + padding, text_y + padding)
        
        overlay = frame.copy()
        cv2.rectangle(overlay, bg_start, bg_end, (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
        
        # Add border
        cv2.rectangle(frame, bg_start, bg_end, (255, 255, 255), 2)
        
        # Add feedback text
        cv2.putText(frame, feedback, (text_x, text_y), self.font, font_scale, (255, 255, 255), thickness)
        
        return frame
    
    def _add_form_score_overlay(self, frame: np.ndarray, event: Dict) -> np.ndarray:
        """Add form score indicator in top-right corner"""
        if not event or 'form_score' not in event:
            return frame
        
        score = event['form_score']
        
        # Score circle position
        center_x = frame.shape[1] - 80
        center_y = 100
        radius = 35
        
        # Color based on score
        if score >= 80:
            color = (0, 255, 0)  # Green
        elif score >= 60:
            color = (0, 255, 255)  # Yellow
        else:
            color = (0, 0, 255)  # Red
        
        # Draw circle background
        cv2.circle(frame, (center_x, center_y), radius, color, -1)
        cv2.circle(frame, (center_x, center_y), radius, (255, 255, 255), 3)
        
        # Add score text
        score_text = f"{score}"
        text_size = cv2.getTextSize(score_text, self.font, 1.0, 2)[0]
        text_x = center_x - text_size[0] // 2
        text_y = center_y + text_size[1] // 2
        
        cv2.putText(frame, score_text, (text_x, text_y), self.font, 1.0, (255, 255, 255), 2)
        
        # Add label
        cv2.putText(frame, "FORM", (center_x - 20, center_y + 55), self.font, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def _add_processing_info(self, frame: np.ndarray, stats: Dict) -> np.ndarray:
        """Add processing information in bottom-left corner"""
        info_text = [
            f"AI: {stats.get('model_used', 'Gemini 2.5 Flash')}",
            f"Frames: {stats.get('frames_analyzed', 0)}",
            f"API Calls: {stats.get('api_calls', 0)}"
        ]
        
        # Add semi-transparent background
        bg_height = len(info_text) * 20 + 20
        bg_width = 200
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, frame.shape[0] - bg_height - 10), 
                     (bg_width, frame.shape[0] - 10), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Add info text
        for i, text in enumerate(info_text):
            y_pos = frame.shape[0] - bg_height + 20 + i * 20
            cv2.putText(frame, text, (15, y_pos), self.font, 0.4, (200, 200, 200), 1)
        
        return frame
    
    def _add_timestamp_overlay(self, frame: np.ndarray, current_time: float) -> np.ndarray:
        """Add timestamp overlay in bottom-right corner"""
        minutes = int(current_time // 60)
        seconds = int(current_time % 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"
        
        # Position in bottom-right
        text_size = cv2.getTextSize(timestamp, self.font, 0.8, 2)[0]
        text_x = frame.shape[1] - text_size[0] - 20
        text_y = frame.shape[0] - 20
        
        # Add background
        padding = 10
        bg_start = (text_x - padding, text_y - text_size[1] - padding)
        bg_end = (text_x + text_size[0] + padding, text_y + padding)
        
        overlay = frame.copy()
        cv2.rectangle(overlay, bg_start, bg_end, (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Add timestamp
        cv2.putText(frame, timestamp, (text_x, text_y), self.font, 0.8, (255, 255, 255), 2)
        
        return frame
    
    def _get_current_event(self, events: List[Dict], current_time: float) -> Optional[Dict]:
        """Get current pull-up event based on timestamp"""
        for event in events:
            start_time = self._timestamp_to_seconds(event.get('timestamp_start', '0:00'))
            end_time = self._timestamp_to_seconds(event.get('timestamp_end', '0:00'))
            
            if start_time <= current_time <= end_time + 3.0:  # 3 second buffer for feedback
                return event
        
        return None
    
    def _timestamp_to_seconds(self, timestamp: str) -> float:
        """Convert timestamp string to seconds"""
        try:
            parts = timestamp.split(':')
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        except (ValueError, IndexError):
            return 0.0
    
    def _get_animation_color(self, events: List[Dict], current_time: float) -> tuple:
        """Get animation color for recent events"""
        # Find most recent event
        recent_event = None
        for event in events:
            end_time = self._timestamp_to_seconds(event.get('timestamp_end', '0:00'))
            if current_time - end_time < self.animation_duration:
                recent_event = event
                break
        
        if recent_event:
            if recent_event.get('result') == 'completed':
                return (0, 255, 0)  # Green for successful pull-up
            else:
                return (0, 0, 255)  # Red for failed attempt
        
        return (255, 255, 255)  # White default
    
    def add_pull_up_indicator(self, frame: np.ndarray, pose_data: Dict) -> np.ndarray:
        """Add pull-up phase indicator"""
        if not pose_data:
            return frame
        
        phase = pose_data.get('metrics', {}).get('pull_up_phase', 'unknown')
        
        # Phase indicator in center-top
        phase_text = f"Phase: {phase.upper()}"
        text_size = cv2.getTextSize(phase_text, self.font, 0.8, 2)[0]
        text_x = (frame.shape[1] - text_size[0]) // 2
        text_y = 40
        
        # Color based on phase
        phase_colors = {
            'hanging': (255, 255, 255),    # White
            'ascending': (0, 255, 255),    # Yellow
            'top_position': (0, 255, 0),   # Green
            'descending': (255, 0, 255),   # Magenta
            'transition': (128, 128, 128)   # Gray
        }
        color = phase_colors.get(phase, (255, 255, 255))
        
        # Add background
        padding = 10
        bg_start = (text_x - padding, text_y - text_size[1] - padding)
        bg_end = (text_x + text_size[0] + padding, text_y + padding)
        
        overlay = frame.copy()
        cv2.rectangle(overlay, bg_start, bg_end, (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Add phase text
        cv2.putText(frame, phase_text, (text_x, text_y), self.font, 0.8, color, 2)
        
        return frame 