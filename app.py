from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips
import io

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
    Uses 'shrink-on-load' optimization via thumbnail_buffer.
    """
    try:
        # Fast file size validation without reading entire file into memory first
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

        image_bytes = file.file.read()

        # pyvips.Image.new_from_buffer is lazy and very fast for metadata access
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        # Use thumbnail_buffer for efficient resizing if width exceeds MAX_WIDTH.
        # This performs "shrink-on-load", significantly reducing memory and CPU usage.
        if img.width > MAX_WIDTH:
            # We set a very large height to ensure the width is the only constraint,
            # maintaining the original aspect ratio.
            img = pyvips.Image.thumbnail_buffer(
                image_bytes,
                MAX_WIDTH,
                height=10000000
            )

        # Handle transparency by flattening onto a white background (JPEG doesn't support alpha)
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Ensure consistent color space (sRGB)
        if img.interpretation != 'srgb':
            img = img.colourspace("srgb")

        # Compress to JPEG with optimized settings
        # Q: Quality (80)
        # optimize_coding: Huffman table optimization (True)
        # interlace: Progressive JPEG (True)
        # strip: Remove metadata like EXIF/ICC to save space (True)
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
        # Re-raise HTTPExceptions (like file size or empty file)
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
