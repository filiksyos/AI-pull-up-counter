from fastapi import WebSocket
from typing import List
import json
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast_progress(self, data: dict):
        """Send progress update to all connected clients"""
        if not self.active_connections:
            return
        
        message = json.dumps(data)
        disconnected_connections = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")
                disconnected_connections.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)
    
    async def send_error(self, error_message: str):
        """Send error message to all connected clients"""
        error_data = {
            "type": "error",
            "message": error_message,
            "step": 0,
            "progress": 0
        }
        await self.broadcast_progress(error_data)
    
    async def send_completion(self, output_filename: str):
        """Send completion message with output file"""
        completion_data = {
            "type": "complete",
            "message": "Processing completed successfully!",
            "step": 4,
            "progress": 100,
            "output_file": output_filename
        }
        await self.broadcast_progress(completion_data) 