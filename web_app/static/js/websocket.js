class ProgressWebSocket {
    constructor() {
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.isConnected = false;
        
        this.statusIndicator = document.getElementById('connectionStatus');
        this.statusDot = this.statusIndicator.querySelector('.status-dot');
        this.statusText = this.statusIndicator.querySelector('span');
        
        this.connect();
    }
    
    connect() {
        try {
            // Determine WebSocket URL
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            console.log('Connecting to WebSocket:', wsUrl);
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = this.onOpen.bind(this);
            this.websocket.onmessage = this.onMessage.bind(this);
            this.websocket.onclose = this.onClose.bind(this);
            this.websocket.onerror = this.onError.bind(this);
            
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.handleConnectionFailure();
        }
    }
    
    onOpen(event) {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        
        // Update status indicator
        this.updateConnectionStatus(true);
        
        // Request current progress
        this.requestProgress();
    }
    
    onMessage(event) {
        try {
            // Handle both JSON strings and plain strings
            let data;
            if (event.data.startsWith('{')) {
                data = JSON.parse(event.data);
            } else {
                console.log('Received plain message:', event.data);
                return;
            }
            
            console.log('Received progress update:', data);
            
            // Pass data to progress UI
            if (window.progressUI) {
                window.progressUI.updateProgress(data);
            }
            
            // Handle different message types
            switch (data.type) {
                case 'progress':
                    this.handleProgressUpdate(data);
                    break;
                case 'complete':
                    this.handleCompletion(data);
                    break;
                case 'error':
                    this.handleError(data);
                    break;
                default:
                    console.log('Unknown message type:', data.type);
            }
            
        } catch (error) {
            console.error('Error processing WebSocket message:', error);
        }
    }
    
    onClose(event) {
        console.log('WebSocket closed:', event.code, event.reason);
        this.isConnected = false;
        this.updateConnectionStatus(false);
        
        // Attempt to reconnect if it wasn't a clean close
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
        }
    }
    
    onError(event) {
        console.error('WebSocket error:', event);
        this.handleConnectionFailure();
    }
    
    handleConnectionFailure() {
        this.isConnected = false;
        this.updateConnectionStatus(false);
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
        } else {
            console.error('Max reconnection attempts reached');
            this.statusText.textContent = 'Connection failed';
        }
    }
    
    scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
        
        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.statusText.textContent = `Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`;
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    updateConnectionStatus(connected) {
        if (connected) {
            this.statusDot.classList.remove('disconnected');
            this.statusText.textContent = 'Connected';
        } else {
            this.statusDot.classList.add('disconnected');
            this.statusText.textContent = 'Disconnected';
        }
    }
    
    handleProgressUpdate(data) {
        // This is handled by progressUI.updateProgress() above
        // but we can add any additional logic here if needed
    }
    
    handleCompletion(data) {
        console.log('Processing completed:', data);
        
        // Switch to completion view
        setTimeout(() => {
            this.showCompletionSection(data.output_file);
        }, 1000);
    }
    
    handleError(data) {
        console.error('Processing error:', data);
        
        // Switch to error view
        setTimeout(() => {
            this.showErrorSection(data.message);
        }, 1000);
    }
    
    showCompletionSection(outputFile) {
        // Hide processing section
        document.getElementById('processingSection').style.display = 'none';
        
        // Show completion section
        const completionSection = document.getElementById('completionSection');
        completionSection.style.display = 'block';
        
        // Setup view results button
        const viewResultsBtn = document.getElementById('viewResultsBtn');
        if (viewResultsBtn && outputFile) {
            viewResultsBtn.onclick = () => {
                // Redirect to results page with the output file
                window.location.href = `/result?file=${encodeURIComponent(outputFile)}`;
            };
        }
    }
    
    showErrorSection(errorMessage) {
        // Hide processing section
        document.getElementById('processingSection').style.display = 'none';
        
        // Show error section
        const errorSection = document.getElementById('errorSection');
        const errorMessageEl = document.getElementById('errorMessage');
        
        errorMessageEl.textContent = errorMessage || 'An unknown error occurred during processing.';
        errorSection.style.display = 'block';
    }
    
    requestProgress() {
        // Fetch current progress via HTTP as backup
        fetch('/progress')
            .then(response => response.json())
            .then(data => {
                console.log('Current progress:', data);
                if (window.progressUI) {
                    window.progressUI.updateProgress(data);
                }
            })
            .catch(error => {
                console.error('Failed to fetch progress:', error);
            });
    }
    
    send(message) {
        if (this.isConnected && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(message));
        } else {
            console.warn('Cannot send message: WebSocket not connected');
        }
    }
    
    reconnect() {
        if (this.websocket) {
            this.websocket.close();
        }
        this.reconnectAttempts = 0;
        this.connect();
    }
    
    disconnect() {
        if (this.websocket) {
            this.websocket.close(1000, 'Client disconnecting');
        }
    }
}

// Initialize WebSocket when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.progressWebSocket = new ProgressWebSocket();
    console.log('WebSocket client initialized');
});

// Clean up WebSocket on page unload
window.addEventListener('beforeunload', () => {
    if (window.progressWebSocket) {
        window.progressWebSocket.disconnect();
    }
}); 