import cv2
import numpy as np
import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from frame_extractor import FrameExtractor
from ai_analyzer import PullUpAIAnalyzer
from utils.pose_detector import PullUpPoseDetector
from utils.overlay_system import OverlaySystem
from config import *

class WebPullUpProcessor:
    def __init__(self, input_video_path: str, output_video_path: str, progress_callback: Optional[Callable] = None):
        self.input_path = input_video_path
        self.output_path = output_video_path
        self.progress_callback = progress_callback
        
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
    
    async def _update_progress(self, step: int, step_name: str, progress: float, message: str):
        """Update progress via callback if available"""
        if self.progress_callback:
            try:
                if asyncio.iscoroutinefunction(self.progress_callback):
                    await self.progress_callback(step, step_name, progress, message)
                else:
                    self.progress_callback(step, step_name, progress, message)
            except Exception as e:
                print(f"Progress callback error: {e}")
    
    async def process_video(self) -> Dict[str, Any]:
        """Main video processing pipeline with progress updates"""
        start_time = datetime.now()
        
        print("🎬 Starting AI Pull-Up Counter analysis...")
        print(f"📁 Input: {self.input_path}")
        print(f"📁 Output: {self.output_path}")
        
        try:
            # Step 1: Extract key frames
            await self._update_progress(1, "Frame Extraction", 5, "Starting frame extraction...")
            print("\n📸 Step 1: Extracting key frames...")
            
            key_frames = await self._extract_key_frames_with_progress()
            self.processing_stats['frames_analyzed'] = len(key_frames)
            
            if not key_frames:
                raise RuntimeError("No frames could be extracted from video")
            
            # Estimate cost
            estimated_cost = self.ai_analyzer.estimate_cost(len(key_frames))
            self.processing_stats['estimated_cost'] = estimated_cost
            print(f"💰 Estimated API cost: ${estimated_cost:.4f}")
            
            await self._update_progress(1, "Frame Extraction", 25, f"Extracted {len(key_frames)} key frames")
            
            # Step 2: AI Analysis
            await self._update_progress(2, "AI Analysis", 30, "Starting AI analysis...")
            print(f"\n🤖 Step 2: Analyzing {len(key_frames)} frames with Gemini AI...")
            
            ai_analysis = await self._analyze_frames_with_progress(key_frames)
            self.processing_stats['api_calls'] = ai_analysis.get('processing_stats', {}).get('api_calls_made', 0)
            
            await self._update_progress(2, "AI Analysis", 75, "AI analysis completed")
            
            # Step 3: Generate output video with overlays
            await self._update_progress(3, "Video Generation", 80, "Starting video generation...")
            print("\n🎨 Step 3: Generating output video with overlays...")
            
            await self._generate_output_video_with_progress(ai_analysis)
            
            await self._update_progress(3, "Video Generation", 95, "Video generation completed")
            
            # Step 4: Save analysis results
            await self._update_progress(4, "Saving Results", 96, "Saving analysis results...")
            print("\n💾 Step 4: Saving analysis results...")
            self._save_analysis_results(ai_analysis)
            
            end_time = datetime.now()
            self.processing_stats['processing_time'] = (end_time - start_time).total_seconds()
            
            # Print final summary
            self._print_summary(ai_analysis)
            
            await self._update_progress(4, "Complete", 100, "Processing completed successfully!")
            
            return {
                'analysis': ai_analysis,
                'stats': self.processing_stats,
                'success': True
            }
            
        except Exception as e:
            error_msg = f"Error during processing: {e}"
            print(f"\n❌ {error_msg}")
            if self.progress_callback:
                await self.progress_callback(0, "Error", 0, error_msg)
            return {
                'analysis': {},
                'stats': self.processing_stats,
                'success': False,
                'error': str(e)
            }
    
    async def _extract_key_frames_with_progress(self) -> List[Dict]:
        """Extract key frames with progress updates"""
        await self._update_progress(1, "Frame Extraction", 10, "Extracting key frames...")
        
        # Use existing frame extractor but add progress tracking
        key_frames = self.frame_extractor.extract_key_frames(KEY_FRAME_INTERVAL)
        
        await self._update_progress(1, "Frame Extraction", 20, f"Extracted {len(key_frames)} frames")
        return key_frames
    
    async def _analyze_frames_with_progress(self, frame_data: List[Dict]) -> Dict[str, Any]:
        """Analyze frames with progress updates"""
        print(f"🤖 Starting AI analysis with {len(frame_data)} frames using {self.ai_analyzer.model}")
        
        # Split frames into batches for API requests
        frame_batches = self.ai_analyzer._split_frames_into_batches(frame_data)
        all_analyses = []
        
        for i, batch in enumerate(frame_batches):
            batch_progress = 25 + (i / len(frame_batches)) * 50  # 25% to 75%
            await self._update_progress(2, "AI Analysis", batch_progress, 
                                       f"Processing batch {i+1}/{len(frame_batches)}...")
            
            print(f"   Processing batch {i+1}/{len(frame_batches)} ({len(batch)} frames)...")
            analysis = self.ai_analyzer._analyze_frame_batch(batch)
            if analysis:
                all_analyses.append(analysis)
            
            # Small delay to respect rate limits
            await asyncio.sleep(0.5)
        
        # Combine analyses into final result
        final_result = self.ai_analyzer._combine_analyses(all_analyses)
        print(f"✅ AI analysis complete. Found {len(final_result.get('pull_ups', []))} pull-up events")
        
        return final_result
    
    async def _generate_output_video_with_progress(self, analysis: Dict[str, Any]):
        """Generate output video with progress updates"""
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
        progress_update_interval = max(1, total_frames // 50)  # Update 50 times max
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                current_time = frame_count / fps
                
                # Add pose detection (optional - for real-time feedback)
                pose_data = self.pose_detector.detect_pull_up_landmarks(frame)
                if pose_data:
                    # Add pull-up phase indicator
                    frame = self.overlay_system.add_pull_up_indicator(frame, pose_data)
                
                # Add comprehensive overlays
                frame = self.overlay_system.add_pull_up_overlays(
                    frame, pull_up_events, current_time, processing_stats
                )
                
                out.write(frame)
                frame_count += 1
                
                # Progress updates
                if frame_count % progress_update_interval == 0 or frame_count >= total_frames:
                    progress = (frame_count / total_frames) * 100
                    video_progress = 75 + (progress * 0.2)  # 75% to 95%
                    await self._update_progress(3, "Video Generation", video_progress, 
                                               f"Processing frame {frame_count}/{total_frames}")
                    last_progress_update = frame_count
        
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