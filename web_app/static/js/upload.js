class VideoUploader {
    constructor() {
        this.uploadZone = document.getElementById('uploadZone');
        this.fileInput = document.getElementById('fileInput');
        this.uploadSection = document.getElementById('uploadSection');
        this.uploadStatus = document.getElementById('uploadStatus');
        this.statusMessage = document.getElementById('statusMessage');
        this.uploadProgress = document.getElementById('uploadProgress');
        this.uploadProgressText = document.getElementById('uploadProgressText');
        
        this.maxFileSize = 500 * 1024 * 1024; // 500MB
        this.supportedFormats = ['video/mp4', 'video/avi', 'video/mov', 'video/quicktime', 'video/x-msvideo'];
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Click to upload
        this.uploadZone.addEventListener('click', () => {
            if (!this.uploadZone.classList.contains('processing')) {
                this.fileInput.click();
            }
        });
        
        // File input change
        this.fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleFile(file);
            }
        });
        
        // Drag and drop events
        this.uploadZone.addEventListener('dragenter', this.handleDragEnter.bind(this));
        this.uploadZone.addEventListener('dragover', this.handleDragOver.bind(this));
        this.uploadZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.uploadZone.addEventListener('drop', this.handleDrop.bind(this));
        
        // Prevent default drag behaviors on document
        document.addEventListener('dragenter', (e) => e.preventDefault());
        document.addEventListener('dragover', (e) => e.preventDefault());
        document.addEventListener('dragleave', (e) => e.preventDefault());
        document.addEventListener('drop', (e) => e.preventDefault());
    }
    
    handleDragEnter(e) {
        e.preventDefault();
        this.uploadZone.classList.add('drag-over');
    }
    
    handleDragOver(e) {
        e.preventDefault();
        this.uploadZone.classList.add('drag-over');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        // Only remove drag-over if we're leaving the upload zone entirely
        if (!this.uploadZone.contains(e.relatedTarget)) {
            this.uploadZone.classList.remove('drag-over');
        }
    }
    
    handleDrop(e) {
        e.preventDefault();
        this.uploadZone.classList.remove('drag-over');
        
        if (this.uploadZone.classList.contains('processing')) {
            return;
        }
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.handleFile(files[0]);
        }
    }
    
    validateFile(file) {
        const errors = [];
        
        // Check file type
        if (!this.supportedFormats.includes(file.type)) {
            errors.push('Unsupported file format. Please use MP4, AVI, or MOV files.');
        }
        
        // Check file size
        if (file.size > this.maxFileSize) {
            const maxSizeMB = Math.round(this.maxFileSize / (1024 * 1024));
            errors.push(`File too large. Maximum size is ${maxSizeMB}MB.`);
        }
        
        // Check minimum size (at least 1MB to ensure it's a real video)
        if (file.size < 1024 * 1024) {
            errors.push('File too small. Please ensure you\'re uploading a valid video file.');
        }
        
        return errors;
    }
    
    async handleFile(file) {
        console.log('Handling file:', file.name, 'Size:', file.size, 'Type:', file.type);
        
        // Validate file
        const validationErrors = this.validateFile(file);
        if (validationErrors.length > 0) {
            this.showError(validationErrors.join(' '));
            return;
        }
        
        // Show upload status
        this.showUploadStatus(`Uploading ${file.name}...`);
        
        try {
            await this.uploadFile(file);
        } catch (error) {
            console.error('Upload error:', error);
            this.showError(`Upload failed: ${error.message}`);
        }
    }
    
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Upload failed (${response.status})`);
            }
            
            const result = await response.json();
            console.log('Upload successful:', result);
            
            // Update upload progress to 100%
            this.updateUploadProgress(100);
            this.statusMessage.textContent = 'Upload complete! Starting processing...';
            
            // Switch to processing view after a short delay
            setTimeout(() => {
                this.switchToProcessing();
            }, 1000);
            
        } catch (error) {
            console.error('Upload request failed:', error);
            throw error;
        }
    }
    
    showUploadStatus(message) {
        this.statusMessage.textContent = message;
        this.uploadStatus.style.display = 'block';
        this.updateUploadProgress(0);
        
        // Add processing class to upload zone
        this.uploadZone.classList.add('processing');
        
        // Simulate upload progress (since we don't have real progress from the upload)
        this.simulateUploadProgress();
    }
    
    simulateUploadProgress() {
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15 + 5; // Random increment between 5-20%
            if (progress >= 95) {
                progress = 95; // Stop at 95% until actual upload completes
                clearInterval(interval);
            }
            this.updateUploadProgress(progress);
        }, 200);
    }
    
    updateUploadProgress(percent) {
        const clampedPercent = Math.min(100, Math.max(0, percent));
        this.uploadProgress.style.width = `${clampedPercent}%`;
        this.uploadProgressText.textContent = `${Math.round(clampedPercent)}%`;
    }
    
    switchToProcessing() {
        // Hide upload section
        this.uploadSection.style.display = 'none';
        
        // Show processing section
        const processingSection = document.getElementById('processingSection');
        processingSection.style.display = 'block';
        
        // Initialize progress tracking
        if (window.progressUI) {
            window.progressUI.reset();
        }
    }
    
    showError(message) {
        // Reset upload zone
        this.uploadZone.classList.remove('processing', 'drag-over');
        
        // Hide upload status
        this.uploadStatus.style.display = 'none';
        
        // Show error in upload zone
        const uploadContent = this.uploadZone.querySelector('.upload-content');
        const originalContent = uploadContent.innerHTML;
        
        uploadContent.innerHTML = `
            <div class="upload-icon">❌</div>
            <h2>Upload Error</h2>
            <p style="color: #dc3545; margin-bottom: 20px;">${message}</p>
            <button class="retry-button" onclick="this.closest('.upload-zone').querySelector('.upload-content').innerHTML = \`${originalContent.replace(/`/g, '\\`')}\`">Try Again</button>
        `;
        
        // Reset after 5 seconds
        setTimeout(() => {
            if (uploadContent.innerHTML.includes('Upload Error')) {
                uploadContent.innerHTML = originalContent;
            }
        }, 5000);
    }
    
    reset() {
        // Reset upload zone
        this.uploadZone.classList.remove('processing', 'drag-over');
        
        // Hide upload status
        this.uploadStatus.style.display = 'none';
        
        // Reset file input
        this.fileInput.value = '';
        
        // Show upload section
        this.uploadSection.style.display = 'block';
        
        // Hide other sections
        document.getElementById('processingSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
        document.getElementById('completionSection').style.display = 'none';
    }
}

// Global function to reset to upload state
function resetToUpload() {
    if (window.videoUploader) {
        window.videoUploader.reset();
    }
    
    // Reset WebSocket connection
    if (window.progressWebSocket) {
        window.progressWebSocket.reconnect();
    }
}

// Initialize uploader when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.videoUploader = new VideoUploader();
    console.log('Video uploader initialized');
}); 