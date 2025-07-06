import mediapipe as mp
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple

class PullUpPoseDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,  # Higher accuracy
            enable_segmentation=False,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
    def detect_pull_up_landmarks(self, frame: np.ndarray) -> Optional[Dict]:
        """Extract key landmarks for pull-up analysis"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        
        if not results.pose_landmarks:
            return None
            
        landmarks = results.pose_landmarks.landmark
        
        # Extract key points for pull-up analysis
        key_points = {
            'nose': self._get_landmark_coords(landmarks[self.mp_pose.PoseLandmark.NOSE]),
            'left_shoulder': self._get_landmark_coords(landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]),
            'right_shoulder': self._get_landmark_coords(landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]),
            'left_elbow': self._get_landmark_coords(landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW]),
            'right_elbow': self._get_landmark_coords(landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW]),
            'left_wrist': self._get_landmark_coords(landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]),
            'right_wrist': self._get_landmark_coords(landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]),
            'left_hip': self._get_landmark_coords(landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]),
            'right_hip': self._get_landmark_coords(landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP])
        }
        
        # Calculate derived metrics
        metrics = self._calculate_pull_up_metrics(key_points)
        
        return {
            'landmarks': key_points,
            'metrics': metrics,
            'raw_landmarks': results.pose_landmarks
        }
    
    def _get_landmark_coords(self, landmark) -> Tuple[float, float, float]:
        """Extract x, y, z coordinates from landmark"""
        return (landmark.x, landmark.y, landmark.z)
    
    def _calculate_pull_up_metrics(self, key_points: Dict) -> Dict:
        """Calculate pull-up specific metrics"""
        metrics = {}
        
        # Calculate chin height relative to shoulders
        chin_y = key_points['nose'][1]  # Using nose as chin approximation
        shoulder_y = (key_points['left_shoulder'][1] + key_points['right_shoulder'][1]) / 2
        metrics['chin_to_shoulder_ratio'] = chin_y - shoulder_y
        
        # Calculate elbow angles
        left_elbow_angle = self._calculate_angle(
            key_points['left_shoulder'], 
            key_points['left_elbow'], 
            key_points['left_wrist']
        )
        right_elbow_angle = self._calculate_angle(
            key_points['right_shoulder'], 
            key_points['right_elbow'], 
            key_points['right_wrist']
        )
        metrics['left_elbow_angle'] = left_elbow_angle
        metrics['right_elbow_angle'] = right_elbow_angle
        metrics['avg_elbow_angle'] = (left_elbow_angle + right_elbow_angle) / 2
        
        # Calculate body alignment
        shoulder_center = (
            (key_points['left_shoulder'][0] + key_points['right_shoulder'][0]) / 2,
            (key_points['left_shoulder'][1] + key_points['right_shoulder'][1]) / 2
        )
        hip_center = (
            (key_points['left_hip'][0] + key_points['right_hip'][0]) / 2,
            (key_points['left_hip'][1] + key_points['right_hip'][1]) / 2
        )
        
        # Calculate body angle (deviation from vertical)
        body_angle = np.arctan2(
            abs(shoulder_center[0] - hip_center[0]),
            abs(shoulder_center[1] - hip_center[1])
        ) * 180 / np.pi
        metrics['body_alignment_angle'] = body_angle
        
        # Calculate grip width
        grip_width = abs(key_points['left_wrist'][0] - key_points['right_wrist'][0])
        metrics['grip_width'] = grip_width
        
        # Determine pull-up phase
        metrics['pull_up_phase'] = self._determine_pull_up_phase(metrics)
        
        # Calculate form score
        metrics['form_score'] = self._calculate_form_score(metrics)
        
        return metrics
    
    def _calculate_angle(self, point1: Tuple, point2: Tuple, point3: Tuple) -> float:
        """Calculate angle between three points"""
        # Convert to numpy arrays
        a = np.array(point1[:2])  # Use only x, y coordinates
        b = np.array(point2[:2])
        c = np.array(point3[:2])
        
        # Calculate vectors
        ba = a - b
        bc = c - b
        
        # Calculate angle
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        
        return np.degrees(angle)
    
    def _determine_pull_up_phase(self, metrics: Dict) -> str:
        """Determine current phase of pull-up"""
        chin_ratio = metrics['chin_to_shoulder_ratio']
        elbow_angle = metrics['avg_elbow_angle']
        
        if elbow_angle > 160:
            return "hanging"
        elif elbow_angle > 120 and chin_ratio > 0:
            return "ascending"
        elif elbow_angle <= 120 and chin_ratio < -0.05:
            return "top_position"
        elif elbow_angle > 120 and chin_ratio > 0:
            return "descending"
        else:
            return "transition"
    
    def _calculate_form_score(self, metrics: Dict) -> int:
        """Calculate form score based on various metrics"""
        score = 100
        
        # Penalize for poor body alignment
        if metrics['body_alignment_angle'] > 15:
            score -= 20
        elif metrics['body_alignment_angle'] > 10:
            score -= 10
        
        # Penalize for asymmetric elbow angles
        elbow_diff = abs(metrics['left_elbow_angle'] - metrics['right_elbow_angle'])
        if elbow_diff > 20:
            score -= 15
        elif elbow_diff > 10:
            score -= 8
        
        # Bonus for full extension
        if metrics['avg_elbow_angle'] > 160:
            score += 5
        
        return max(0, min(100, score))
    
    def draw_landmarks(self, frame: np.ndarray, landmarks, show_connections: bool = True) -> np.ndarray:
        """Draw pose landmarks on frame"""
        if landmarks:
            if show_connections:
                # Draw connections
                self.mp_drawing.draw_landmarks(
                    frame, 
                    landmarks, 
                    self.mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
                )
            else:
                # Draw only landmarks
                self.mp_drawing.draw_landmarks(
                    frame, 
                    landmarks, 
                    None,
                    landmark_drawing_spec=self.mp_drawing.DrawingSpec(
                        color=(255, 255, 255), thickness=2, circle_radius=3
                    )
                )
        return frame
    
    def draw_pull_up_analysis(self, frame: np.ndarray, pose_data: Dict) -> np.ndarray:
        """Draw pull-up specific analysis overlays"""
        if not pose_data:
            return frame
        
        landmarks = pose_data['landmarks']
        metrics = pose_data['metrics']
        
        # Convert normalized coordinates to pixel coordinates
        h, w = frame.shape[:2]
        
        # Draw key points
        key_points = ['nose', 'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist']
        for point_name in key_points:
            if point_name in landmarks:
                x, y = landmarks[point_name][:2]
                px, py = int(x * w), int(y * h)
                cv2.circle(frame, (px, py), 5, (0, 255, 0), -1)
        
        # Draw chin-to-bar line
        nose_x, nose_y = landmarks['nose'][:2]
        nose_px, nose_py = int(nose_x * w), int(nose_y * h)
        
        # Draw horizontal line at bar level (estimated)
        bar_y = int(nose_py - 50)  # Approximate bar position
        cv2.line(frame, (0, bar_y), (w, bar_y), (255, 0, 0), 2)
        cv2.putText(frame, "Pull-up Bar", (10, bar_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        # Draw analysis text
        analysis_text = [
            f"Phase: {metrics['pull_up_phase']}",
            f"Elbow Angle: {metrics['avg_elbow_angle']:.1f}°",
            f"Body Alignment: {metrics['body_alignment_angle']:.1f}°",
            f"Form Score: {metrics['form_score']}/100"
        ]
        
        for i, text in enumerate(analysis_text):
            cv2.putText(frame, text, (10, 30 + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def is_pull_up_position(self, pose_data: Dict) -> bool:
        """Check if person is in pull-up position"""
        if not pose_data:
            return False
        
        metrics = pose_data['metrics']
        
        # Check if arms are raised (typical hanging position)
        if metrics['avg_elbow_angle'] > 140:
            return True
        
        # Check if in pull-up motion
        if metrics['pull_up_phase'] in ['ascending', 'top_position', 'descending']:
            return True
        
        return False 