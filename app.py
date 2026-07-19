from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    # Read uploaded file synchronously
    try:
        image_bytes = file.file.read()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # File size validation
    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large. Max allowed size is 100 MB"
        )

    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file"
        )

    # Try loading image using pyvips.
    # Note that we use thumbnail_buffer to do shrink-on-load.
    # If width > 1600, it downsamples. Otherwise, size='down' keeps original dimensions.
    try:
        # 10000000 height ensures only target width of 1600 constrains resizing (preserving aspect ratio)
        img = pyvips.Image.thumbnail_buffer(
            image_bytes,
            1600,
            height=10000000,
            size='down'
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

    # Convert images with transparency/alpha channels to a white background (flatten)
    if img.hasalpha():
        img = img.flatten(background=[255, 255, 255])

    # Convert to standard color space
    img = img.colourspace("srgb")

    # Compress and save image to JPEG buffer
    try:
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
