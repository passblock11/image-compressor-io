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
    """
    Compresses an uploaded image using pyvips.
    Synchronous endpoint allows FastAPI to run this CPU-bound task in a thread pool.
    """
    try:
        # Efficient file size validation without reading entire content into memory first
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

        # Use new_from_buffer first to check dimensions lazily
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        MAX_WIDTH = 1600

        # Use shrink-on-load via thumbnail_buffer if resizing is needed
        if img.width > MAX_WIDTH:
            # We set a very large height to ensure width is the only constraint,
            # preserving the aspect ratio.
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Handle alpha channel by flattening onto a white background
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Ensure consistent sRGB color space
        if img.interpretation != "srgb":
            img = img.colourspace("srgb")

        # Compress to JPEG with optimized settings
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
        )

    except HTTPException:
        # Re-raise FastAPIs HTTPExceptions (e.g. 413, 400 Empty file)
        raise
    except pyvips.Error:
        # pyvips raises Error for invalid image formats
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except Exception:
        # Catch-all for other unexpected errors during upload or processing
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
