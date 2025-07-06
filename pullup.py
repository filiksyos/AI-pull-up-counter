import cv2
import numpy as np
import os
import json
from typing import List, Dict, Any
from datetime import datetime

from frame_extractor import FrameExtractor
from ai_analyzer import PullUpAIAnalyzer
from utils.pose_detector import PullUpPoseDetector
from utils.overlay_system import OverlaySystem
from config import *

class PullUpProcessor:
    def __init__(self, input_video_path: str, output_video_path: str):
        self.input_path = input_video_path
        self.output_path = output_video_path
        
        # Validate input file
        if not os.path.exists(input_video_path):
            raise FileNotFoundError(f"Input video not found: {input_video_path}")
        
        # Initialize components
        try:
            self.frame_extractor = FrameExtractor(input_video_path)
            self.ai_analyzer = PullUpAIAnalyzer()
            self.pose_detector = PullUpPoseDetector()
            self.overlay_system = OverlaySystem()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize components: {e}")
        
        # Processing state
        self.pull_up_count = 0
        self.failed_attempts = 0
        self.current_analysis = None
        self.processing_stats = {
            'total_frames': 0,
            'frames_analyzed': 0,
            'api_calls': 0,
            'processing_time': 0,
            'estimated_cost': 0.0
        }
    
    def process_video(self) -> Dict[str, Any]:
        """Main video processing pipeline"""
        start_time = datetime.now()
        
        print("🎬 Starting AI Pull-Up Counter analysis...")
        print(f"📁 Input: {self.input_path}")
        print(f"📁 Output: {self.output_path}")
        
        try:
            # Step 1: Extract key frames
            print("\n📸 Step 1: Extracting key frames...")
            key_frames = self.frame_extractor.extract_key_frames(KEY_FRAME_INTERVAL)
            self.processing_stats['frames_analyzed'] = len(key_frames)
            
            if not key_frames:
                raise RuntimeError("No frames could be extracted from video")
            
            # Estimate cost
            estimated_cost = self.ai_analyzer.estimate_cost(len(key_frames))
            self.processing_stats['estimated_cost'] = estimated_cost
            print(f"💰 Estimated API cost: ${estimated_cost:.4f}")
            
            # Step 2: AI Analysis
            print(f"\n🤖 Step 2: Analyzing {len(key_frames)} frames with Gemini AI...")
            ai_analysis = self.ai_analyzer.analyze_pull_up_sequence(key_frames)
            self.processing_stats['api_calls'] = ai_analysis.get('processing_stats', {}).get('api_calls_made', 0)
            
            # Step 3: Generate output video with overlays
            print("\n🎨 Step 3: Generating output video with overlays...")
            self._generate_output_video(ai_analysis)
            
            # Step 4: Save analysis results
            print("\n💾 Step 4: Saving analysis results...")
            self._save_analysis_results(ai_analysis)
            
            end_time = datetime.now()
            self.processing_stats['processing_time'] = (end_time - start_time).total_seconds()
            
            # Print final summary
            self._print_summary(ai_analysis)
            
            return {
                'analysis': ai_analysis,
                'stats': self.processing_stats,
                'success': True
            }
            
        except Exception as e:
            print(f"\n❌ Error during processing: {e}")
            return {
                'analysis': {},
                'stats': self.processing_stats,
                'success': False,
                'error': str(e)
            }
    
    def _generate_output_video(self, analysis: Dict[str, Any]):
        """Generate output video with overlays"""
        cap = cv2.VideoCapture(self.input_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            raise RuntimeError(f"Could not open output video writer: {self.output_path}")
        
        # Process pull-up events from AI analysis
        pull_up_events = analysis.get('pull_ups', [])
        processing_stats = analysis.get('processing_stats', {})
        
        frame_count = 0
        last_progress_update = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                current_time = frame_count / fps
                
                # Add pose detection (optional - for real-time feedback)
                pose_data = self.pose_detector.detect_pull_up_landmarks(frame)
                if pose_data:
                    # Optionally draw pose landmarks
                    # frame = self.pose_detector.draw_landmarks(frame, pose_data['raw_landmarks'])
                    
                    # Add pull-up phase indicator
                    frame = self.overlay_system.add_pull_up_indicator(frame, pose_data)
                
                # Add comprehensive overlays
                frame = self.overlay_system.add_pull_up_overlays(
                    frame, pull_up_events, current_time, processing_stats
                )
                
                out.write(frame)
                frame_count += 1
                
                # Progress indicator (every 5 seconds)
                if frame_count % (fps * 5) == 0:
                    progress = (frame_count / total_frames) * 100
                    print(f"   Video processing: {progress:.1f}%")
                    last_progress_update = frame_count
            
            # Final progress update
            if frame_count > last_progress_update:
                print("   Video processing: 100.0%")
        
        finally:
            cap.release()
            out.release()
            
        self.processing_stats['total_frames'] = frame_count
        print(f"✅ Output video saved: {self.output_path}")
    
    def _save_analysis_results(self, analysis: Dict[str, Any]):
        """Save analysis results to JSON file"""
        pull_ups = analysis.get('pull_ups', [])
        summary = analysis.get('summary', {})
        
        output_data = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "input_video": self.input_path,
                "output_video": self.output_path,
                "model_used": MODEL_NAME,
                "processing_stats": self.processing_stats
            },
            "pull_ups": pull_ups,
            "summary": {
                "total_completed": summary.get('total_completed', 0),
                "total_failed": summary.get('total_failed', 0),
                "total_attempts": summary.get('total_attempts', 0),
                "success_rate": summary.get('success_rate', 0),
                "average_form_score": summary.get('average_form_score', 0)
            },
            "detailed_analysis": {
                "frame_interval": KEY_FRAME_INTERVAL,
                "frames_per_request": MAX_FRAMES_PER_REQUEST,
                "cost_breakdown": {
                    "frames_analyzed": self.processing_stats['frames_analyzed'],
                    "api_calls_made": self.processing_stats['api_calls'],
                    "estimated_cost_usd": self.processing_stats['estimated_cost']
                }
            }
        }
        
        # Save to pullup.json
        with open('pullup.json', 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"📊 Analysis results saved to: pullup.json")
    
    def _print_summary(self, analysis: Dict[str, Any]):
        """Print comprehensive summary"""
        summary = analysis.get('summary', {})
        pull_ups = analysis.get('pull_ups', [])
        
        print("\n" + "="*60)
        print("🏋️ AI PULL-UP COUNTER - ANALYSIS COMPLETE")
        print("="*60)
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"   ✅ Completed pull-ups: {summary.get('total_completed', 0)}")
        print(f"   ❌ Failed attempts: {summary.get('total_failed', 0)}")
        print(f"   📈 Total attempts: {summary.get('total_attempts', 0)}")
        print(f"   🎯 Success rate: {summary.get('success_rate', 0):.1f}%")
        print(f"   📏 Average form score: {summary.get('average_form_score', 0):.1f}/100")
        
        print(f"\n🤖 PROCESSING STATS:")
        print(f"   🎬 Total frames: {self.processing_stats['total_frames']}")
        print(f"   🔍 Frames analyzed: {self.processing_stats['frames_analyzed']}")
        print(f"   📡 API calls made: {self.processing_stats['api_calls']}")
        print(f"   ⏱️ Processing time: {self.processing_stats['processing_time']:.1f}s")
        print(f"   💰 Estimated cost: ${self.processing_stats['estimated_cost']:.4f}")
        print(f"   🧠 AI model used: {MODEL_NAME}")
        
        if pull_ups:
            print(f"\n📋 DETAILED BREAKDOWN:")
            for i, pullup in enumerate(pull_ups, 1):
                result_emoji = "✅" if pullup.get('result') == 'completed' else "❌"
                print(f"   {result_emoji} Pull-up #{i}: {pullup.get('result', 'unknown')}")
                print(f"      ⏰ Time: {pullup.get('timestamp_start', 'N/A')} - {pullup.get('timestamp_end', 'N/A')}")
                print(f"      📏 Form score: {pullup.get('form_score', 'N/A')}/100")
                if pullup.get('feedback'):
                    print(f"      💬 Feedback: {pullup.get('feedback')}")
                if pullup.get('failure_reason'):
                    print(f"      ⚠️ Issue: {pullup.get('failure_reason')}")
                print()
        
        print(f"📁 Files generated:")
        print(f"   🎥 Video: {self.output_path}")
        print(f"   📄 Analysis: pullup.json")
        print("\n" + "="*60)

def main():
    """Main entry point"""
    input_video = "input_video.mp4"
    output_video = "output_video.mp4"
    
    # Check for API key
    if not OPENROUTER_API_KEY:
        print("❌ Error: OPENROUTER_API_KEY not set in environment variables")
        print("💡 Please create a .env file with your OpenRouter API key")
        print("   Copy .env.template to .env and add your API key")
        return
    
    # Check for input video
    if not os.path.exists(input_video):
        print(f"❌ Error: Input video not found: {input_video}")
        print("💡 Please place your pull-up video as 'input_video.mp4' in this directory")
        return
    
    try:
        # Create processor and run analysis
        processor = PullUpProcessor(input_video, output_video)
        results = processor.process_video()
        
        if results['success']:
            print("\n🎉 Processing completed successfully!")
        else:
            print(f"\n💥 Processing failed: {results.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print("📝 Please check your video file and API configuration")

if __name__ == "__main__":
    main() 