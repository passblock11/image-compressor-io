import io

import pyvips
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    # File size validation without reading entire file into memory first
    file.file.seek(0, io.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, detail="File too large. Max allowed size is 100 MB"
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        image_bytes = file.file.read()
        # Use pyvips for high-performance image processing
        # new_from_buffer is lazy and only reads metadata initially
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        # Resize if width exceeds MAX_WIDTH
        if img.width > MAX_WIDTH:
            # thumbnail_buffer uses "shrink-on-load" for massive speedup
            # height is set very large to ensure width is the only constraint
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Handle transparency by flattening to white background (parity with Pillow RGB conversion)
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Compress to JPEG with parity settings
        # Q=80, optimize_coding=True (optimize), interlace=True (progressive), strip=True (metadata)
        output_bytes = img.jpegsave_buffer(
            Q=80, optimize_coding=True, interlace=True, strip=True
        )

    except pyvips.Error:
        raise HTTPException(status_code=400, detail="Invalid image file")
    except HTTPException:
        # Re-raise HTTPExceptions (like file size/empty file if they were inside try)
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Upload failed")

    return Response(content=output_bytes, media_type="image/jpeg")
