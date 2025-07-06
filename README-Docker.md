# Docker Setup for AI Pull-Up Counter

This project uses Docker to ensure consistent Python 3.12 environment and MediaPipe compatibility across all systems.

## 🐳 Quick Start

1. **Copy and configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` file and add your OpenRouter API key:
   ```
   OPENROUTER_API_KEY=your_actual_api_key_here
   ```

2. **Build and run the application:**
   ```bash
   docker-compose up --build
   ```

3. **Place your video files in the `input_videos/` directory**

4. **Process videos interactively:**
   ```bash
   docker-compose exec pullup-counter python pullup.py
   ```

## 📁 Directory Structure

```
AI pull up counter/
├── input_videos/          # Place your input videos here
├── output_videos/         # Processed videos will be saved here
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile            # Docker image configuration
├── .env.example          # Environment variables template
└── .env                  # Your actual environment variables (create this)
```

## 🛠️ Docker Commands

### Build the Docker image:
```bash
docker-compose build
```

### Run the application:
```bash
docker-compose up
```

### Run in detached mode:
```bash
docker-compose up -d
```

### Access the container shell:
```bash
docker-compose exec pullup-counter bash
```

### Stop the application:
```bash
docker-compose down
```

### View logs:
```bash
docker-compose logs -f pullup-counter
```

## 🎯 Usage Examples

### Process a specific video:
```bash
# Copy your video to input_videos/
cp your_video.mp4 input_videos/

# Run the container interactively
docker-compose run --rm pullup-counter python pullup.py
```

### Custom processing:
```bash
# Access the container shell
docker-compose exec pullup-counter bash

# Inside the container, run your custom commands
python pullup.py --input input_videos/your_video.mp4 --output output_videos/analyzed_video.mp4
```

## 🖥️ GUI Support (Linux/macOS)

For GUI applications, the Docker setup includes X11 forwarding:

### On Linux:
```bash
# Allow X11 forwarding
xhost +local:docker

# Run with GUI support
docker-compose up
```

### On macOS:
```bash
# Install XQuartz first
brew install --cask xquartz

# Start XQuartz and allow connections
xhost +localhost

# Run the application
docker-compose up
```

### On Windows:
GUI applications may require additional setup with X11 server like VcXsrv or Xming.

## 🔧 Environment Configuration

### Required Variables:
- `OPENROUTER_API_KEY`: Your OpenRouter API key for AI analysis

### Optional Variables:
- `DISPLAY`: X11 display for GUI applications
- `FRAME_EXTRACTION_RATE`: Frame extraction rate (default: 3)
- `KEY_FRAME_INTERVAL`: Key frame interval in seconds (default: 0.5)
- `MAX_FRAMES_PER_REQUEST`: Max frames per API request (default: 8)
- `IMAGE_QUALITY`: JPEG quality for encoding (default: 85)

## 📊 Cost Monitoring

The application provides cost estimation for API usage:
- Frames analyzed and API calls are tracked
- Cost estimates are displayed before processing
- Detailed breakdown is saved in `pullup.json`

## 🚀 Performance Tips

1. **Use GPU acceleration** (if available):
   ```yaml
   # Add to docker-compose.yml under pullup-counter service
   runtime: nvidia
   environment:
     - NVIDIA_VISIBLE_DEVICES=all
   ```

2. **Optimize video processing**:
   - Adjust `KEY_FRAME_INTERVAL` for balance between accuracy and cost
   - Use `FRAME_EXTRACTION_RATE` to control processing speed
   - Monitor `MAX_FRAMES_PER_REQUEST` for API efficiency

3. **Resource allocation**:
   ```yaml
   # Add to docker-compose.yml under pullup-counter service
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 4G
       reservations:
         memory: 2G
   ```

## 🐛 Troubleshooting

### Common Issues:

1. **Permission errors with video files:**
   ```bash
   chmod 755 input_videos/
   chmod 644 input_videos/*.mp4
   ```

2. **API key not found:**
   - Ensure `.env` file exists and contains valid `OPENROUTER_API_KEY`
   - Check that `.env` file is in the same directory as `docker-compose.yml`

3. **Container fails to start:**
   ```bash
   # Check logs
   docker-compose logs pullup-counter
   
   # Rebuild without cache
   docker-compose build --no-cache
   ```

4. **GUI applications not working:**
   - Ensure X11 forwarding is enabled
   - Check `DISPLAY` environment variable
   - Try running `xhost +local:docker` on Linux

5. **MediaPipe compatibility issues:**
   - The Docker image uses Python 3.12 specifically for MediaPipe compatibility
   - Ensure you're using the provided Dockerfile without modifications

## 🔄 Development Mode

For development, you can mount the entire project directory:

```yaml
# In docker-compose.yml
volumes:
  - .:/app  # This line mounts your local code
```

This allows you to edit code locally and see changes immediately in the container.

## 🧹 Cleanup

To clean up Docker resources:

```bash
# Stop and remove containers
docker-compose down

# Remove images
docker-compose down --rmi all

# Remove volumes
docker-compose down --volumes

# Complete cleanup
docker system prune -a
``` 