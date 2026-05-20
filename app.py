from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips

app = FastAPI()

# 100 MB file size limit
MAX_FILE_SIZE = 100 * 1024 * 1024
# Standard max width for compressed images
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    """
    Optimized image compression endpoint using pyvips.
    Synchronous 'def' allows FastAPI to delegate CPU-bound work to an external thread pool,
    preventing the event loop from being blocked by image processing.
    """
    try:
        # Validate file size using the file pointer to avoid loading entire content into memory first.
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

        if size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Max allowed size is 100 MB"
            )

        if size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )

        image_bytes = file.file.read()

        # Use thumbnail_buffer for ultra-fast resizing during loading.
        # This is significantly faster than loading the full image and then resizing.
        # size='down' ensures we only downsize, never upscale.
        # A very large height effectively constrains the image by width while preserving aspect ratio.
        img = pyvips.Image.thumbnail_buffer(
            image_bytes,
            MAX_WIDTH,
            height=10000000,
            size='down'
        )

        # Handle alpha channels (RGBA/P) by flattening onto a white background.
        # JPEG doesn't support transparency, so this ensures consistent visual behavior with Pillow.
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Compress to JPEG with high-performance settings.
        # 'interlace=True' generates a progressive JPEG, matching the original implementation.
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            subsample_mode='on'
        )

        return Response(
            content=output_buffer,
            media_type="image/jpeg"
        )

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except HTTPException:
        # Re-raise known HTTP exceptions
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
