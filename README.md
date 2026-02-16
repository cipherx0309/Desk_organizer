# Desk Organizer - AI-Powered Workspace Organization System

A web-based application that uses computer vision and AI to help users organize their physical desk space efficiently.

## 🎯 Project Overview

This system guides users through organizing their desk by:
1. Capturing an image of the messy desk
2. Allowing users to define the workspace area
3. Detecting objects using Gemini 2.0 Flash vision API
4. Generating an organization plan based on user intent (work/art/leisure)
5. Providing visual guidance with colored arrows showing where to move items
6. Evaluating the organized desk against the plan

## 🏗️ System Architecture

### Frontend
- **Technology**: HTML5 + JavaScript + TailwindCSS
- **Features**: 
  - Responsive camera interface
  - Interactive corner selection for workspace definition
  - Intent selection (work/art/leisure/custom)
  - Visual plan display with arrows
  - Real-time verification and scoring

### Backend
- **Technology**: Python Flask + OpenCV
- **AI Integration**: Google Gemini 2.0 Flash API
- **Key Functions**:
  - Perspective transformation (homography)
  - Object detection and center localization
  - Zone-based classification
  - Before/after comparison and scoring

## 📋 Prerequisites

- Python 3.8+
- Webcam or mobile device camera
- Google Gemini API key

## 🚀 Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/desk-organizer.git
cd desk-organizer
```

### 2. Install Python dependencies
```bash
pip install flask opencv-python numpy google-genai
```

### 3. Set up API Key
Replace the API key in `app.py` line 8 with your own Gemini API key:
```python
client = genai.Client(api_key="YOUR_API_KEY_HERE")
```

To get a free Gemini API key:
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"

## 📱 Running the Application

### 1. Start the Flask server
```bash
python app.py
```

The server will start on `http://0.0.0.0:5001`

### 2. Access the application

**On the same device:**
- Open browser and go to `http://localhost:5001`

**From a mobile device on the same network:**
1. Find your computer's IP address:
   - **Mac/Linux**: Run `ifconfig` or `ip addr`
   - **Windows**: Run `ipconfig`
2. On your mobile browser, go to `http://YOUR_IP_ADDRESS:5001`
   - Example: `http://192.168.1.100:5001`

### 3. Use the application

1. **Capture Desk**: Point camera at your messy desk and tap "Capture Desk"
2. **Mark Corners**: Tap the 4 corners of your workspace (Top-Left → Top-Right → Bottom-Right → Bottom-Left)
3. **Select Intent**: Choose your desk's purpose (work/art/leisure) or describe custom needs
4. **View Plan**: See the organization plan with colored arrows
5. **Organize**: Follow the arrows to move items
6. **Check Work**: Capture your organized desk and get a score with feedback

## 🎨 Organization Zones

The system divides your desk into three zones:

- **Main Work Area** (Yellow arrows): Bottom-right 70% × 70% - for primary work items
- **Support Area** (Orange arrows): Top 30% horizontal strip - for frequently-used small items
- **Edge Area** (Pink arrows): Left 30% vertical strip - for secondary items

## 📁 Project Structure

```
desk-organizer/
├── app.py                 # Flask backend server
├── index.html            # Frontend interface
├── README.md             # This file
├── requirements.txt      # Python dependencies
└── demo/                 # Demo video and screenshots
```

## 🔧 Configuration

### Zone Layout Customization
Edit the `get_zone_bounds()` function in `app.py` to adjust zone sizes:

```python
def get_zone_bounds(w, h):
    return {
        "Main Work Area": {"x": int(w*0.30), "y": int(h*0.30), "w": int(w*0.70), "h": int(h*0.70)},
        "Support Area": {"x": 0, "y": 0, "w": w, "h": int(h*0.30)},
        "Edge Area": {"x": 0, "y": int(h*0.30), "w": int(w*0.30), "h": int(h*0.70)}
    }
```

### Intent-Based Rules
Customize classification rules in `build_classify_prompt()` function in `app.py`.

## 🛠️ Troubleshooting

### Camera not working
- Ensure browser has camera permissions
- Try using `http://` instead of `https://` for local testing
- On mobile, make sure you're not blocking camera access

### Cannot connect from mobile device
- Ensure both devices are on the same WiFi network
- Check firewall settings aren't blocking port 5001
- Try disabling VPN if active

### API errors
- Verify your Gemini API key is valid
- Check API quota limits at [Google AI Studio](https://aistudio.google.com/)
- Ensure you have internet connection

### Objects not detected correctly
- Ensure good lighting conditions
- Make sure workspace corners are clearly visible
- Try recapturing if initial detection fails

## 🎥 Demo Video

[Link to demo video will be added here]

## 📊 Technical Highlights

- **Perspective Transformation**: Uses homography to create top-down desk view
- **Coordinate System Accuracy**: Custom prompt engineering for pixel-perfect object localization
- **Derisking Strategy**: Manual corner selection instead of automatic detection for reliability
- **Flexible Classification**: AI-powered zone assignment based on user intent
- **Real-time Feedback**: Before/after comparison with scoring system

## 🔮 Future Enhancements

- Real-time AR tracking during organization process
- Hand detection via MediaPipe
- 3D model for interactive layout customization
- Support for irregular desk shapes
- Offline object detection using local models

## 📝 License

This project was created as a starter task for the Human-AI Lab SURE program at the University of Michigan.

## 👥 Contact

For questions or issues, please contact:
- Yuxuan Liu (liurick@umich.edu)
- Chen Liang (clumich@umich.edu)

## 🙏 Acknowledgments

- Google Gemini 2.0 Flash for vision capabilities
- TailwindCSS for UI styling
- OpenCV for computer vision processing
- Human-AI Lab at University of Michigan for project guidance
