import io

import pyvips
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    """
    Highly optimized image compression endpoint.
    - Implements a synchronous `def` endpoint to offload CPU-bound image operations
      to FastAPI's internal thread pool, keeping the main event loop unblocked.
    - Uses `pyvips` for extremely fast and memory-efficient image processing
      and 'shrink-on-load' thumbnailing.
    - Prevents unnecessary full-file reads and redundant memory allocation.
    """
    # Performance Optimization: Validate file size efficiently without reading
    # the entire payload into memory first. We seek to the end, read the cursor, and seek back.
    file.file.seek(0, io.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    # Validate file size constraints (before any try-except block to avoid swallowing HTTPExceptions)
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

    # Read the file bytes into memory
    image_bytes = file.file.read()

    try:
        # Performance Optimization: Use new_from_buffer to lazily check image metadata (width)
        # and only invoke the expensive shrink-on-load thumbnailing if resizing is actually needed.
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        MAX_WIDTH = 1600

        # Resize large images
        if img.width > MAX_WIDTH:
            # Performance Optimization: Use thumbnail_buffer for shrink-on-load optimization.
            # Only read the pixels required for the target size.
            # Using a very large height parameter ensures only width is constrained, preserving aspect ratio.
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Performance Parity: If the image has an alpha channel, flatten it onto a white background
        # to match Pillow's RGBA -> RGB behavior.
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Convert to sRGB to ensure consistent color representation before compression
        img = img.colourspace("srgb")

        # Performance Optimization: Save JPEG to buffer with optimal configuration:
        # - Q=80: matches Pillow quality=80
        # - interlace=True: generates a progressive JPEG, matching Pillow's progressive=True
        # - optimize_coding=True: achieves Huffman table optimization, matching Pillow's optimize=True
        # - strip=True: strips all EXIF/ICC metadata to reduce file size
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
