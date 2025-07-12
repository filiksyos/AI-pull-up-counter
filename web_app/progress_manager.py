import asyncio
from typing import Optional, Callable
import time
import logging

logger = logging.getLogger(__name__)

class ProgressManager:
    def __init__(self, websocket_manager=None):
        self.websocket_manager = websocket_manager
        self.current_progress = {
            "type": "progress",
            "step": 0,
            "step_name": "Waiting",
            "progress": 0,
            "message": "Ready to process video",
            "eta": None,
            "error": None
        }
        self.start_time = None
        self.step_start_time = None
        
        # Progress step definitions
        self.steps = {
            1: {"name": "Frame Extraction", "range": (0, 25)},
            2: {"name": "AI Analysis", "range": (25, 75)},
            3: {"name": "Video Generation", "range": (75, 95)},
            4: {"name": "Saving Results", "range": (95, 100)}
        }
    
    async def start_processing(self):
        """Initialize processing state"""
        self.start_time = time.time()
        self.step_start_time = time.time()
        await self.update_progress(0, "Initializing", 0, "Starting video processing...")
    
    async def update_progress(self, step: int, step_name: str, progress: float, message: str, eta: Optional[float] = None):
        """Update progress and broadcast to WebSocket clients"""
        
        # Update current progress
        self.current_progress.update({
            "type": "progress",
            "step": step,
            "step_name": step_name,
            "progress": min(100, max(0, progress)),
            "message": message,
            "eta": eta,
            "error": None
        })
        
        # Calculate ETA if not provided
        if eta is None and self.start_time and progress > 0:
            elapsed = time.time() - self.start_time
            total_estimated = elapsed / (progress / 100)
            eta = total_estimated - elapsed
            self.current_progress["eta"] = max(0, eta)
        
        # Log progress
        logger.info(f"Progress: Step {step} - {step_name} - {progress:.1f}% - {message}")
        
        # Broadcast to WebSocket clients
        if self.websocket_manager:
            await self.websocket_manager.broadcast_progress(self.current_progress)
    
    async def update_step_progress(self, step: int, step_progress: float, message: str):
        """Update progress within a specific step"""
        if step not in self.steps:
            return
        
        step_info = self.steps[step]
        step_name = step_info["name"]
        progress_range = step_info["range"]
        
        # Calculate overall progress
        overall_progress = progress_range[0] + (step_progress / 100) * (progress_range[1] - progress_range[0])
        
        await self.update_progress(step, step_name, overall_progress, message)
    
    async def complete_step(self, step: int, message: str = None):
        """Mark a step as complete"""
        if step not in self.steps:
            return
        
        step_info = self.steps[step]
        step_name = step_info["name"]
        progress = step_info["range"][1]
        
        if message is None:
            message = f"{step_name} completed"
        
        await self.update_progress(step, step_name, progress, message)
        self.step_start_time = time.time()
    
    async def set_error(self, error_message: str):
        """Set error state"""
        self.current_progress.update({
            "type": "error",
            "error": error_message,
            "message": f"Error: {error_message}"
        })
        
        logger.error(f"Processing error: {error_message}")
        
        if self.websocket_manager:
            await self.websocket_manager.broadcast_progress(self.current_progress)
    
    async def complete_processing(self, output_filename: str):
        """Mark processing as complete"""
        await self.update_progress(4, "Complete", 100, "Processing completed successfully!")
        
        if self.websocket_manager:
            await self.websocket_manager.send_completion(output_filename)
    
    def get_progress(self) -> dict:
        """Get current progress state"""
        return self.current_progress.copy()
    
    def create_callback(self):
        """Create a callback function for the PullUpProcessor"""
        async def progress_callback(step: int, step_name: str, progress: float, message: str, eta: Optional[float] = None):
            await self.update_progress(step, step_name, progress, message, eta)
        
        return progress_callback 