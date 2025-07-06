import requests
import json
import time
from typing import List, Dict, Any, Optional
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MODEL_NAME, MAX_FRAMES_PER_REQUEST

class PullUpAIAnalyzer:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.base_url = OPENROUTER_BASE_URL
        self.model = MODEL_NAME
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://pullup-counter.com",  # Optional
            "X-Title": "AI Pull-Up Counter"                 # Optional
        }
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
    
    def analyze_pull_up_sequence(self, frame_data: List[Dict]) -> Dict[str, Any]:
        """Analyze sequence of frames for pull-up detection"""
        print(f"🤖 Starting AI analysis with {len(frame_data)} frames using {self.model}")
        
        # Split frames into batches for API requests
        frame_batches = self._split_frames_into_batches(frame_data)
        all_analyses = []
        
        for i, batch in enumerate(frame_batches):
            print(f"   Processing batch {i+1}/{len(frame_batches)} ({len(batch)} frames)...")
            analysis = self._analyze_frame_batch(batch)
            if analysis:
                all_analyses.append(analysis)
            
            # Small delay to respect rate limits
            time.sleep(0.5)
        
        # Combine analyses into final result
        final_result = self._combine_analyses(all_analyses)
        print(f"✅ AI analysis complete. Found {len(final_result.get('pull_ups', []))} pull-up events")
        
        return final_result
    
    def _split_frames_into_batches(self, frames: List[Dict]) -> List[List[Dict]]:
        """Split frames into batches for API processing"""
        batches = []
        for i in range(0, len(frames), MAX_FRAMES_PER_REQUEST):
            batch = frames[i:i + MAX_FRAMES_PER_REQUEST]
            batches.append(batch)
        return batches
    
    def _analyze_frame_batch(self, frame_batch: List[Dict]) -> Optional[Dict[str, Any]]:
        """Analyze a batch of frames via OpenRouter API"""
        
        # Prepare content array
        content = [
            {
                "type": "text",
                "text": self._create_pull_up_analysis_prompt(frame_batch)
            }
        ]
        
        # Add frames as base64 images
        for i, frame_data in enumerate(frame_batch):
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{frame_data['base64_data']}",
                    "detail": "high"
                }
            })
        
        # Make API request
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "max_tokens": 4000,
            "temperature": 0.1  # Low temperature for consistent analysis
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=120  # 2 minute timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'api_response': result,
                    'frames_analyzed': len(frame_batch),
                    'timestamp_range': f"{frame_batch[0]['timestamp']:.1f}s - {frame_batch[-1]['timestamp']:.1f}s"
                }
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("⏱️ API request timed out")
            return None
        except Exception as e:
            print(f"💥 Request failed: {e}")
            return None
    
    def _create_pull_up_analysis_prompt(self, frame_batch: List[Dict]) -> str:
        """Create detailed prompt for pull-up analysis"""
        
        timestamps = [f"{frame['timestamp']:.1f}s" for frame in frame_batch]
        timestamp_list = ", ".join(timestamps)
        
        return f"""
        Analyze these {len(frame_batch)} sequential frames from a pull-up workout video.
        
        Frame timestamps: {timestamp_list}
        
        Please analyze each frame for pull-up activity and provide a JSON response with the following structure:
        
        {{
            "pull_ups": [
                {{
                    "timestamp_start": "0:05.2",
                    "timestamp_peak": "0:06.1", 
                    "timestamp_end": "0:07.3",
                    "result": "completed",
                    "failure_reason": null,
                    "form_score": 85,
                    "total_completed_so_far": 1,
                    "total_failed_so_far": 0,
                    "feedback": "Good form - maintain straight body alignment"
                }}
            ],
            "overall_analysis": {{
                "body_alignment": "good",
                "range_of_motion": "full",
                "tempo": "controlled",
                "grip_stability": "stable"
            }}
        }}
        
        **Key criteria for pull-up analysis:**
        1. **Completed Pull-up**: Chin must clearly rise above the bar AND arms must fully extend at the bottom
        2. **Body Alignment**: Look for straight body position, minimal swinging or kipping
        3. **Range of Motion**: Full extension at bottom (arms straight) to chin over bar at top
        4. **Controlled Movement**: Smooth ascent and descent, not using momentum
        5. **Grip and Shoulder**: Proper shoulder engagement, stable grip position
        
        **Form scoring (0-100):**
        - 90-100: Perfect form with full range of motion
        - 80-89: Good form with minor issues
        - 70-79: Acceptable form with moderate issues
        - 60-69: Poor form with significant issues
        - Below 60: Very poor form or incomplete movement
        
        **Form feedback should be:**
        - Specific and actionable
        - Focused on the most important improvement
        - Encouraging but honest about form issues
        - Maximum 12 words per feedback message
        
        **Failure reasons:**
        - "chin_not_over_bar": Chin didn't clear the bar
        - "incomplete_extension": Arms didn't fully extend at bottom
        - "excessive_swinging": Too much body momentum/kipping
        - "partial_range": Incomplete range of motion
        
        If no pull-up motion is detected in these frames, return empty pull_ups array but still provide overall_analysis of the person's position and readiness.
        
        IMPORTANT: Return ONLY the JSON response, no additional text.
        """
    
    def _combine_analyses(self, analyses: List[Dict]) -> Dict[str, Any]:
        """Combine multiple API responses into final analysis"""
        combined_pull_ups = []
        total_frames = 0
        api_calls = len(analyses)
        
        for analysis in analyses:
            if analysis and 'api_response' in analysis:
                content = analysis['api_response']['choices'][0]['message']['content']
                total_frames += analysis['frames_analyzed']
                
                try:
                    # Clean up the content (remove any markdown formatting)
                    cleaned_content = content.strip()
                    if cleaned_content.startswith('```json'):
                        cleaned_content = cleaned_content[7:]
                    if cleaned_content.endswith('```'):
                        cleaned_content = cleaned_content[:-3]
                    
                    parsed_content = json.loads(cleaned_content)
                    if 'pull_ups' in parsed_content:
                        combined_pull_ups.extend(parsed_content['pull_ups'])
                        
                except json.JSONDecodeError as e:
                    print(f"⚠️ Failed to parse JSON from API response: {e}")
                    print(f"Raw content: {content[:200]}...")
                    continue
        
        # Calculate summary statistics
        completed_count = len([p for p in combined_pull_ups if p.get('result') == 'completed'])
        failed_count = len([p for p in combined_pull_ups if p.get('result') == 'failed'])
        
        # Calculate average form score
        form_scores = [p.get('form_score', 0) for p in combined_pull_ups if p.get('form_score')]
        avg_form_score = sum(form_scores) / len(form_scores) if form_scores else 0
        
        return {
            "pull_ups": combined_pull_ups,
            "summary": {
                "total_completed": completed_count,
                "total_failed": failed_count,
                "total_attempts": completed_count + failed_count,
                "success_rate": (completed_count / (completed_count + failed_count) * 100) if (completed_count + failed_count) > 0 else 0,
                "average_form_score": round(avg_form_score, 1)
            },
            "processing_stats": {
                "total_frames_analyzed": total_frames,
                "api_calls_made": api_calls,
                "model_used": self.model
            }
        }
    
    def estimate_cost(self, num_frames: int) -> float:
        """Estimate API cost based on number of frames"""
        # Gemini 2.5 Flash pricing: $0.619 per 1K input images
        cost_per_image = 0.000619
        return num_frames * cost_per_image 