# AI Pull-Up Counter

https://github.com/user-attachments/assets/1fa76ea3-129b-4c63-9b99-5784d0b8d38f

An intelligent pull-up counter that uses computer vision and AI to analyze your pull-up form and count repetitions automatically.

## Features

🏋️ **Automated Pull-Up Counting**: Uses AI to detect and count completed pull-ups  
📊 **Form Analysis**: Provides detailed feedback on your pull-up technique  
🎯 **Success Rate Tracking**: Monitors completed vs failed attempts  
📏 **Form Scoring**: Rates your form on a scale of 0-100  
🎥 **Video Overlay**: Generates annotated video with real-time statistics  
💰 **Cost Efficient**: Uses Gemini 2.5 Flash for affordable AI analysis  

## Requirements

- Python 3.8+
- OpenRouter API account
- MP4 video file of pull-up workout

## Installation

1. **Clone or download this project**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up API key**:
   - Copy `.env.template` to `.env`
   - Add your OpenRouter API key:
```bash
cp .env.template .env
# Edit .env and add your OPENROUTER_API_KEY
```

4. **Get OpenRouter API Key**:
   - Sign up at [OpenRouter.ai](https://openrouter.ai)
   - Create an API key in your dashboard
   - Add credit to your account (estimated cost: $0.005-0.02 per video)

## Usage

1. **Prepare your video**:
   - Place your pull-up video as `input_video.mp4` in the project directory
   - Ensure good lighting and clear view of the pull-up motion
   - Video should show full body during pull-ups

2. **Run the analysis**:
```bash
python pullup.py
```

3. **View results**:
   - `output_video.mp4`: Annotated video with overlays
   - `pullup.json`: Detailed analysis results

## Output Information

### Video Overlays
- **Pull-up count**: Completed and failed attempts
- **Form score**: Real-time form rating (0-100)
- **Progress bar**: Workout progression
- **Feedback text**: AI-generated form tips
- **Phase indicator**: Current pull-up phase (hanging, ascending, etc.)
- **Processing info**: AI model and analysis details

### JSON Analysis
```json
{
  "summary": {
    "total_completed": 8,
    "total_failed": 2,
    "success_rate": 80.0,
    "average_form_score": 85.5
  },
  "pull_ups": [
    {
      "timestamp_start": "0:05.2",
      "timestamp_end": "0:07.3",
      "result": "completed",
      "form_score": 85,
      "feedback": "Good form - maintain straight body alignment"
    }
  ]
}
```

## Configuration

Edit `config.py` to customize:

- **Frame extraction rate**: How often to analyze frames
- **AI model**: Switch between Gemini models
- **Detection thresholds**: Pull-up validation criteria
- **Cost optimization**: Frames per API request

## Cost Estimation

Using Gemini 2.5 Flash Preview:
- **Price**: $0.619 per 1,000 input images
- **Typical cost**: $0.005-0.02 per video (depending on length)
- **30-second video**: ~$0.01
- **2-minute video**: ~$0.05

## Troubleshooting

### Common Issues

**"OPENROUTER_API_KEY not found"**
- Ensure `.env` file exists with your API key
- Check that the key is valid and has credits

**"Input video not found"**
- Place your video as `input_video.mp4`
- Ensure the file is a valid MP4 format

**"Failed to extract frames"**
- Check video file isn't corrupted
- Try converting to standard MP4 format

**Poor detection accuracy**
- Ensure good lighting in video
- Make sure full body is visible
- Avoid excessive camera movement

### Video Requirements

✅ **Good videos**:
- Clear view of full body
- Good lighting
- Stable camera position
- Person clearly visible against background

❌ **Problematic videos**:
- Poor lighting or shadows
- Partial body view
- Excessive camera shake
- Person blends with background

## Technical Details

### Architecture
- **Frame Extraction**: OpenCV for video processing
- **Pose Detection**: MediaPipe for body landmark detection
- **AI Analysis**: OpenRouter + Gemini for intelligent analysis
- **Visualization**: Custom overlay system

### AI Model
- **Primary**: `google/gemini-2.5-flash-preview`
- **Alternative**: `google/gemini-2.5-pro` (higher accuracy, more expensive)
- **Analysis**: Multi-frame sequence analysis for accurate counting

### Processing Pipeline
1. Extract key frames from video (every 0.5s)
2. Send frame batches to Gemini AI for analysis
3. Process AI responses and extract pull-up events
4. Generate annotated video with overlays
5. Save detailed analysis results

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Ensure your video meets the requirements
3. Verify your OpenRouter API key and credits

## License

This project is open source and available under the MIT License. 
