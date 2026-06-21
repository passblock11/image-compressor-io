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
    """
    Compresses an image using pyvips for high performance.
    Uses synchronous 'def' to allow FastAPI to delegate the CPU-bound work to a thread pool.
    """
    try:
        # Get file size without reading everything into memory yet
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

        image_bytes = file.file.read()

        MAX_WIDTH = 1600

        # Check image dimensions first to avoid upscaling
        try:
            # We use new_from_buffer first just to get metadata
            temp_img = pyvips.Image.new_from_buffer(image_bytes, "")
            if temp_img.width > MAX_WIDTH:
                # Use thumbnail_buffer for 'shrink-on-load' optimization
                # It only reads the pixels it needs to generate the requested size.
                img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)
            else:
                img = temp_img
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        # Convert to RGB if it has an alpha channel
        if img.hasalpha():
            # Flatten onto a white background
            img = img.flatten(background=[255, 255, 255])

        # Compress and save as JPEG
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
        )

        return Response(
            content=output_buffer,
            media_type="image/jpeg"
        )

    except HTTPException:
        # Re-raise HTTP exceptions so they aren't swallowed by the general Exception block
        raise

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
