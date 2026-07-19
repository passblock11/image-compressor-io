# Image Compression API

An extremely high-performance image compression and resizing API built with FastAPI and pyvips.

## Prerequisites

This API leverages `pyvips` for lightning-fast image resizing and compression. `pyvips` requires the system-level `libvips` C library to be installed on the host system.

### System-level Dependencies

- **Debian / Ubuntu**:
  ```bash
  sudo apt-get update
  sudo apt-get install -y libvips-dev
  ```

- **macOS (Homebrew)**:
  ```bash
  brew install vips
  ```

- **Windows**:
  Follow the instructions on the [libvips documentation](https://libvips.github.io/libvips/install.html) to install libvips and add its `bin` folder to your system `PATH`.

## Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   uvicorn app:app --reload
   ```

## Testing

Run tests with `pytest`:
```bash
pytest test_app.py
```
