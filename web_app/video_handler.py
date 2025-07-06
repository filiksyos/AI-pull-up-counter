import os
import time
import aiofiles
from fastapi import UploadFile, HTTPException
from typing import Optional
import logging
from pathlib import Path
from config import UPLOAD_DIR, OUTPUT_DIR, MAX_FILE_SIZE

logger = logging.getLogger(__name__)

class VideoHandler:
    def __init__(self):
        self.upload_dir = Path(UPLOAD_DIR)
        self.output_dir = Path(OUTPUT_DIR)
        self.max_file_size = MAX_FILE_SIZE
        
        # Supported video formats
        self.supported_formats = {'.mp4', '.avi', '.mov', '.mkv'}
        
        # Ensure directories exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self.supported_formats:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format. Supported formats: {', '.join(self.supported_formats)}"
            )
        
        # Check file size (if provided)
        if hasattr(file, 'size') and file.size and file.size > self.max_file_size:
            max_size_mb = self.max_file_size / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {max_size_mb:.0f}MB"
            )
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename with timestamp"""
        timestamp = str(int(time.time()))
        file_extension = Path(original_filename).suffix.lower()
        safe_name = Path(original_filename).stem[:50]  # Limit length
        
        # Remove any unsafe characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        safe_name = ''.join(c for c in safe_name if c in safe_chars)
        
        return f"{timestamp}_{safe_name}{file_extension}"
    
    async def save_uploaded_file(self, file: UploadFile) -> str:
        """Save uploaded file and return filename"""
        try:
            # Validate file
            self.validate_file(file)
            
            # Generate unique filename
            filename = self.generate_unique_filename(file.filename)
            file_path = self.upload_dir / filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                
                # Check actual file size
                if len(content) > self.max_file_size:
                    max_size_mb = self.max_file_size / (1024 * 1024)
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too large. Maximum size: {max_size_mb:.0f}MB"
                    )
                
                await f.write(content)
            
            logger.info(f"File uploaded successfully: {filename}")
            return filename
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}")
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")
    
    def get_input_file_path(self, filename: str) -> str:
        """Get full path for input file"""
        return str(self.upload_dir / filename)
    
    def get_output_filename(self, input_filename: str) -> str:
        """Generate output filename based on input filename"""
        timestamp = str(int(time.time()))
        input_name = Path(input_filename).stem
        
        # Clean up input name to avoid double timestamps
        # Remove existing timestamp pattern if present
        import re
        cleaned_name = re.sub(r'^\d{10}_', '', input_name)
        cleaned_name = cleaned_name.replace('_processed', '')
        
        # Limit length and ensure safe characters
        cleaned_name = cleaned_name[:30]  # Limit to 30 chars
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        cleaned_name = ''.join(c for c in cleaned_name if c in safe_chars)
        
        return f"{timestamp}_{cleaned_name}_processed.mp4"
    
    def get_output_file_path(self, output_filename: str) -> str:
        """Get full path for output file"""
        return str(self.output_dir / output_filename)
    
    def file_exists(self, filepath: str) -> bool:
        """Check if file exists"""
        return Path(filepath).exists()
    
    def get_file_size(self, filepath: str) -> Optional[int]:
        """Get file size in bytes"""
        try:
            return Path(filepath).stat().st_size
        except:
            return None
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> None:
        """Remove old files to manage storage"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        # Cleanup input files
        for file_path in self.upload_dir.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        logger.info(f"Cleaned up old input file: {file_path.name}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup file {file_path}: {e}")
        
        # Cleanup output files
        for file_path in self.output_dir.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        logger.info(f"Cleaned up old output file: {file_path.name}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup file {file_path}: {e}")
    
    async def delete_file(self, filepath: str) -> bool:
        """Delete a specific file"""
        try:
            file_path = Path(filepath)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {filepath}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {filepath}: {e}")
            return False 