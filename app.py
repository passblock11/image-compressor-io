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
    FastAPI executes synchronous 'def' endpoints in a thread pool,
    preventing CPU-bound tasks from blocking the event loop.
    """
    try:
        # Read uploaded file content
        image_bytes = file.file.read()

        # File size validation
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Empty file")

        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, detail="File too large. Max allowed size is 100 MB"
            )

        # Use pyvips.Image.thumbnail_buffer for ultra-fast resizing during loading.
        # This is significantly faster than loading the full image and then resizing.
        # We use a very large height to ensure we only constrain by width.
        # 'size="down"' ensures we never upscale images smaller than MAX_WIDTH.
        try:
            img = pyvips.Image.thumbnail_buffer(
                image_bytes, MAX_WIDTH, height=10000000, size="down"
            )
        except pyvips.Error as e:
            # Check for common "not a known format" errors
            err_msg = str(e)
            if "not a known format" in err_msg or "not in a known format" in err_msg:
                raise HTTPException(status_code=400, detail="Invalid image file")
            raise

        # Handle images with alpha channel (RGBA, LA, etc.) by flattening onto a white background.
        # JPEG does not support transparency.
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Compress to JPEG using jpegsave_buffer.
        # Q=80 matches the previous Pillow quality setting.
        # optimize_coding and interlace (progressive) are enabled for better compression.
        compressed_data = img.jpegsave_buffer(
            Q=80, optimize_coding=True, interlace=True
        )

        return Response(content=compressed_data, media_type="image/jpeg")

    except HTTPException:
        # Re-raise HTTP exceptions to maintain correct status codes
        raise
    except Exception as e:
        # Generic fallback for unexpected errors
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=400, detail="Upload failed")
