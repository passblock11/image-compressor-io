from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips
import io

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    """
    Compresses an image using pyvips.
    Uses a synchronous 'def' to allow FastAPI to run this CPU-bound task in a thread pool.
    """
    try:
        # Efficiently check file size using seek/tell
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

        # Load metadata to check width
        # This is fast as it doesn't decode the whole image yet
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        MAX_WIDTH = 1600

        if img.width > MAX_WIDTH:
            # Use 'shrink-on-load' for massive performance gain when resizing
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)

        # Flatten alpha channel (RGBA/P) to white background since JPEG doesn't support transparency
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Compress to JPEG buffer
        # interlace=True for progressive JPEG
        # strip=True removes metadata (EXIF/IPTC/etc)
        # optimize_coding=True for better compression
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

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except HTTPException:
        # Re-raise HTTPExceptions (like file too large)
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
