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
    Compress an image using pyvips for better performance.
    The endpoint is synchronous to allow FastAPI to run it in a separate thread,
    preventing the event loop from being blocked by CPU-bound image processing.
    """
    try:
        # Read uploaded file
        # We use file.file.read() to read synchronously from the SpooledTemporaryFile
        image_bytes = file.file.read()

        # File size validation
        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, detail="File too large. Max allowed size is 100 MB"
            )

        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        # Load image metadata lazily to check dimensions
        try:
            # new_from_buffer only reads the header by default
            img = pyvips.Image.new_from_buffer(image_bytes, "")
        except pyvips.error.Error:
            raise HTTPException(status_code=400, detail="Invalid image file")

        MAX_WIDTH = 1600

        # Resize large images using shrink-on-load if possible
        # pyvips.Image.thumbnail_buffer is very efficient for this as it only
        # decodes the pixels needed for the output size.
        if img.width > MAX_WIDTH:
            img = pyvips.Image.thumbnail_buffer(
                image_bytes,
                MAX_WIDTH,
                height=1000000,  # Large height to maintain aspect ratio based on width
            )

        # Handle transparency/alpha channel by flattening onto a white background.
        # This is done AFTER potential resizing to ensure it's applied to the final image.
        # This matches Pillow's conversion to RGB for JPEG.
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Compress image to JPEG buffer
        # strip=True removes metadata (EXIF, ICC profiles, etc.)
        # interlace=True creates a progressive JPEG
        output_buffer = img.jpegsave_buffer(Q=80, strip=True, interlace=True)

        return Response(content=output_buffer, media_type="image/jpeg")

    except HTTPException:
        raise
    except Exception:
        # Log error if needed: print(f"Error during compression: {e}")
        raise HTTPException(status_code=400, detail="Upload failed")
