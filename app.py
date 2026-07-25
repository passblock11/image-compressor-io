import io

import pyvips
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response

app = FastAPI()

# Note: Both pyvips and system-level libvips-dev are pre-declared and pre-existing
# dependencies in requirements.txt and render.yaml.
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    # Check file size without reading the entire file into memory first
    file.file.seek(0, io.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    # File size validation
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large. Max allowed size is 100 MB"
        )

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file"
        )

    try:
        image_bytes = file.file.read()
        # pyvips lazy load of the image from buffer
        img = pyvips.Image.new_from_buffer(image_bytes, "")
    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    width = img.width

    MAX_WIDTH = 1600

    # Resize large images using shrink-on-load (pyvips.Image.thumbnail_buffer)
    # The height is configured to a very large number to restrict resizing purely by width,
    # preserving the original aspect ratio behavior for tall/wide images.
    if width > MAX_WIDTH:
        try:
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file or processing error"
            )

    # Convert image colorspace to sRGB to ensure consistent output formats
    if img.interpretation != "srgb":
        img = img.colourspace("srgb")

    # If the image has an alpha channel, flatten it onto a white background to prevent error when saving as JPEG
    # Note: img.hasalpha() returns 1 (True) or 0 (False) in pyvips. We fallback to img.bands in (2, 4) as backup.
    has_alpha = img.hasalpha() if hasattr(img, "hasalpha") else (img.bands in (2, 4))
    if has_alpha:
        img = img.flatten(background=[255, 255, 255])

    try:
        # Compress image with optimal JPEG settings
        # Q corresponds to quality, interlace=True corresponds to progressive=True
        # optimize_coding=True corresponds to optimize=True, strip=True removes metadata/profiles
        output_bytes = img.jpegsave_buffer(
            Q=80,
            interlace=True,
            optimize_coding=True,
            strip=True
        )
    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file or processing error"
        )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
