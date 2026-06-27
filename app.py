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
    Compresses an uploaded image using pyvips for high performance.
    Large images are resized to a maximum width of 1600px.
    Returns a progressive JPEG with optimized Huffman tables.
    """
    try:
        # Efficiently validate file size using seek/tell
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

        try:
            # new_from_buffer is lazy and only reads metadata initially
            img = pyvips.Image.new_from_buffer(image_bytes, "")
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        # Optimization: Use thumbnail_buffer for shrink-on-load when resizing is needed
        if img.width > MAX_WIDTH:
            # pyvips.Image.thumbnail_buffer provides high-quality downsampling
            # by only reading the pixels required for the target size.
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)

        # Handle transparency by flattening onto a white background (matches previous Pillow behavior)
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Generate optimized JPEG
        output_bytes = img.jpegsave_buffer(
            Q=80,                # Quality factor
            optimize_coding=True, # Optimize Huffman tables (Pillow's optimize=True)
            interlace=True,       # Progressive JPEG (Pillow's progressive=True)
            strip=True            # Remove metadata/profiles
        )

        return Response(
            content=output_bytes,
            media_type="image/jpeg"
        )

    except HTTPException:
        # Re-raise HTTPExceptions (e.g. 413, 400) to avoid swallowing them in the generic catch
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
