# Desk Organizer

A web-based application that uses computer vision and Gen AI to help users organize their physical desk space efficiently.

## 🎯 Overview

This system guides users through organizing their desk by:

1. **Capture Desk**: Point camera at your messy desk and tap "Capture Desk"
2. **Mark Corners**: Tap the 4 corners of your workspace (Top-Left → Top-Right → Bottom-Right → Bottom-Left)
3. **Select Intent**: Choose your desk's purpose (work/art/leisure) or describe custom needs
4. **View Plan**: See the organization plan with colored arrows
5. **Organize**: Follow the arrows to move items
6. **Check Work**: Capture your organized desk and get a score with feedback

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

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up API Key

**Important**: You must provide your own Gemini API key to run this application.

Replace the placeholder in `app.py` (line 8) with your API key:
```python
client = genai.Client(api_key="YOUR_API_KEY_HERE")
```

To get a free Gemini API key:
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and paste it into `app.py`

## 📱 Running the Application

### 1. Start the Flask server
```bash
python app.py
```
The server will start on `http://0.0.0.0:5001`

### 2. Expose to mobile device using ngrok

First, create a free account at [ngrok.com](https://ngrok.com/)

Then in a new terminal window:
```bash
ngrok http 5001
```

You'll see output like:
```
Forwarding    https://your-unique-url.ngrok-free.app -> http://localhost:5001
```

Open the ngrok URL (`https://your-unique-url.ngrok-free.app`) on your phone's browser!

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

https://youtube.com/shorts/77CalDnkifo

## 📧 Contact

For questions or issues, please contact:
- Yilan Liu (liuyilan@umich.edu)

---

*This project was created as a starter task for the Human-AI Lab SURE program at the University of Michigan (Winter 2026).*

