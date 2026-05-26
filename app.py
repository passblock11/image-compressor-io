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
    Switching to a synchronous 'def' allows FastAPI to run this CPU-bound task
    in an external thread pool, avoiding event loop blockage.
    """
    try:
        # Validate file size without reading full content into memory
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, detail="File too large. Max allowed size is 100 MB"
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        image_bytes = file.file.read()

        # Use thumbnail_buffer for efficient loading and resizing in one step
        # This is significantly faster than loading the full image and then resizing
        img = pyvips.Image.thumbnail_buffer(
            image_bytes,
            MAX_WIDTH,
            height=10000000,  # Large height to effectively only constrain by width
            size=pyvips.Size.DOWN,
        )

        # Handle transparency: flatten onto a white background (consistent with Pillow RGB conversion)
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Save to JPEG buffer with optimization
        # Note: 'interlace=True' in pyvips corresponds to 'progressive=True' in Pillow
        output_buffer = img.jpegsave_buffer(Q=80, optimize_coding=True, interlace=True)

        return Response(content=output_buffer, media_type="image/jpeg")

    except pyvips.Error:
        raise HTTPException(status_code=400, detail="Invalid image file")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Upload failed")
