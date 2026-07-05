import io
import pyvips
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response

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
    Uses synchronous 'def' to allow FastAPI to run it in a thread pool.
    """
    try:
        # Validate file size without reading everything into memory first
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

        # Read the file content
        image_bytes = file.file.read()

        # Load image metadata lazily to check dimensions
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        # Resize if necessary using 'shrink-on-load' optimization via thumbnail_buffer
        if img.width > MAX_WIDTH:
            # thumbnail_buffer is much faster as it only decodes what's needed
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Ensure image is in sRGB and handle transparency (flatten to white)
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        if img.interpretation != 'srgb':
            img = img.colourspace('srgb')

        # Compress to JPEG
        # Q: quality (80)
        # optimize_coding: Huffman table optimization (True)
        # interlace: Progressive JPEG (True)
        # strip: Remove metadata (similar to Pillow's default behavior here)
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
        raise
    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except Exception:
        # Log error if needed, but for now keep parity with original generic error
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )