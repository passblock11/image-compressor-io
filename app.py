import io
import pyvips
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response

app = FastAPI()

# Max file size: 100 MB
MAX_FILE_SIZE = 100 * 1024 * 1024


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    """
    Compresses an uploaded image using pyvips.
    Synchronous 'def' is used so FastAPI runs this in a thread pool,
    avoiding event loop blockage during CPU-bound image processing.
    """
    try:
        # Validate file size using the underlying file object to avoid reading into memory
        file.file.seek(0, io.SEEK_END)
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

        # Read file content into memory for processing
        image_bytes = file.file.read()

        # Load image metadata lazily to check dimensions
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        MAX_WIDTH = 1600

        # High-performance resizing using 'shrink-on-load' if width exceeds MAX_WIDTH
        if img.width > MAX_WIDTH:
            # thumbnail_buffer is significantly faster as it only decodes required pixels
            # We set a very large height to only constrain by width
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Ensure consistent background for images with transparency (e.g. PNG)
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Compress to JPEG with optimized settings
        # Q=80: Quality level (matches Pillow's quality=80)
        # optimize_coding=True: Huffman table optimization (matches Pillow's optimize=True)
        # interlace=True: Progressive JPEG (matches Pillow's progressive=True)
        # strip=True: Remove metadata (EXIF, ICC profiles) to reduce file size
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
        )

        return Response(
            content=output_bytes,
            media_type="image/jpeg"
        )

    except pyvips.error.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except HTTPException:
        # Re-raise HTTPExceptions (like file too large or empty file)
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
