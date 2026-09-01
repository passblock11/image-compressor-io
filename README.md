# Image Compression API

FastAPI web service for image compression and resizing.

## Requirements & Local Setup

### System Dependencies
This service uses `pyvips` for high-performance image processing, which requires `libvips` C libraries installed on the host system:

- **Ubuntu / Debian**: `sudo apt-get update && sudo apt-get install -y libvips-dev`
- **macOS**: `brew install vips`

### Python Setup & Testing

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   uvicorn app:app --reload
   ```

3. Run unit tests:
   ```bash
   python3 -m pytest test_app.py
   ```
