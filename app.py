from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips
import io

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    # File size validation (efficiently without reading into memory yet)
    file.file.seek(0, io.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

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

        # Check if resize is needed using lazy loading
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        if img.width > MAX_WIDTH:
            # Use 'shrink-on-load' via thumbnail_buffer for maximum performance.
            # Large height ensures only width is the constraint.
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Handle alpha channel by flattening onto a white background (matches Pillow behavior)
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Ensure consistent sRGB output
        img = img.colourspace("srgb")

        # Compress to JPEG
        # Q: Quality (80)
        # optimize_coding: Huffman table optimization (Pillow's optimize=True)
        # interlace: Progressive JPEG (Pillow's progressive=True)
        # strip: Remove metadata for smaller size
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
        )

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    return Response(
        content=output_buffer,
        media_type="image/jpeg"
    )
