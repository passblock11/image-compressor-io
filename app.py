from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    """
    Compresses an image using pyvips for high performance.
    Switched to a synchronous endpoint to allow FastAPI to manage the CPU-bound
    image processing in an external thread pool, preventing event loop blockage.
    """
    try:
        # File size validation without loading entire file into memory first
        file.file.seek(0, 2)
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

        image_bytes = file.file.read()

        # Use thumbnail_buffer for efficient resize-on-load
        # We set a very large height to only constrain by width
        img = pyvips.Image.thumbnail_buffer(
            image_bytes,
            MAX_WIDTH,
            height=10000000,
            size='down'
        )

        # Handle transparency by flattening onto a white background
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Compress image to progressive JPEG
        # subsampling_mode is not supported in some libvips versions, so we omit it
        # to ensure compatibility as verified in previous sessions.
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

        return Response(
            content=output_buffer,
            media_type="image/jpeg"
        )

    except HTTPException as e:
        # Re-raise HTTPExceptions to preserve status codes
        raise e

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
