from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import asyncio
import logging
import os
from pathlib import Path

from .websocket_manager import WebSocketManager
from .progress_manager import ProgressManager
from .video_handler import VideoHandler
from modified_pullup import WebPullUpProcessor
from config import WEB_SERVER_HOST, WEB_SERVER_PORT, OPENROUTER_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="AI Pull-Up Counter",
    description="Intelligent pull-up analysis with real-time progress tracking",
    version="1.0.0"
)

# Global managers
websocket_manager = WebSocketManager()
progress_manager = ProgressManager(websocket_manager)
video_handler = VideoHandler()

# Processing state
is_processing = False
current_output_file = None

# Mount static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve main page"""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        return HTMLResponse("""
        <html>
            <head><title>AI Pull-Up Counter</title></head>
            <body>
                <h1>AI Pull-Up Counter</h1>
                <p>Static files not found. Please ensure the static directory exists.</p>
            </body>
        </html>
        """)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates"""
    await websocket_manager.connect(websocket)
    try:
        # Send current progress state immediately
        current_progress = progress_manager.get_progress()
        await websocket.send_text(str(current_progress))
        
        # Keep connection alive
        while True:
            # Wait for messages (though we don't expect any from client)
            message = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {message}")
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

@app.post("/upload")
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload video file and start processing"""
    global is_processing, current_output_file
    
    # Check if already processing
    if is_processing:
        raise HTTPException(status_code=409, detail="Another video is currently being processed")
    
    # Validate API key
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenRouter API key not configured")
    
    try:
        # Save uploaded file
        filename = await video_handler.save_uploaded_file(file)
        logger.info(f"Video uploaded: {filename}")
        
        # Start background processing
        background_tasks.add_task(process_video_task, filename)
        
        return {
            "message": "Upload successful, processing started",
            "filename": filename,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def process_video_task(input_filename: str):
    """Background task for video processing"""
    global is_processing, current_output_file
    
    is_processing = True
    current_output_file = None
    
    try:
        # Reset progress manager
        await progress_manager.start_processing()
        
        # Get file paths
        input_path = video_handler.get_input_file_path(input_filename)
        output_filename = video_handler.get_output_filename(input_filename)
        output_path = video_handler.get_output_file_path(output_filename)
        
        logger.info(f"Starting processing: {input_path} -> {output_path}")
        
        # Create processor with progress callback
        progress_callback = progress_manager.create_callback()
        processor = WebPullUpProcessor(input_path, output_path, progress_callback)
        
        # Process video
        result = await processor.process_video()
        
        if result['success']:
            current_output_file = output_filename
            await progress_manager.complete_processing(output_filename)
            logger.info(f"Processing completed successfully: {output_filename}")
        else:
            error_msg = result.get('error', 'Unknown processing error')
            await progress_manager.set_error(error_msg)
            logger.error(f"Processing failed: {error_msg}")
            
    except Exception as e:
        error_msg = f"Processing error: {str(e)}"
        logger.error(error_msg)
        await progress_manager.set_error(error_msg)
        
    finally:
        is_processing = False
        
        # Cleanup old files after processing
        try:
            video_handler.cleanup_old_files(max_age_hours=24)
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")

@app.get("/progress")
async def get_progress():
    """Get current processing progress"""
    progress = progress_manager.get_progress()
    return {
        **progress,
        "is_processing": is_processing,
        "output_file": current_output_file
    }

@app.get("/download/{filename}")
@app.head("/download/{filename}")
async def download_video(filename: str, request: Request):
    """Download processed video file"""
    try:
        # Validate filename (security check)
        if not filename.endswith('.mp4') or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        file_path = video_handler.get_output_file_path(filename)
        
        if not video_handler.file_exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # For HEAD requests, just return headers without content
        if request.method == "HEAD":
            from fastapi.responses import Response
            file_size = video_handler.get_file_size(file_path)
            headers = {
                "content-type": "video/mp4",
                "content-length": str(file_size) if file_size else "0"
            }
            return Response(headers=headers)
        
        # For GET requests, return the actual file
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='video/mp4'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail="Download failed")

@app.get("/result")
async def result_page():
    """Serve result page"""
    result_path = static_path / "result.html"
    if result_path.exists():
        return FileResponse(result_path)
    else:
        return HTMLResponse("""
        <html>
            <head><title>Processing Results</title></head>
            <body>
                <h1>Processing Results</h1>
                <p>Result page not found.</p>
                <a href="/">← Back to Upload</a>
            </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "is_processing": is_processing,
        "api_key_configured": bool(OPENROUTER_API_KEY)
    }

@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("🚀 AI Pull-Up Counter Web App starting...")
    logger.info(f"📂 Upload directory: {video_handler.upload_dir}")
    logger.info(f"📂 Output directory: {video_handler.output_dir}")
    logger.info(f"🔑 API key configured: {bool(OPENROUTER_API_KEY)}")
    
    # Cleanup old files on startup
    try:
        video_handler.cleanup_old_files(max_age_hours=24)
        logger.info("✅ Old files cleaned up")
    except Exception as e:
        logger.warning(f"Startup cleanup warning: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("🛑 AI Pull-Up Counter Web App shutting down...")
    
    # Final cleanup
    try:
        video_handler.cleanup_old_files(max_age_hours=0)
        logger.info("✅ Final cleanup completed")
    except Exception as e:
        logger.warning(f"Shutdown cleanup warning: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT, reload=True) 