# ASCII Media Converter 🎬➡️📝

A powerful Flask web application that converts images and videos into ASCII art with real-time terminal playback support. Transform your media files into stunning text-based representations with customizable parameters.

<img width="1000" height=auto alt="Screenshot 2025-08-17 at 10 17 17 PM" src="https://github.com/user-attachments/assets/7c94905a-196a-4fee-bafc-6d1e0246f4f8" />

*The clean and intuitive web interface for uploading and converting media files*

## ✨ Features

- **Image to ASCII Conversion**: Convert PNG, JPG, JPEG, BMP, and GIF images to ASCII art
- **Video to ASCII Conversion**: Convert MP4, AVI, MOV, MKV, and WEBM videos to ASCII animations
- **Real-time Terminal Playback**: Watch ASCII videos play directly in your server terminal
- **Customizable Parameters**:
  - Adjustable character width (default: 120 characters)
  - Custom ASCII character sets (default: `@%#*+=-:. `)
  - Color support with 24-bit ANSI escape codes
  - Brightness inversion option
- **Web Interface**: Clean, responsive HTML interface for easy file uploads
- **REST API**: Programmatic access via JSON endpoints
- **Docker Support**: Easy deployment with Docker and Docker Compose

## 🖼️ Example Output

| Original Image | ASCII Art Output |
|:--------------:|:----------------:|
| <img width="300" height="auto" alt="Original C++ Logo" src="https://github.com/user-attachments/assets/5b4154dd-a5e9-43b8-870e-aa77743768f5" /> | <img width="300" height="auto" alt="ASCII Art Conversion" src="https://github.com/user-attachments/assets/ea8c6d02-06f3-43c6-8be3-3ee5ba70dfea" /> |
| *Original input image* | *The same image converted to ASCII art* |

## 📁 Project Structure

```
ASCII-Game/
├── app/
│   ├── __init__.py                 # Flask app factory
│   ├── config.py                   # Configuration settings
│   ├── blueprints/
│   │   ├── main.py                # Main web interface routes
│   │   └── api.py                 # REST API endpoints
│   ├── services/
│   │   ├── ascii_engine.py        # Core ASCII conversion logic
│   │   ├── terminal_player.py     # Terminal video player
│   │   └── video_utils.py         # Video utility functions
│   ├── utils/
│   │   └── file_utils.py          # File handling utilities
│   ├── templates/
│   │   ├── base.html             # Base HTML template
│   │   ├── index.html            # Main upload interface
│   │   └── success.html          # Success page template
│   └── static/                   # Static assets (CSS, JS)
├── instance/                     # Auto-created runtime directory
│   ├── uploads/                  # Uploaded files storage
│   └── outputs/                  # Generated ASCII files
├── run.py                       # Development server entry point
├── wsgi.py                      # Production WSGI entry point
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker container configuration
├── docker-compose.yml          # Docker Compose setup
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenCV dependencies (automatically handled in Docker)
- Modern web browser

### Method 1: Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ASCII-Game
   ```

2. **Start the application**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Open your browser and go to: `http://localhost:5050`
   - The server terminal will display ASCII video playback

4. **Stop the application**
   ```bash
   docker-compose down
   ```

### Method 2: Local Python Installation

1. **Clone and setup**
   ```bash
   git clone <your-repo-url>
   cd ASCII-Game
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the development server**
   ```bash
   python run.py
   ```

4. **Access the application**
   - Open your browser and go to: `http://localhost:5000`

## 🎮 Usage

### Web Interface

1. **Navigate to the main page** (`http://localhost:5050` for Docker or `http://localhost:5000` for local)

2. **Upload a file**:
   - Select an image or video file
   - Adjust conversion parameters:
     - **Width**: Number of characters per line (default: 120)
     - **Charset**: ASCII characters from dense to sparse (default: `@%#*+=-:. `)
     - **Invert**: Flip brightness values
     - **Color**: Enable 24-bit color output
     - **Terminal Playback**: Enable real-time terminal display (videos only)

3. **View results**:
   - Images: ASCII art saved to text file
   - Videos: Watch playback in server terminal + instruction file generated

### REST API

#### Convert Image
```bash
curl -X POST http://localhost:5050/api/upload/image \
  -F "file=@your_image.jpg" \
  -F "width=80" \
  -F "charset=@#*+-. " \
  -F "invert=false" \
  -F "color=true" \
  -F "terminal=true"
```

#### Convert Video
```bash
curl -X POST http://localhost:5050/api/upload/video \
  -F "file=@your_video.mp4" \
  -F "width=120" \
  -F "charset=@%#*+=-:. " \
  -F "terminal=true"
```

#### Stop Video Playback
```bash
curl -X POST http://localhost:5050/api/control/stop
```

## ⚙️ Configuration

Key configuration options in `app/config.py`:

```python
MAX_CONTENT_LENGTH = 512 * 1024 * 1024  # 512MB file size limit
DEFAULT_TARGET_WIDTH = 120               # Default ASCII width
DEFAULT_ASCII_CHARSET = "@%#*+=-:. "     # Default character set
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "gif"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm"}
```

## 🐳 Docker Configuration

### Dockerfile
- Based on Python 3.11 slim image
- Includes OpenCV system dependencies
- Exposes port 5000
- Optimized for production use

### Docker Compose
- Maps container port 5000 to host port 5050
- Volume mounts for development
- Environment variables for Flask development mode

## 🛠️ Development

### Adding New Features

1. **New conversion algorithms**: Extend `ascii_engine.py`
2. **Additional file formats**: Update allowed extensions in `config.py`
3. **New API endpoints**: Add routes to `blueprints/api.py`
4. **UI improvements**: Modify templates in `templates/`

### Running Tests

```bash
# Add your test commands here
python -m pytest tests/
```

## 🔧 Troubleshooting

### Common Issues

1. **"Failed to open video" error**
   - Ensure the video file format is supported
   - Check file isn't corrupted
   - Verify OpenCV installation

2. **Terminal playback not visible**
   - Check server console/logs where Flask is running
   - Ensure terminal supports ANSI escape codes

3. **Large file upload fails**
   - Increase `MAX_CONTENT_LENGTH` in configuration
   - Check available disk space

4. **Docker container won't start**
   - Ensure Docker and Docker Compose are installed
   - Check port 5050 isn't already in use
   - Run `docker-compose logs` for error details

### Performance Tips

- Use smaller target widths for faster processing
- Reduce video resolution before conversion for better performance
- Consider shorter character sets for simpler output

## 📝 License

[Add your license information here]

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## 📞 Support

- **Issues**: [GitHub Issues](your-repo-url/issues)
- **Discussions**: [GitHub Discussions](your-repo-url/discussions)
- **Email**: [your-email@domain.com]

---

**Made with ❤️ and lots of ASCII characters**
