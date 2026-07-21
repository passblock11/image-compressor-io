from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import io
import pyvips

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    try:
        # File size validation without loading into memory first
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

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
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    try:
        # Use new_from_buffer to lazily inspect image metadata
        img = pyvips.Image.new_from_buffer(image_bytes, "")
    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file or processing error"
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    width = img.width
    MAX_WIDTH = 1600

    # Resize large images
    if width > MAX_WIDTH:
        try:
            # Configure with very large height to only constrain width, preserving aspect ratio.
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file or processing error"
            )
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Upload failed"
            )

    # Convert and flatten alpha channels if present
    if img.hasalpha():
        img = img.flatten(background=[255, 255, 255])

    # Ensure consistent RGB output colorspace (sRGB)
    img = img.colourspace("srgb")

    try:
        # Compress image using jpegsave_buffer
        compressed_bytes = img.jpegsave_buffer(
            Q=80,
            strip=True,
            optimize_coding=True,
            interlace=True
        )
    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file or processing error"
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    return Response(
        content=compressed_bytes,
        media_type="image/jpeg"
    )
