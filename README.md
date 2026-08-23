# Image Compressor Service

High-performance image compression API built with FastAPI and pyvips / libvips.

## Prerequisites & Requirements

This service uses `pyvips`, which requires system-level `libvips` libraries.

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update && sudo apt-get install -y libvips42t64 || sudo apt-get install -y libvips-dev
```

### macOS
```bash
brew install vips
```

## Setup & Running

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```
