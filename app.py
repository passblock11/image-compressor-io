import io
import pyvips
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    try:
        # Seek to end to check size efficiently
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

        # Read uploaded file
        image_bytes = file.file.read()

    except HTTPException:
        # Re-raise HTTPExceptions (such as 413 or 400) directly
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    try:
        # Lazy metadata loading to check original image dimensions
        # Use pyvips.Image.new_from_buffer to avoid decoding the full image immediately
        img = pyvips.Image.new_from_buffer(image_bytes, "")
        width = img.width

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )

    MAX_WIDTH = 1600

    try:
        # Resize large images using high-performance thumbnail_buffer
        if width > MAX_WIDTH:
            # We use height=10000000 to constrain only the width while preserving aspect ratio
            # This also enables shrink-on-load optimization
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Flatten alpha channels (like RGBA, LA) onto a white background to match Pillow's conversion
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Convert to standard sRGB color space for consistent JPEG output
        img = img.colourspace("srgb")

        # Compress and save image to JPEG format
        output_bytes = img.jpegsave_buffer(
            Q=80,
            interlace=True,          # Matches progressive=True in Pillow
            optimize_coding=True,    # Matches optimize=True in Pillow
            strip=True               # Strip metadata for minimal file size
        )

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
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
