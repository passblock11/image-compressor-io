# Image Compression Service

A high-performance image compression API built with FastAPI and pyvips (`libvips`).

## Local Development Requirements

This service uses `pyvips` for ultra-fast, low-memory image processing. `pyvips` requires the `libvips` C library installed on your system.

### Installing libvips

- **Debian / Ubuntu:** `sudo apt-get install -y libvips-dev` (or `libvips42t64`)
- **macOS:** `brew install vips`
- **Arch Linux:** `sudo pacman -S libvips`

### Running the Application

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the server:
   ```bash
   uvicorn app:app --reload
   ```

3. Run unit tests:
   ```bash
   pytest test_app.py
   ```
